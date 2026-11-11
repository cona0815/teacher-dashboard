"""小綿助 v5 動畫：四隻角色（lamb、cat、dog、robot）× 16 種動作的動態 WebP 動畫包。

- assets/pet/v5/manifest.json＋<角色>/<動作>.webp（tools/build_pet_pack.py 產生）
- 用到的動作才解碼；最近用過的幾個動作留在記憶體，其餘釋放
- Windows 上用分層視窗（UpdateLayeredWindow）畫每像素透明，邊緣柔和、機器人光暈半透明；
  其他平台或分層視窗失敗時，退回舊的洋紅色鍵透明
"""

from __future__ import annotations

import json
import sys
from collections import OrderedDict
from pathlib import Path

from PIL import Image, ImageChops

# v6＝PET-03 六格精靈圖（2026-11-11 換上，手腳數量全部重畫正確）；沒有 v6 時退回 v5
_PET_DIR = Path(__file__).resolve().parent / "assets" / "pet"
PACK_ROOT = _PET_DIR / "v6" if (_PET_DIR / "v6" / "manifest.json").is_file() else _PET_DIR / "v5"
CHARACTERS = {"lamb": "小綿羊", "cat": "橘貓", "dog": "薩摩耶", "robot": "小機器人"}
DEFAULT_CHARACTER = "lamb"

# 程式裡用的動作名 → v5 動作。v5 沒有走路、探頭、拖曳專用動作（老師不要左右巡邏）。
ALIASES = {
    "idle": "idle",
    "idle_blink": "idle",
    "idle_grade": "note",
    "listen": "listen",
    "think": "think",
    "success": "success",
    "warning": "remind",
    "overdue": "task_due",
    "greet": "notice",
    "sleep": "rest",
    "drag": "notice",
    "mail": "notice",
    "drink": "acknowledge",
    "stretch": "stretch",
    "medicine": "remind",
    "focus": "think",
    "watch": "remind",
    "note": "note",
    "sign": "report",
    # v5 新動作用原名
    "notice": "notice",
    "acknowledge": "acknowledge",
    "remind": "remind",
    "pet": "pet",
    "rise": "rise",
    "rest": "rest",
    "spin": "spin",
    "task_due": "task_due",
    "report": "report",
    "cheer": "cheer",
}


def premultiply(image: Image.Image) -> Image.Image:
    """直通 alpha → 預乘 alpha，通道排成 BGRA（分層視窗要的格式）。"""
    r, g, b, a = image.split()
    r, g, b = (ImageChops.multiply(c, a) for c in (r, g, b))
    return Image.merge("RGBA", (b, g, r, a))


def colorkey(image: Image.Image) -> Image.Image:
    """退回色鍵透明時用：alpha 二值化（Tk 色鍵只認完全透明）。"""
    alpha = image.getchannel("A").point(lambda v: 255 if v >= 110 else 0)
    out = image.copy()
    out.putalpha(alpha)
    return out


class ActionPlayer:
    """一個動作：依格解碼、縮到桌寵大小，解過的格留在 cache。"""

    def __init__(self, path: Path, durations: list[int], size: int, prepare) -> None:
        self.path = path
        self.durations = durations
        self.size = size
        self.prepare = prepare
        self.cache: list[Image.Image | None] = [None] * len(durations)
        self._image: Image.Image | None = None

    def __len__(self) -> int:
        return len(self.durations)

    def delay(self, index: int) -> int:
        return self.durations[index % len(self.durations)]

    def frame(self, index: int) -> Image.Image:
        index %= len(self.durations)
        cached = self.cache[index]
        if cached is not None:
            return cached
        if self._image is None:
            self._image = Image.open(self.path)
        self._image.seek(index)
        self._image.load()
        frame = self._image.convert("RGBA")
        if frame.width != self.size:
            frame = frame.resize((self.size, self.size), Image.Resampling.LANCZOS)
        frame = self.prepare(frame)
        self.cache[index] = frame
        return frame

    def release(self) -> None:
        self.cache = [None] * len(self.durations)
        if self._image is not None:
            self._image.close()
            self._image = None


class PetPack:
    KEEP = 3   # 除了 idle 之外，最多保留幾個動作的已解碼畫面

    def __init__(self, root: Path, character: str, size: int, layered: bool) -> None:
        self.root = root
        self.manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        self.size = size
        # 分層視窗：留直通 alpha，整張視窗畫面疊好角標後才一起預乘；色鍵：先把 alpha 二值化
        self.prepare = (lambda frame: frame) if layered else colorkey
        self.character = character if character in self.manifest["characters"] else DEFAULT_CHARACTER
        self.players: dict[str, ActionPlayer] = {}
        self.recent: OrderedDict[str, None] = OrderedDict()
        self._build()

    @classmethod
    def find(cls, character: str, size: int, layered: bool, root: Path = PACK_ROOT) -> "PetPack | None":
        if not (root / "manifest.json").is_file():
            return None
        try:
            return cls(root, character, size, layered)
        except (OSError, ValueError, KeyError):
            return None

    def _build(self) -> None:
        for player in self.players.values():
            player.release()
        actions = self.manifest["characters"][self.character]
        self.players = {}
        for action, info in actions.items():
            path = self.root / info["file"]
            if path.is_file():
                self.players[action] = ActionPlayer(path, list(info["durations"]), self.size, self.prepare)
        self.recent.clear()

    def set_character(self, character: str) -> bool:
        if character not in self.manifest["characters"] or character == self.character:
            return False
        self.character = character
        self._build()
        return True

    def states(self) -> dict[str, ActionPlayer]:
        """程式動作名 → 播放器（同一個 v5 動作共用一個播放器）。"""
        return {state: self.players[action] for state, action in ALIASES.items() if action in self.players}

    def touch(self, player: ActionPlayer) -> None:
        """記錄最近播放的動作，超過 KEEP 個就把最舊的畫面釋放。"""
        key = str(player.path)
        self.recent.pop(key, None)
        self.recent[key] = None
        idle = self.players.get("idle")
        while len(self.recent) > self.KEEP:
            old = self.recent.popitem(last=False)[0]
            for p in self.players.values():
                if str(p.path) == old and p is not idle and p is not player:
                    p.release()


class LayeredWindow:
    """把 Tk 頂層視窗改成 Windows 分層視窗，每一格用 UpdateLayeredWindow 貼上預乘 BGRA 點陣圖。"""

    def __init__(self, tk_root) -> None:
        import ctypes
        import ctypes.wintypes as wt

        self.ctypes, self.wt = ctypes, wt
        user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
        self.user32, self.gdi32 = user32, gdi32

        class BLENDFUNCTION(ctypes.Structure):
            _fields_ = [("BlendOp", ctypes.c_byte), ("BlendFlags", ctypes.c_byte),
                        ("SourceConstantAlpha", ctypes.c_ubyte), ("AlphaFormat", ctypes.c_byte)]

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG), ("biPlanes", wt.WORD),
                        ("biBitCount", wt.WORD), ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                        ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD),
                        ("biClrImportant", wt.DWORD)]

        self.BLENDFUNCTION, self.BITMAPINFOHEADER = BLENDFUNCTION, BITMAPINFOHEADER
        user32.GetParent.restype = wt.HWND
        user32.GetParent.argtypes = [wt.HWND]
        user32.GetWindowLongW.restype = ctypes.c_long
        user32.GetWindowLongW.argtypes = [wt.HWND, ctypes.c_int]
        user32.SetWindowLongW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_long]
        user32.GetDC.restype = wt.HDC
        user32.GetDC.argtypes = [wt.HWND]
        user32.ReleaseDC.argtypes = [wt.HWND, wt.HDC]
        user32.UpdateLayeredWindow.argtypes = [wt.HWND, wt.HDC, ctypes.POINTER(wt.POINT), ctypes.POINTER(wt.SIZE), wt.HDC,
                                               ctypes.POINTER(wt.POINT), wt.COLORREF, ctypes.POINTER(BLENDFUNCTION), wt.DWORD]
        gdi32.CreateCompatibleDC.restype = wt.HDC
        gdi32.CreateCompatibleDC.argtypes = [wt.HDC]
        gdi32.CreateDIBSection.restype = wt.HBITMAP
        gdi32.CreateDIBSection.argtypes = [wt.HDC, ctypes.c_void_p, wt.UINT, ctypes.POINTER(ctypes.c_void_p), wt.HANDLE, wt.DWORD]
        gdi32.SelectObject.restype = wt.HGDIOBJ
        gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
        gdi32.DeleteObject.argtypes = [wt.HGDIOBJ]
        gdi32.DeleteDC.argtypes = [wt.HDC]

        tk_root.update_idletasks()
        self.hwnd = user32.GetParent(tk_root.winfo_id()) or tk_root.winfo_id()
        style = user32.GetWindowLongW(self.hwnd, -20)
        user32.SetWindowLongW(self.hwnd, -20, style | 0x80000)   # GWL_EXSTYLE |= WS_EX_LAYERED
        self.size = (0, 0)
        self.hdc = self.hbmp = self.old = None
        self.bits = ctypes.c_void_p()

    def _ensure(self, size: tuple[int, int]) -> None:
        if size == self.size and self.hdc:
            return
        self.close()
        w, h = size
        screen = self.user32.GetDC(None)
        self.hdc = self.gdi32.CreateCompatibleDC(screen)
        self.user32.ReleaseDC(None, screen)
        bmi = self.BITMAPINFOHEADER(self.ctypes.sizeof(self.BITMAPINFOHEADER), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
        self.hbmp = self.gdi32.CreateDIBSection(self.hdc, self.ctypes.byref(bmi), 0, self.ctypes.byref(self.bits), None, 0)
        if not self.hbmp:
            raise OSError("CreateDIBSection failed")
        self.old = self.gdi32.SelectObject(self.hdc, self.hbmp)
        self.size = size

    def show(self, bgra: Image.Image) -> bool:
        """bgra：已預乘、通道為 BGRA 的整個視窗大小畫面。"""
        self._ensure(bgra.size)
        data = bgra.tobytes()
        self.ctypes.memmove(self.bits, data, len(data))
        wt = self.wt
        screen = self.user32.GetDC(None)
        blend = self.BLENDFUNCTION(0, 0, 255, 1)   # AC_SRC_OVER、每像素 alpha
        ok = self.user32.UpdateLayeredWindow(self.hwnd, screen, None, self.ctypes.byref(wt.SIZE(*bgra.size)), self.hdc,
                                             self.ctypes.byref(wt.POINT(0, 0)), 0, self.ctypes.byref(blend), 2)
        self.user32.ReleaseDC(None, screen)
        return bool(ok)

    def close(self) -> None:
        if self.hdc:
            if self.old:
                self.gdi32.SelectObject(self.hdc, self.old)
            if self.hbmp:
                self.gdi32.DeleteObject(self.hbmp)
            self.gdi32.DeleteDC(self.hdc)
        self.hdc = self.hbmp = self.old = None
        self.size = (0, 0)

    @classmethod
    def attach(cls, tk_root) -> "LayeredWindow | None":
        if sys.platform != "win32":
            return None
        try:
            return cls(tk_root)
        except (OSError, AttributeError, ValueError):
            return None
