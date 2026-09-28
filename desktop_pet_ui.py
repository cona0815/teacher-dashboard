"""
小綿助 v2.2 資訊顯示層（參考 Clippy.js 的泡泡擺位與 VPet／DyberPet 的狀態顯示做法，程式為本專案原創）。

- NoticeQueue：純邏輯的訊息分級排隊（可單元測試，不依賴 Tk）
    urgent（吃藥、逾期、LINE 新訊息）不會被蓋掉；normal（喝水、起身、分心）；
    feedback（使用者自己操作的回應，立即顯示但不蓋 urgent）；chatter（走路閒聊，有待看訊息就不講）。
- BubbleWindow：獨立浮動泡泡視窗，圓角＋指向小綿羊的尾巴，碰到螢幕邊緣自動換邊；
    停留時間依字數 3–10 秒（重要訊息 8–20 秒），滑鼠移上去暫停關閉；可放「打開／晚點」等按鈕與 ✕。
- BadgeCanvas：小綿羊身上的紅色數字角標。
- HoverCard：滑鼠停在羊上才出現的狀態卡。
- PopupMenu：自己畫的右鍵小選單（不用 tk.Menu——v1.6 曾因 tk.Menu 讓桌寵整隻消失）。
"""
from __future__ import annotations

import time
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass, field
from typing import Callable, Optional

TRANSPARENT = "#ff00ff"
LEVELS = {"chatter": 1, "normal": 2, "feedback": 2, "urgent": 3}
PALETTE = {
    "fill": "#fffdf8", "border": "#a9c3b8", "ink": "#1c302d", "muted": "#657570",
    "urgent": "#b5523f", "normal": "#1f514a", "accent": "#1f514a", "accent_soft": "#e8f2ee",
    "badge": "#d23f31", "hover": "#eef5f1",
}
FONT = "Microsoft JhengHei"


@dataclass
class Notice:
    text: str
    level: str = "chatter"
    key: str = ""
    tag: str = ""
    actions: list = field(default_factory=list)   # [(label, action_id)]
    created: float = field(default_factory=time.time)
    shown_at: float = 0.0

    @property
    def rank(self) -> int:
        return LEVELS.get(self.level, 1)

    def duration_ms(self) -> int:
        base = 3000 + len(self.text) * 90
        if self.level == "urgent":
            return int(min(20000, max(8000, base)))
        if self.level == "chatter":
            return int(min(4500, max(2200, base - 800)))
        return int(min(10000, max(3000, base)))


class NoticeQueue:
    """決定每則訊息是「立刻顯示」「排隊」「丟棄」，並保留通知紀錄。"""

    def __init__(self, log: Optional[list] = None, log_limit: int = 50):
        self.current: Optional[Notice] = None
        self.pending: list[Notice] = []
        self.log: list = log if isinstance(log, list) else []
        self.log_limit = log_limit
        self.dnd_until = 0.0

    # ---- 勿擾
    def in_dnd(self, now: Optional[float] = None) -> bool:
        return (now or time.time()) < self.dnd_until

    # ---- 推入
    def push(self, notice: Notice) -> str:
        if notice.level != "chatter" and notice.level != "feedback":
            self._record(notice)
        if self.in_dnd() and notice.level != "urgent" and notice.level != "feedback":
            return "dropped"
        if notice.level == "chatter":
            if self.current is not None or self.pending:
                return "dropped"
            self.current = notice
            return "show"
        if notice.key:
            if self.current is not None and self.current.key == notice.key:
                self.current.text, self.current.actions, self.current.tag = notice.text, notice.actions, notice.tag
                return "update"
            self.pending = [item for item in self.pending if item.key != notice.key]
        if self.current is None:
            self.current = notice
            return "show"
        cur = self.current
        if cur.level == "urgent":
            # 重要訊息不會被任何東西蓋掉，包含另一則重要訊息
            self._enqueue(notice)
            return "queued"
        if notice.rank >= cur.rank:
            if cur.level in ("normal", "urgent"):
                self.pending.insert(0, cur)
            self.current = notice
            return "show"
        self._enqueue(notice)
        return "queued"

    def _enqueue(self, notice: Notice) -> None:
        self.pending.append(notice)
        self.pending.sort(key=lambda item: (-item.rank, item.created))
        del self.pending[20:]

    def close_current(self, read: bool = True) -> Optional[Notice]:
        """目前的關掉，回傳下一則（沒有就 None）。read=False：時間到自動消失，重要訊息保留未讀。"""
        if self.current is not None and (read or self.current.level != "urgent"):
            self.mark_read(self.current)
        self.current = None
        while self.pending:
            nxt = self.pending.pop(0)
            if self.in_dnd() and nxt.level not in ("urgent", "feedback"):
                continue
            self.current = nxt
            return nxt
        return None

    def mark_all_read(self) -> None:
        for entry in self.log:
            entry["read"] = True

    # ---- 紀錄
    def _record(self, notice: Notice) -> None:
        if notice.key:
            self.log[:] = [entry for entry in self.log if entry.get("read") or entry.get("key") != notice.key]
        self.log.insert(0, {"time": time.strftime("%H:%M"), "date": time.strftime("%Y-%m-%d"), "text": notice.text[:200],
                            "level": notice.level, "tag": notice.tag, "read": False, "key": notice.key})
        del self.log[self.log_limit:]

    def mark_read(self, notice: Notice) -> None:
        for entry in self.log:
            if entry.get("text") == notice.text[:200] and not entry.get("read"):
                entry["read"] = True
                break

    def unread_count(self) -> int:
        """沒看到的重要通知（不含正在泡泡裡顯示的那則）。"""
        showing = self.current.text[:200] if self.current is not None else None
        return sum(1 for entry in self.log if not entry.get("read") and entry.get("level") == "urgent" and entry.get("text") != showing)


# ---------------------------------------------------------------------- Tk 視窗工具
def _toplevel(root: tk.Misc) -> tk.Toplevel:
    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=TRANSPARENT)
    try:
        win.wm_attributes("-transparentcolor", TRANSPARENT)
    except tk.TclError:
        pass
    return win


def round_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, **kw):
    points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2,
              x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(points, smooth=True, **kw)


class BubbleWindow:
    """獨立的對話泡泡：圓角＋尾巴指向小綿羊，碰到螢幕邊緣換邊。"""

    def __init__(self, root: tk.Misc, scale: float, pet_box: Callable[[], tuple], on_action: Callable[[Notice, str], None], on_closed: Callable[[Notice, str], None]):
        self.root, self.s = root, scale
        self.pet_box, self.on_action, self.on_closed = pet_box, on_action, on_closed
        self.win: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None
        self.notice: Optional[Notice] = None
        self.side = ""
        self.size = (0, 0)
        self.hide_job: Optional[str] = None
        self.follow_job: Optional[str] = None
        self.hovering = False
        self.body_font = tkfont.Font(family=FONT, size=10)
        self.tag_font = tkfont.Font(family=FONT, size=9, weight="bold")
        self.btn_font = tkfont.Font(family=FONT, size=9, weight="bold")

    # ---- 尺寸
    def _measure(self, notice: Notice) -> dict:
        s = self.s
        pad, wrap = 12 * s, 230 * s
        lines_w, text_h = self._wrap_size(notice.text, wrap)
        tag_h = (self.tag_font.metrics("linespace") + 4 * s) if notice.tag else 0
        btns = [(label, aid, self.btn_font.measure(label) + 18 * s) for label, aid in notice.actions]
        btn_row_w = sum(w for _, _, w in btns) + max(0, len(btns) - 1) * 6 * s
        btn_h = 24 * s if btns else 0
        close_w = 16 * s
        content_w = max(lines_w, btn_row_w, (self.tag_font.measure(notice.tag) if notice.tag else 0))
        bw = max(120 * s, content_w + pad * 2 + close_w)
        bh = pad + tag_h + text_h + (8 * s + btn_h if btns else 0) + pad
        return {"pad": pad, "wrap": wrap, "tag_h": tag_h, "text_h": text_h, "btns": btns, "btn_h": btn_h, "bw": bw, "bh": bh}

    def _wrap_lines(self, text: str, wrap: float) -> list:
        """中文逐字斷行（Tk 的 width= 只在空白處斷，中英混排會算錯高度）；標點不放行首。"""
        lines = []
        for paragraph in str(text).split("\n"):
            current = ""
            for ch in paragraph:
                if self.body_font.measure(current + ch) > wrap and current:
                    if ch in "，。、；：！？）」』》,.;:!?)":
                        current += ch
                        continue
                    lines.append(current)
                    current = ch
                else:
                    current += ch
            lines.append(current)
        return lines

    def _wrap_size(self, text: str, wrap: float) -> tuple:
        lines = self._wrap_lines(text, wrap)
        widest = max((self.body_font.measure(line) for line in lines), default=0)
        return widest, len(lines) * self.body_font.metrics("linespace")

    # ---- 擺位（Clippy 式：依序試四個方向，找不超出螢幕的）
    def _place(self, bw: float, bh: float, prefer: str = "") -> tuple:
        s = self.s
        x0, y0, x1, y1 = self.pet_box()
        hx = (x0 + x1) / 2
        head_y = y0 + (y1 - y0) * 0.16
        foot_y = y1 - (y1 - y0) * 0.1
        tail = 16 * s
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        m = 6
        order = ["above-left", "above-right", "below-left", "below-right"] if hx > sw / 2 else ["above-right", "above-left", "below-right", "below-left"]
        if prefer in order:
            order.remove(prefer)
            order.insert(0, prefer)
        best = None
        for side in order:
            bx = hx + 40 * s - bw if side.endswith("left") else hx - 40 * s
            by = head_y - tail - bh if side.startswith("above") else foot_y + tail
            fits = m <= bx and bx + bw <= sw - m and m <= by and by + bh <= sh - m
            cand = (side, bx, by, hx, head_y if side.startswith("above") else foot_y)
            if fits:
                return cand
            best = best or cand
        side, bx, by, tx, ty = best
        bx = min(max(m, bx), sw - m - bw)
        by = min(max(m, by), sh - m - bh)
        return side, bx, by, tx, ty

    # ---- 顯示
    def show(self, notice: Notice) -> None:
        self.notice = notice
        notice.shown_at = time.time()
        self._draw(prefer="")
        self._schedule_hide(notice.duration_ms())
        self._follow()

    def update_text(self, notice: Notice) -> None:
        self.notice = notice
        self._draw(prefer=self.side)

    def _draw(self, prefer: str) -> None:
        notice = self.notice
        if notice is None:
            return
        s = self.s
        m = self._measure(notice)
        bw, bh = m["bw"], m["bh"]
        side, bx, by, tx, ty = self._place(bw, bh, prefer)
        tail = 16 * s
        above = side.startswith("above")
        wx, wy = int(bx), int(by if above else by - tail)
        ww, wh = int(bw + 2), int(bh + tail + 2)
        if self.win is None or not self._alive():
            self.win = _toplevel(self.root)
            self.canvas = tk.Canvas(self.win, bg=TRANSPARENT, highlightthickness=0, bd=0)
            self.canvas.pack(fill="both", expand=True)
            self.canvas.bind("<Enter>", self._on_enter)
            self.canvas.bind("<Leave>", self._on_leave)
        c = self.canvas
        c.delete("all")
        self.win.geometry(f"{ww}x{wh}+{wx}+{wy}")
        c.configure(width=ww, height=wh)
        top = 1 if above else tail + 1
        color = PALETTE["urgent"] if notice.level == "urgent" else PALETTE["border"]
        width = 2 if notice.level == "urgent" else 1.5
        round_rect(c, 1, top, bw, top + bh - 1, 14 * s, fill=PALETTE["fill"], outline=color, width=width)
        # 尾巴：尖端指向小綿羊，底邊貼著泡泡
        tip_x = min(max(tx - wx, 22 * s), bw - 22 * s)
        base_c = min(max(tip_x + (10 * s if side.endswith("left") else -10 * s), 24 * s), bw - 24 * s)
        if above:
            edge = top + bh - 1
            tip = (tx - wx, edge + tail - 1)
            pts = [base_c - 9 * s, edge - 1, base_c + 9 * s, edge - 1, *tip]
        else:
            edge = top
            tip = (tx - wx, 1)
            pts = [base_c - 9 * s, edge + 1, base_c + 9 * s, edge + 1, *tip]
        c.create_polygon(pts, fill=PALETTE["fill"], outline=color, width=width)
        c.create_line(base_c - 8 * s, pts[1], base_c + 8 * s, pts[3], fill=PALETTE["fill"], width=width + 2)
        # 內容
        y = top + m["pad"]
        if notice.tag:
            c.create_text(m["pad"], y, text=notice.tag, anchor="nw", font=self.tag_font,
                          fill=PALETTE["urgent"] if notice.level == "urgent" else PALETTE["normal"])
            y += m["tag_h"]
        c.create_text(m["pad"], y, text="\n".join(self._wrap_lines(notice.text, m["wrap"])), anchor="nw", font=self.body_font, fill=PALETTE["ink"])
        y += m["text_h"] + 8 * s
        x = m["pad"]
        for i, (label, aid, w) in enumerate(m["btns"]):
            primary = i == 0
            tag = f"act_{i}"
            round_rect(c, x, y, x + w, y + m["btn_h"], 8 * s, fill=PALETTE["accent"] if primary else PALETTE["fill"],
                       outline=PALETTE["accent"], width=1, tags=(tag,))
            c.create_text(x + w / 2, y + m["btn_h"] / 2, text=label, font=self.btn_font,
                          fill="#ffffff" if primary else PALETTE["accent"], tags=(tag,))
            c.tag_bind(tag, "<Button-1>", lambda _e, a=aid: self._act(a))
            x += w + 6 * s
        cx, cy = bw - 14 * s, top + 13 * s
        c.create_text(cx, cy, text="✕", font=self.tag_font, fill=PALETTE["muted"], tags=("close",))
        c.tag_bind("close", "<Button-1>", lambda _e: self.close("dismiss"))
        self.side, self.size = side, (bw, bh)
        try:
            self.win.deiconify()
            self.win.lift()
        except tk.TclError:
            pass

    def _alive(self) -> bool:
        try:
            return bool(self.win and self.win.winfo_exists())
        except tk.TclError:
            return False

    # ---- 計時與跟隨
    def _schedule_hide(self, ms: int) -> None:
        if self.hide_job:
            try:
                self.root.after_cancel(self.hide_job)
            except tk.TclError:
                pass
        self.hide_job = self.root.after(ms, lambda: self.close("timeout"))

    def _on_enter(self, _e=None) -> None:
        self.hovering = True
        if self.hide_job:
            try:
                self.root.after_cancel(self.hide_job)
            except tk.TclError:
                pass
            self.hide_job = None

    def _on_leave(self, _e=None) -> None:
        self.hovering = False
        if self.notice is not None:
            self._schedule_hide(2500)

    def _follow(self) -> None:
        if self.notice is None or not self._alive():
            self.follow_job = None
            return
        bw, bh = self.size
        side, bx, by, tx, ty = self._place(bw, bh, self.side)
        if side != self.side:
            self._draw(prefer=side)
        else:
            s = self.s
            above = side.startswith("above")
            try:
                self.win.geometry(f"+{int(bx)}+{int(by if above else by - 16 * s)}")
            except tk.TclError:
                pass
        self.follow_job = self.root.after(90, self._follow)

    def _act(self, action_id: str) -> None:
        notice = self.notice
        self.close("action")
        if notice is not None:
            self.on_action(notice, action_id)

    def close(self, reason: str = "dismiss") -> None:
        notice = self.notice
        self.notice = None
        for job in (self.hide_job, self.follow_job):
            if job:
                try:
                    self.root.after_cancel(job)
                except tk.TclError:
                    pass
        self.hide_job = self.follow_job = None
        if self._alive():
            try:
                self.win.withdraw()
            except tk.TclError:
                pass
        if notice is not None:
            self.on_closed(notice, reason)

    def hide_quietly(self) -> None:
        """收起泡泡但不算看過（投影／全螢幕時暫時藏起來，之後會再顯示）。"""
        on_closed = self.on_closed
        self.on_closed = lambda _notice, _reason: None
        try:
            self.close("hidden")
        finally:
            self.on_closed = on_closed

    @property
    def visible(self) -> bool:
        return self.notice is not None


class BadgeCanvas:
    """小綿羊頭上的紅色數字角標（逾期＋LINE 未整理）。"""

    def __init__(self, parent: tk.Misc, scale: float, on_click: Callable[[], None]):
        self.s = scale
        self.canvas = tk.Canvas(parent, width=int(30 * scale), height=int(22 * scale), bg=TRANSPARENT, highlightthickness=0, bd=0)
        self.canvas.bind("<Button-1>", lambda _e: on_click())
        self.font = tkfont.Font(family=FONT, size=9, weight="bold")
        self.count = -1

    def set(self, count: int, x: int, y: int) -> None:
        if count == self.count:
            if count > 0:
                self.canvas.place(x=x, y=y)
            return
        self.count = count
        c = self.canvas
        c.delete("all")
        if count <= 0:
            c.place_forget()
            return
        text = str(count) if count < 100 else "99+"
        s = self.s
        w = max(22 * s, self.font.measure(text) + 12 * s)
        c.configure(width=int(w + 2), height=int(22 * s))
        round_rect(c, 1, 1, w, 21 * s, 10 * s, fill=PALETTE["badge"], outline="#ffffff", width=2)
        c.create_text(w / 2 + 1, 11 * s, text=text, font=self.font, fill="#ffffff")
        c.place(x=x, y=y)
        c.tk.call("raise", c._w)   # Canvas.lift 是 tag_raise，這裡要的是把整個角標疊到小綿羊上面


class HoverCard:
    """滑鼠停在小綿羊上 0.6 秒才出現的狀態卡。"""

    def __init__(self, root: tk.Misc, scale: float, pet_box: Callable[[], tuple]):
        self.root, self.s, self.pet_box = root, scale, pet_box
        self.win: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None
        self.font = tkfont.Font(family=FONT, size=10)
        self.title_font = tkfont.Font(family=FONT, size=10, weight="bold")
        self.hint_font = tkfont.Font(family=FONT, size=8)
        self.visible = False

    def show(self, title: str, rows: list, hint: str) -> None:
        s = self.s
        pad, line_h = 12 * s, self.font.metrics("linespace") + 5 * s
        texts = [title] + [r for r in rows] + [hint]
        width = max([self.title_font.measure(title)] + [self.font.measure(r) for r in rows] + [self.hint_font.measure(hint)]) + pad * 2
        height = pad * 2 + line_h * (len(rows) + 1) + self.hint_font.metrics("linespace") + 4 * s
        x0, y0, x1, y1 = self.pet_box()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        gx = x1 + 4 * s if x1 + 4 * s + width < sw - 6 else x0 - 4 * s - width
        gy = min(max(6, (y0 + y1) / 2 - height / 2), sh - 6 - height)
        if self.win is None:
            self.win = _toplevel(self.root)
            self.canvas = tk.Canvas(self.win, bg=TRANSPARENT, highlightthickness=0, bd=0)
            self.canvas.pack(fill="both", expand=True)
        c = self.canvas
        c.delete("all")
        self.win.geometry(f"{int(width + 2)}x{int(height + 2)}+{int(gx)}+{int(gy)}")
        c.configure(width=int(width + 2), height=int(height + 2))
        round_rect(c, 1, 1, width, height, 12 * s, fill=PALETTE["fill"], outline=PALETTE["border"], width=1.5)
        y = pad
        c.create_text(pad, y, text=title, anchor="nw", font=self.title_font, fill=PALETTE["accent"])
        y += line_h
        for row in rows:
            c.create_text(pad, y, text=row, anchor="nw", font=self.font, fill=PALETTE["ink"])
            y += line_h
        c.create_text(pad, y + 2 * s, text=hint, anchor="nw", font=self.hint_font, fill=PALETTE["muted"])
        del texts
        self.win.deiconify()
        self.win.lift()
        self.visible = True

    def hide(self) -> None:
        self.visible = False
        if self.win is not None:
            try:
                self.win.withdraw()
            except tk.TclError:
                pass


class PopupMenu:
    """自己畫的右鍵小選單。items: [(label, callback) 或 None 當分隔線]。"""

    def __init__(self, root: tk.Misc, scale: float):
        self.root, self.s = root, scale
        self.win: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None
        self.font = tkfont.Font(family=FONT, size=10)
        self.close_job: Optional[str] = None
        self.entered = False

    def open(self, x_root: int, y_root: int, items: list, avoid: Optional[tuple] = None) -> None:
        """avoid＝小綿羊的螢幕範圍：選單改開在羊的旁邊，不蓋住牠（牠每 4 秒會浮上最上層）。"""
        self.close()
        s = self.s
        pad, row_h = 6 * s, 30 * s
        width = max(self.font.measure(item[0]) for item in items if item) + 40 * s
        height = pad * 2 + sum(row_h if item else 9 * s for item in items)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        if avoid:
            ax0, ay0, ax1, ay1 = avoid
            x = ax0 - width - 8 * s if ax0 - width - 8 * s >= 6 else ax1 + 8 * s
            y = min(max(6, y_root - 24 * s), sh - height - 6)
        else:
            x = min(x_root, sw - width - 6)
            y = y_root - height - 8 if y_root + height > sh - 6 else y_root
        self.win = _toplevel(self.root)
        c = self.canvas = tk.Canvas(self.win, bg=TRANSPARENT, highlightthickness=0, bd=0, width=int(width + 2), height=int(height + 2))
        c.pack()
        self.win.geometry(f"{int(width + 2)}x{int(height + 2)}+{int(x)}+{int(max(6, y))}")
        round_rect(c, 1, 1, width, height, 12 * s, fill=PALETTE["fill"], outline=PALETTE["border"], width=1.5)
        yy = pad
        for i, item in enumerate(items):
            if item is None:
                c.create_line(12 * s, yy + 4 * s, width - 12 * s, yy + 4 * s, fill="#dde6e2")
                yy += 9 * s
                continue
            label, callback = item
            tag = f"row_{i}"
            c.create_rectangle(6 * s, yy, width - 6 * s, yy + row_h, fill=PALETTE["fill"], outline="", tags=(tag, f"{tag}_bg"))
            c.create_text(18 * s, yy + row_h / 2, text=label, anchor="w", font=self.font, fill=PALETTE["ink"], tags=(tag,))
            c.tag_bind(tag, "<Enter>", lambda _e, t=tag: c.itemconfigure(f"{t}_bg", fill=PALETTE["hover"]))
            c.tag_bind(tag, "<Leave>", lambda _e, t=tag: c.itemconfigure(f"{t}_bg", fill=PALETTE["fill"]))
            c.tag_bind(tag, "<Button-1>", lambda _e, cb=callback: self._choose(cb))
            yy += row_h
        c.bind("<Enter>", self._enter)
        c.bind("<Leave>", self._leave)
        self.win.bind("<Escape>", lambda _e: self.close())
        self.win.bind("<FocusOut>", lambda _e: self.close())
        self.entered = False
        try:
            self.win.focus_force()
        except tk.TclError:
            pass
        self.close_job = self.root.after(6000, self.close)

    def _enter(self, _e=None) -> None:
        self.entered = True
        if self.close_job:
            self.root.after_cancel(self.close_job)
            self.close_job = None

    def _leave(self, _e=None) -> None:
        if self.close_job:
            self.root.after_cancel(self.close_job)
        self.close_job = self.root.after(900, self.close)

    def _choose(self, callback: Callable[[], None]) -> None:
        self.close()
        try:
            callback()
        except Exception:  # noqa: BLE001 - 選單動作失敗不能讓桌寵閃退
            pass

    def close(self) -> None:
        if self.close_job:
            try:
                self.root.after_cancel(self.close_job)
            except tk.TclError:
                pass
            self.close_job = None
        if self.win is not None:
            try:
                self.win.destroy()
            except tk.TclError:
                pass
        self.win = None

    @property
    def is_open(self) -> bool:
        return self.win is not None
