"""Windows desktop preview for the original 小綿助 animation set."""

from __future__ import annotations

import random
import sys
import tkinter as tk
import traceback
from pathlib import Path
from typing import Callable

from PIL import Image, ImageTk

if sys.platform == "win32":
    # 宣告 DPI 感知：高解析縮放螢幕上，非感知程式會被 Windows 點陣拉伸，
    # 部分機器（尤其超寬螢幕＋150% 縮放）拉伸重繪會損壞（面板空白、文字重影）。
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:  # noqa: BLE001 - 舊系統沒有此 API 時維持原行為
        pass


TRANSPARENT = "#ff00ff"
WINDOW_WIDTH = 330
WINDOW_HEIGHT = 236
PET_SIZE = 164
PET_TOP = 68
BUBBLE_WRAP = 286
ERROR_LOG = Path.home() / "XiaoMianZhuSecretary" / "desktop_pet.log"


class DesktopPetPreview:
    FRAME_DELAYS = {
        "drag": 125,
        "idle": 200,
        "listen": 155,
        "sleep": 290,
        "success": 110,
        "think": 145,
        # Use the complete 16-frame gait cycle.  Keeping the cadence in sync
        # with the web animation prevents the lamb from appearing to limp.
        "walk_left": 75,
        "walk_right": 75,
        "warning": 140,
    }

    FRAME_COUNTS = {
        "drag": 6,
        "idle": 6,
        "listen": 6,
        "sleep": 6,
        "success": 8,
        "think": 8,
        "walk_left": 16,
        "walk_right": 16,
        "warning": 8,
    }

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("小綿助桌面預覽")
        # pythonw.exe 沒有主控台；記錄 Tk callback 例外，避免操作時看起來像閃退。
        self.root.report_callback_exception = self._report_callback_exception
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=TRANSPARENT)
        if sys.platform == "win32":
            self.root.wm_attributes("-transparentcolor", TRANSPARENT)

        self.dpi_scale = max(1.0, self.root.winfo_fpixels("1i") / 96.0)
        self.win_w = int(WINDOW_WIDTH * self.dpi_scale)
        self.win_h = int(WINDOW_HEIGHT * self.dpi_scale)
        self.pet_px = int(PET_SIZE * self.dpi_scale)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        # Start in a clearly visible position for local testing. The real
        # secretary remembers its saved location; this preview should never
        # appear to be missing because it started behind a taskbar or off the
        # right edge of a multi-monitor desktop.
        self.x = max(12, (self.screen_width - self.win_w) // 2)
        self.y = max(12, (self.screen_height - self.win_h) // 2)
        self.root.geometry(f"{self.win_w}x{self.win_h}+{self.x}+{self.y}")

        self.assets_root = Path(__file__).resolve().parent / "assets" / "pet" / "frames"
        self.frames = self._load_frames()
        self.state = "idle"
        self.frame_index = 0
        self.completed_loops = 0
        self.loop_limit: int | None = None
        self.after_state = "idle"
        self.paused = False
        self.wandering = True
        self.walking = False
        self.walk_direction = -1
        self.walk_stop_at = 0
        self.drag_origin: tuple[int, int, int, int] | None = None
        self.drag_moved = False
        self.bubble_timer: str | None = None

        self.bubble = tk.Label(
            self.root,
            text="我會在桌面陪你工作！",
            bg="#fffdf8",
            fg="#2e5a4a",
            font=("Microsoft JhengHei", 9, "bold"),
            padx=9,
            pady=5,
            relief="solid",
            borderwidth=1,
            justify="center",
            anchor="center",
            wraplength=int(BUBBLE_WRAP * self.dpi_scale),
        )
        self.bubble.place(relx=0.5, y=4, anchor="n")

        self.pet_label = tk.Label(self.root, bg=TRANSPARENT, borderwidth=0, highlightthickness=0)
        self.pet_label.place(x=(self.win_w - self.pet_px) // 2, y=int(PET_TOP * self.dpi_scale), width=self.pet_px, height=self.pet_px)

        for widget in (self.root, self.pet_label):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._drag)
            widget.bind("<ButtonRelease-1>", self._finish_drag)
            widget.bind("<Double-Button-1>", lambda _event: self.play("success", 2, "idle", "任務完成！"))
            widget.bind("<Button-3>", self._show_menu)

        self.menu = tk.Menu(self.root, tearoff=False, font=("Microsoft JhengHei", 10))
        self.menu.add_command(label="開始走動", command=self.start_walking)
        self.menu.add_command(label="待機", command=lambda: self.play("idle", None, "idle", "我在這裡陪你。"))
        self.menu.add_command(label="聆聽", command=lambda: self.play("listen", 3, "idle", "我正在聽……"))
        self.menu.add_command(label="思考", command=lambda: self.play("think", 3, "idle", "我正在整理工作。"))
        self.menu.add_command(label="成功", command=lambda: self.play("success", 2, "idle", "任務完成！"))
        self.menu.add_command(label="警告", command=lambda: self.play("warning", 3, "idle", "這件工作快到期囉！"))
        self.menu.add_command(label="睡覺", command=lambda: self.play("sleep", 5, "idle", "先休息一下……"))
        self.menu.add_separator()
        self.menu.add_command(label="暫停／繼續", command=self.toggle_pause)
        self.menu.add_command(label="關閉小綿助", command=self.root.destroy)

        self.root.bind("<Escape>", lambda _event: self.root.destroy())
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self._render_frame()
        self.root.after(850, self._hide_bubble)
        self.root.after(self.FRAME_DELAYS[self.state], self._animation_tick)
        self.root.after(30, self._movement_tick)
        self.root.after(2600, self.start_walking)

    def _report_callback_exception(self, exc_type, exc_value, exc_traceback) -> None:
        """記錄 Tk 事件錯誤，讓桌寵繼續常駐。"""
        try:
            ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
            detail = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            with ERROR_LOG.open("a", encoding="utf-8") as stream:
                stream.write(f"\n[{__import__('datetime').datetime.now().isoformat(timespec='seconds')}]\n{detail}")
        except OSError:
            pass
        try:
            self.show_bubble("剛才的操作沒有完成，桌寵仍在運作。", 2800)
        except tk.TclError:
            pass

    def _load_frames(self) -> dict[str, list[ImageTk.PhotoImage]]:
        result: dict[str, list[ImageTk.PhotoImage]] = {}
        for state, count in self.FRAME_COUNTS.items():
            folder = self.assets_root / f"pet_{state}"
            paths = sorted(folder.glob("*.png"))
            if len(paths) != count:
                raise FileNotFoundError(f"{folder} 應有 {count} 張動畫，目前找到 {len(paths)} 張。")
            result[state] = []
            for path in paths:
                image = Image.open(path).convert("RGBA").resize((self.pet_px, self.pet_px), Image.Resampling.LANCZOS)
                # Tk's Windows color-key transparency only removes exact magenta.
                # Remove the very soft alpha fringe before Tk blends it with the
                # magenta window background, otherwise a pink outline remains.
                cleaned_pixels = []
                for red, green, blue, alpha in image.getdata():
                    # 生成動畫曾使用洋紅底；連同抗鋸齒產生的粉紫殘邊一起移除。
                    is_magenta_fringe = red >= 190 and blue >= 190 and green <= 165 and abs(red - blue) <= 85
                    cleaned_pixels.append((red, green, blue, 0 if is_magenta_fringe or alpha < 32 else 255))
                image.putdata(cleaned_pixels)
                result[state].append(ImageTk.PhotoImage(image))
            # Walk assets are authored as a complete, ordered gait cycle.
            # Keep that order instead of mirroring it at runtime: the
            # generated frames already alternate weight-bearing legs and
            # include the return-to-contact pose. Mirroring here made the
            # rear hoof appear to snap backwards and read as an injury.
        return result

    def run(self) -> None:
        self.root.mainloop()

    def play(
        self,
        state: str,
        loops: int | None = None,
        after_state: str = "idle",
        message: str | None = None,
    ) -> None:
        self.walking = state.startswith("walk_")
        self.state = state
        self.frame_index = 0
        self.completed_loops = 0
        self.loop_limit = loops
        self.after_state = after_state
        if message:
            self.show_bubble(message, 2400)
        self._render_frame()

    def show_bubble(self, message: str, duration: int = 2200) -> None:
        self.bubble.configure(text=message)
        self.bubble.place(relx=0.5, y=4, anchor="n")
        if self.bubble_timer:
            self.root.after_cancel(self.bubble_timer)
        self.bubble_timer = self.root.after(duration, self._hide_bubble)

    def _hide_bubble(self) -> None:
        self.bubble.place_forget()
        self.bubble_timer = None

    def _render_frame(self) -> None:
        frame_set = self.frames[self.state]
        self.pet_label.configure(image=frame_set[self.frame_index])
        self.pet_label.image = frame_set[self.frame_index]

    def _animation_tick(self) -> None:
        if not self.paused:
            frame_count = len(self.frames[self.state])
            self.frame_index += 1
            if self.frame_index >= frame_count:
                self.frame_index = 0
                self.completed_loops += 1
                if self.loop_limit is not None and self.completed_loops >= self.loop_limit:
                    next_state = self.after_state
                    self.play(next_state)
            self._render_frame()
        self.root.after(self.FRAME_DELAYS[self.state], self._animation_tick)

    def start_walking(self) -> None:
        if self.paused or self.drag_origin:
            return
        self.walk_direction = -1 if self.x > self.screen_width / 2 else 1
        self.walk_stop_at = self.root.tk.call("clock", "milliseconds") + random.randint(5000, 9000)
        self.play("walk_left" if self.walk_direction < 0 else "walk_right")
        self.show_bubble("我去巡一下工作進度！", 1800)

    def _movement_tick(self) -> None:
        if not self.paused and self.walking and not self.drag_origin:
            # Keep screen travel in proportion to the relaxed animation.
            # One pixel per 30 ms avoids the previous skating/limping effect.
            self.x += self.walk_direction
            max_x = max(0, self.screen_width - self.win_w)
            if self.x <= 0 or self.x >= max_x:
                self.x = min(max(self.x, 0), max_x)
                self.walk_direction *= -1
                self.play("walk_left" if self.walk_direction < 0 else "walk_right")
            self.root.geometry(f"+{self.x}+{self.y}")
            now = int(self.root.tk.call("clock", "milliseconds"))
            if now >= self.walk_stop_at:
                self.walking = False
                if random.random() < 0.22:
                    self.play("sleep", random.randint(4, 7), "idle", "休息一下再繼續。")
                else:
                    self.play("idle")
                self.root.after(random.randint(3500, 7000), self.start_walking)
        self.root.after(30, self._movement_tick)

    def _start_drag(self, event: tk.Event) -> None:
        self.drag_origin = (event.x_root, event.y_root, self.x, self.y)
        self.drag_moved = False
        self.walking = False
        self.play("drag")

    def _drag(self, event: tk.Event) -> None:
        if not self.drag_origin:
            return
        start_x, start_y, window_x, window_y = self.drag_origin
        dx, dy = event.x_root - start_x, event.y_root - start_y
        if abs(dx) + abs(dy) > 5:
            self.drag_moved = True
        self.x = min(max(0, window_x + dx), max(0, self.screen_width - self.win_w))
        self.y = min(max(0, window_y + dy), max(0, self.screen_height - self.win_h))
        self.root.geometry(f"+{self.x}+{self.y}")

    def _finish_drag(self, _event: tk.Event) -> None:
        moved = self.drag_moved
        self.drag_origin = None
        self.play("idle")
        if not moved:
            self.show_bubble("我是小綿助，右鍵可以試動作！", 2600)
        self.root.after(4200, self.start_walking)

    def _show_menu(self, event: tk.Event) -> None:
        self.walking = False
        self.play("idle")
        self.menu.tk_popup(event.x_root, event.y_root)

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.walking = False
        self.play("idle")
        self.show_bubble("已暫停。" if self.paused else "繼續陪你工作！", 1800)
        if not self.paused:
            self.root.after(1800, self.start_walking)


if __name__ == "__main__":
    DesktopPetPreview().run()
