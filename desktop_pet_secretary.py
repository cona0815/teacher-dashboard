"""小綿助 Windows 桌面秘書。

平時只有透明桌寵常駐；點一下角色才展開秘書首頁。所有本機健康紀錄、
快速記事與尚未同步的任務均保存在使用者 AppData，不寫入網頁 localStorage。
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageGrab

from desktop_pet_preview import DesktopPetPreview


APP_NAME = "小綿助教師秘書"
DATA_ROOT = Path(os.getenv("APPDATA", Path.home())) / "XiaoMianZhuSecretary"
DATA_FILE = DATA_ROOT / "secretary_data.json"
ATTACHMENT_ROOT = DATA_ROOT / "attachments"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def default_data() -> dict:
    now = now_iso()
    return {
        "tasks": [],
        "notes": [],
        "health": {
            "date": date.today().isoformat(),
            "water_count": 0,
            "last_water": now,
            "last_move": now,
            "move_done_date": "",
            "medicine_time": "",
            "medicine_done_date": "",
        },
    }


class SecretaryPet(DesktopPetPreview):
    COLORS = {
        "bg": "#fffdf8",
        "soft": "#edf4ef",
        "primary": "#355e59",
        "strong": "#284a46",
        "ink": "#2f3b37",
        "muted": "#6d7973",
        "line": "#d8e2da",
        "danger": "#a94f43",
        "danger_soft": "#f9e6e1",
        "gold_soft": "#f6eed8",
    }

    def __init__(self) -> None:
        super().__init__()
        self.root.title(APP_NAME)
        self.data = self._load_data()
        self.attachments: list[Path] = []
        self.draft: dict | None = None
        self.panel: tk.Toplevel | None = None
        self.panel_widgets: dict[str, object] = {}
        self.health_alerted = {"water": False, "move": False, "medicine": False}

        self.menu.insert_command(0, label="開啟秘書首頁", command=self.toggle_secretary)
        self.menu.insert_command(1, label="整理今日簡報", command=lambda: self.open_secretary("today"))
        self.menu.insert_separator(2)
        self.root.after(1000, self._health_tick)
        self.root.after(1200, self._opening_brief)

    def _load_data(self) -> dict:
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        ATTACHMENT_ROOT.mkdir(parents=True, exist_ok=True)
        try:
            loaded = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("invalid data")
        except (OSError, ValueError, json.JSONDecodeError):
            loaded = default_data()
        base = default_data()
        base.update(loaded)
        if not isinstance(base.get("tasks"), list):
            base["tasks"] = []
        if not isinstance(base.get("notes"), list):
            base["notes"] = []
        health = default_data()["health"]
        health.update(base.get("health") or {})
        if health["date"] != date.today().isoformat():
            health["date"] = date.today().isoformat()
            health["water_count"] = 0
        base["health"] = health
        return base

    def _save_data(self) -> None:
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _finish_drag(self, _event: tk.Event) -> None:
        moved = self.drag_moved
        self.drag_origin = None
        self.play("idle")
        if not moved:
            self.toggle_secretary()
        self.root.after(4200, self.start_walking)

    def toggle_secretary(self) -> None:
        if self.panel and self.panel.winfo_exists() and self.panel.state() != "withdrawn":
            self.panel.withdraw()
            return
        self.open_secretary()

    def open_secretary(self, brief_mode: str | None = None) -> None:
        if not self.panel or not self.panel.winfo_exists():
            self._build_panel()
        if brief_mode:
            self._render_brief(brief_mode)
        self._render_dashboard()
        self.panel.deiconify()
        self.panel.lift()
        self.panel.focus_force()

    def _build_panel(self) -> None:
        c = self.COLORS
        panel = tk.Toplevel(self.root)
        self.panel = panel
        panel.title(APP_NAME)
        panel.configure(bg=c["bg"])
        panel.attributes("-topmost", True)
        panel.geometry(self._panel_geometry(590, 760))
        panel.minsize(520, 620)
        panel.protocol("WM_DELETE_WINDOW", panel.withdraw)

        style = ttk.Style(panel)
        style.configure("Secretary.TButton", font=("Microsoft JhengHei", 9, "bold"), padding=(8, 5))

        header = tk.Frame(panel, bg=c["primary"], padx=16, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="教師秘書・小綿助", bg=c["primary"], fg="white", font=("Microsoft JhengHei", 17, "bold")).pack(anchor="w")
        tk.Label(header, text="桌面常駐｜先整理、再確認；系統與 Google 同步將於下一階段串接", bg=c["primary"], fg="#dcebe4", font=("Microsoft JhengHei", 9)).pack(anchor="w", pady=(3, 0))

        canvas = tk.Canvas(panel, bg=c["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        body = tk.Frame(canvas, bg=c["bg"], padx=14, pady=12)
        body_window = canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        body.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(body_window, width=e.width))
        panel.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        brief = self._card(body, "☀ 今日簡報", c["soft"])
        brief_label = tk.Label(brief, bg=c["soft"], fg=c["ink"], justify="left", anchor="w", wraplength=510, font=("Microsoft JhengHei", 10), pady=5)
        brief_label.pack(fill="x")
        brief_actions = tk.Frame(brief, bg=c["soft"])
        brief_actions.pack(fill="x", pady=(5, 0))
        ttk.Button(brief_actions, text="整理今天", style="Secretary.TButton", command=lambda: self._render_brief("today")).pack(side="left")
        ttk.Button(brief_actions, text="準備明天", style="Secretary.TButton", command=lambda: self._render_brief("tomorrow")).pack(side="left", padx=6)
        self.panel_widgets["brief"] = brief_label

        task_grid = tk.Frame(body, bg=c["bg"])
        task_grid.pack(fill="x", pady=9)
        task_grid.columnconfigure(0, weight=1)
        task_grid.columnconfigure(1, weight=1)
        today_card = self._card(task_grid, "📌 今日重要", c["bg"], pack=False)
        today_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        overdue_card = self._card(task_grid, "⚠ 已逾期", c["danger_soft"], pack=False)
        overdue_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.panel_widgets["today"] = self._listbox(today_card)
        self.panel_widgets["overdue"] = self._listbox(overdue_card)

        tracking = self._card(body, "📮 待追蹤｜等待回覆、尚未收齊", c["bg"])
        tracking.pack(fill="x", pady=(0, 9))
        self.panel_widgets["tracking"] = self._listbox(tracking, height=3)

        health = self._card(body, "🌿 健康管理", c["soft"])
        health.pack(fill="x", pady=(0, 9))
        self._build_health_rows(health)

        quick = self._card(body, "💬 快速交代", c["bg"])
        quick.pack(fill="x")
        tk.Label(quick, text="可輸入文字、選擇檔案，或按 Ctrl+V 貼上截圖／複製的檔案。", bg=c["bg"], fg=c["muted"], font=("Microsoft JhengHei", 8)).pack(anchor="w", pady=(0, 5))
        handoff = tk.Text(quick, height=4, wrap="word", relief="solid", borderwidth=1, font=("Microsoft JhengHei", 10), undo=True)
        handoff.pack(fill="x")
        handoff.bind("<Control-v>", self._paste_attachment, add="+")
        self.panel_widgets["handoff"] = handoff
        attachment_label = tk.Label(quick, text="尚未加入附件", bg=c["bg"], fg=c["muted"], anchor="w", justify="left", wraplength=510, font=("Microsoft JhengHei", 8))
        attachment_label.pack(fill="x", pady=5)
        self.panel_widgets["attachments"] = attachment_label
        actions = tk.Frame(quick, bg=c["bg"])
        actions.pack(fill="x")
        ttk.Button(actions, text="📎 圖片／檔案", style="Secretary.TButton", command=self._choose_attachments).pack(side="left")
        ttk.Button(actions, text="清除附件", style="Secretary.TButton", command=self._clear_attachments).pack(side="left", padx=5)
        ttk.Button(actions, text="🎙 語音交代", style="Secretary.TButton", command=self._voice_handoff).pack(side="left", padx=5)
        ttk.Button(actions, text="交給小綿助整理", style="Secretary.TButton", command=self._analyze_handoff).pack(side="right")
        ttk.Button(actions, text="先存為記事", style="Secretary.TButton", command=self._save_note).pack(side="right", padx=5)

        draft = tk.Frame(body, bg=c["gold_soft"], padx=12, pady=10, highlightbackground="#d9c58e", highlightthickness=1)
        draft_label = tk.Label(draft, bg=c["gold_soft"], fg=c["ink"], justify="left", anchor="w", wraplength=500, font=("Microsoft JhengHei", 10, "bold"))
        draft_label.pack(fill="x")
        draft_actions = tk.Frame(draft, bg=c["gold_soft"])
        draft_actions.pack(fill="x", pady=(8, 0))
        ttk.Button(draft_actions, text="確認建立本機任務", style="Secretary.TButton", command=self._confirm_draft).pack(side="left")
        ttk.Button(draft_actions, text="返回修改", style="Secretary.TButton", command=draft.pack_forget).pack(side="left", padx=6)
        self.panel_widgets["draft_frame"] = draft
        self.panel_widgets["draft_label"] = draft_label

        panel.bind("<Escape>", lambda _e: panel.withdraw())
        self._render_brief("tomorrow" if datetime.now().hour >= 15 else "today")
        self._render_health()

    def _panel_geometry(self, width: int, height: int) -> str:
        x = max(10, self.x - width + 130)
        y = max(10, min(self.screen_height - height - 50, self.y - height + 180))
        return f"{width}x{height}+{x}+{y}"

    def _card(self, parent: tk.Misc, title: str, bg: str, pack: bool = True) -> tk.Frame:
        frame = tk.Frame(parent, bg=bg, padx=10, pady=9, highlightbackground=self.COLORS["line"], highlightthickness=1)
        if pack:
            frame.pack(fill="x")
        tk.Label(frame, text=title, bg=bg, fg=self.COLORS["strong"], font=("Microsoft JhengHei", 10, "bold")).pack(anchor="w", pady=(0, 5))
        return frame

    @staticmethod
    def _listbox(parent: tk.Misc, height: int = 4) -> tk.Listbox:
        box = tk.Listbox(parent, height=height, borderwidth=0, highlightthickness=0, activestyle="none", font=("Microsoft JhengHei", 9))
        box.pack(fill="both", expand=True)
        return box

    def _build_health_rows(self, parent: tk.Frame) -> None:
        c = self.COLORS
        rows = [
            ("water", "💧 喝水", "喝一杯", lambda: self._record_health("water")),
            ("move", "🚶 起身活動", "活動完成", lambda: self._record_health("move")),
        ]
        for key, title, button_text, command in rows:
            row = tk.Frame(parent, bg=c["soft"], pady=3)
            row.pack(fill="x")
            tk.Label(row, text=title, bg=c["soft"], fg=c["ink"], width=12, anchor="w", font=("Microsoft JhengHei", 9, "bold")).pack(side="left")
            label = tk.Label(row, bg=c["soft"], fg=c["muted"], anchor="w", font=("Microsoft JhengHei", 8))
            label.pack(side="left", fill="x", expand=True)
            ttk.Button(row, text=button_text, style="Secretary.TButton", command=command).pack(side="right")
            self.panel_widgets[f"health_{key}"] = label

        row = tk.Frame(parent, bg=c["soft"], pady=3)
        row.pack(fill="x")
        tk.Label(row, text="💊 服藥", bg=c["soft"], fg=c["ink"], width=12, anchor="w", font=("Microsoft JhengHei", 9, "bold")).pack(side="left")
        label = tk.Label(row, bg=c["soft"], fg=c["muted"], anchor="w", font=("Microsoft JhengHei", 8))
        label.pack(side="left", fill="x", expand=True)
        med_var = tk.StringVar(value=self.data["health"].get("medicine_time", ""))
        med_entry = ttk.Entry(row, width=7, textvariable=med_var)
        med_entry.pack(side="left", padx=4)
        med_entry.bind("<FocusOut>", lambda _e: self._set_medicine_time(med_var.get()))
        ttk.Button(row, text="已服用", style="Secretary.TButton", command=lambda: self._record_health("medicine")).pack(side="right")
        self.panel_widgets["health_medicine"] = label

    def _render_dashboard(self) -> None:
        if not self.panel_widgets:
            return
        today = date.today().isoformat()
        active = [task for task in self.data["tasks"] if task.get("status") != "已完成"]
        due_today = [task for task in active if task.get("due_date") == today]
        overdue = [task for task in active if task.get("due_date") and task["due_date"] < today]
        tracking = [task for task in active if task.get("waiting_for") or task.get("status") == "等待回覆"]
        self._fill_task_list("today", due_today, "今天沒有期限任務")
        self._fill_task_list("overdue", overdue, "目前沒有逾期任務")
        self._fill_task_list("tracking", tracking, "目前沒有等待回覆的事項")
        self._render_health()

    def _fill_task_list(self, key: str, tasks: list[dict], empty: str) -> None:
        box: tk.Listbox = self.panel_widgets[key]  # type: ignore[assignment]
        box.delete(0, "end")
        if not tasks:
            box.insert("end", empty)
            return
        for task in tasks[:5]:
            suffix = f"｜{task.get('due_time')}" if task.get("due_time") else ""
            box.insert("end", f"{task.get('title', '未命名')}{suffix}")

    def _render_brief(self, mode: str) -> None:
        if "brief" not in self.panel_widgets:
            return
        target = date.today() + (timedelta(days=1) if mode == "tomorrow" else timedelta())
        active = [task for task in self.data["tasks"] if task.get("status") != "已完成"]
        due = [task for task in active if task.get("due_date") == target.isoformat()]
        overdue = [task for task in active if task.get("due_date") and task["due_date"] < date.today().isoformat()] if mode == "today" else []
        tracking = [task for task in active if task.get("waiting_for") or task.get("status") == "等待回覆"]
        if mode == "tomorrow":
            text = f"明天有 {len(due)} 件期限任務。\n" + (f"建議先準備：{due[0]['title']}" if due else "目前沒有需要提前準備的期限事項。")
        else:
            text = f"今天有 {len(due)} 件期限任務、{len(overdue)} 件逾期、{len(tracking)} 件等待回覆。\n"
            text += f"建議優先處理：{overdue[0]['title']}" if overdue else f"今天先完成：{due[0]['title']}" if due else "今天的期限工作已整理完成。"
        label: tk.Label = self.panel_widgets["brief"]  # type: ignore[assignment]
        label.configure(text=text)

    def _render_health(self) -> None:
        if "health_water" not in self.panel_widgets:
            return
        health = self.data["health"]
        water: tk.Label = self.panel_widgets["health_water"]  # type: ignore[assignment]
        move: tk.Label = self.panel_widgets["health_move"]  # type: ignore[assignment]
        medicine: tk.Label = self.panel_widgets["health_medicine"]  # type: ignore[assignment]
        water.configure(text=f"今天 {health.get('water_count', 0)} 杯")
        move.configure(text="今天已完成" if health.get("move_done_date") == date.today().isoformat() else "今天尚未記錄")
        medicine.configure(text="未設定時間" if not health.get("medicine_time") else "今天已完成" if health.get("medicine_done_date") == date.today().isoformat() else f"提醒 {health['medicine_time']}")

    def _record_health(self, kind: str) -> None:
        health = self.data["health"]
        if kind == "water":
            health["water_count"] = int(health.get("water_count", 0)) + 1
            health["last_water"] = now_iso()
            self.health_alerted["water"] = False
            message = "喝水完成！"
        elif kind == "move":
            health["last_move"] = now_iso()
            health["move_done_date"] = date.today().isoformat()
            self.health_alerted["move"] = False
            message = "起身活動完成！"
        else:
            if not health.get("medicine_time"):
                messagebox.showinfo(APP_NAME, "請先輸入服藥提醒時間，例如 13:30。", parent=self.panel)
                return
            health["medicine_done_date"] = date.today().isoformat()
            self.health_alerted["medicine"] = False
            message = "今天的服藥紀錄已完成。"
        self._save_data()
        self._render_health()
        self.play("success", 2, "idle", message)

    def _set_medicine_time(self, value: str) -> None:
        value = value.strip()
        if value and not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
            messagebox.showwarning(APP_NAME, "請輸入 24 小時格式，例如 13:30。", parent=self.panel)
            return
        self.data["health"]["medicine_time"] = value
        self.data["health"]["medicine_done_date"] = ""
        self.health_alerted["medicine"] = False
        self._save_data()
        self._render_health()

    def _health_tick(self) -> None:
        health = self.data["health"]
        now = datetime.now()
        if health.get("date") != date.today().isoformat():
            health["date"] = date.today().isoformat()
            health["water_count"] = 0
            self._save_data()
            self._render_health()
        alerts: list[str] = []
        for key, field, minutes, message in [
            ("water", "last_water", 60, "忙了一段時間，記得喝口水。"),
            ("move", "last_move", 50, "已經坐了快一小時，起身活動一下吧！"),
        ]:
            try:
                elapsed = now - datetime.fromisoformat(health[field])
            except (KeyError, TypeError, ValueError):
                elapsed = timedelta()
            if elapsed >= timedelta(minutes=minutes) and not self.health_alerted[key]:
                self.health_alerted[key] = True
                alerts.append(message)
        med_time = health.get("medicine_time", "")
        if med_time and health.get("medicine_done_date") != date.today().isoformat() and now.strftime("%H:%M") >= med_time and not self.health_alerted["medicine"]:
            self.health_alerted["medicine"] = True
            alerts.append(f"服藥提醒時間 {med_time} 到了，請依自己的醫囑處理。")
        if alerts:
            self.play("warning", 3, "idle", alerts[0])
        self.root.after(60_000, self._health_tick)

    def _opening_brief(self) -> None:
        today = date.today().isoformat()
        active = [task for task in self.data["tasks"] if task.get("status") != "已完成"]
        overdue = [task for task in active if task.get("due_date") and task["due_date"] < today]
        due = [task for task in active if task.get("due_date") == today]
        if overdue:
            self.show_bubble(f"有 {len(overdue)} 件逾期任務，要先看看嗎？", 4200)
        elif due:
            self.show_bubble(f"今天有 {len(due)} 件期限任務。", 3600)

    def _choose_attachments(self) -> None:
        paths = filedialog.askopenfilenames(
            title="交給小綿助整理",
            filetypes=[("支援的檔案", "*.png *.jpg *.jpeg *.webp *.pdf *.txt *.md *.csv *.doc *.docx *.xls *.xlsx *.ppt *.pptx"), ("所有檔案", "*.*")],
            parent=self.panel,
        )
        self._add_attachment_paths([Path(path) for path in paths])

    def _paste_attachment(self, _event: tk.Event) -> str | None:
        try:
            content = ImageGrab.grabclipboard()
        except OSError:
            return None
        if isinstance(content, Image.Image):
            target = ATTACHMENT_ROOT / f"貼上圖片-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
            content.save(target, "PNG")
            self._add_attachment_paths([target])
            return "break"
        if isinstance(content, list):
            paths = [Path(item) for item in content if Path(item).is_file()]
            if paths:
                self._add_attachment_paths(paths)
                return "break"
        return None

    def _add_attachment_paths(self, paths: list[Path]) -> None:
        for path in paths:
            if len(self.attachments) >= 10:
                messagebox.showwarning(APP_NAME, "一次最多加入 10 個附件。", parent=self.panel)
                break
            try:
                if path.stat().st_size > 35 * 1024 * 1024:
                    messagebox.showwarning(APP_NAME, f"{path.name} 超過單檔 35 MB。", parent=self.panel)
                    continue
            except OSError:
                continue
            if path not in self.attachments:
                self.attachments.append(path)
        self._render_attachments()

    def _render_attachments(self) -> None:
        if "attachments" not in self.panel_widgets:
            return
        label: tk.Label = self.panel_widgets["attachments"]  # type: ignore[assignment]
        label.configure(text="尚未加入附件" if not self.attachments else "附件：" + "、".join(path.name for path in self.attachments))

    def _clear_attachments(self) -> None:
        self.attachments = []
        self._render_attachments()

    def _voice_handoff(self) -> None:
        handoff: tk.Text = self.panel_widgets["handoff"]  # type: ignore[assignment]
        handoff.focus_set()
        self.panel.update_idletasks()
        if sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                keyup = 0x0002
                user32.keybd_event(0x5B, 0, 0, 0)
                user32.keybd_event(ord("H"), 0, 0, 0)
                user32.keybd_event(ord("H"), 0, keyup, 0)
                user32.keybd_event(0x5B, 0, keyup, 0)
            except (AttributeError, OSError):
                pass
        self.show_bubble("已開啟 Windows 語音輸入；說完後再交給我整理。", 3000)

    def _analyze_handoff(self) -> None:
        handoff: tk.Text = self.panel_widgets["handoff"]  # type: ignore[assignment]
        text = handoff.get("1.0", "end").strip()
        if not text and not self.attachments:
            messagebox.showinfo(APP_NAME, "請輸入交代內容，或加入圖片／檔案。", parent=self.panel)
            return
        source = text or "處理附件：" + "、".join(path.name for path in self.attachments)
        due_date = self._parse_date(source)
        due_time_match = re.search(r"(?:上午|下午|晚上)?\s*(\d{1,2})[:：點](\d{2})", source)
        due_time = f"{int(due_time_match.group(1)):02d}:{due_time_match.group(2)}" if due_time_match else ""
        title = re.sub(r"(今天|明天|後天|請|幫我|記得|提醒我|提醒|加入|新增|待辦)", " ", source)
        title = re.sub(r"\s+", " ", title).strip(" ，。,.！!")[:80] or "未命名事項"
        kind = "行程" if re.search(r"會議|開會|日曆|行事曆", source) else "任務"
        waiting_for = "" if not re.search(r"等待|回覆|收齊|調查", source) else "待確認對象"
        self.draft = {
            "id": str(uuid.uuid4()), "title": title, "kind": kind, "due_date": due_date,
            "due_time": due_time, "priority": "高" if due_date <= (date.today() + timedelta(days=1)).isoformat() else "中",
            "status": "等待回覆" if waiting_for else "未開始", "waiting_for": waiting_for,
            "attachment_names": [path.name for path in self.attachments], "source": source, "created_at": now_iso(),
        }
        label: tk.Label = self.panel_widgets["draft_label"]  # type: ignore[assignment]
        label.configure(text=f"建議建立{kind}：{title}\n日期：{due_date} {due_time or '未指定時間'}｜優先級：{self.draft['priority']}\n附件：{len(self.attachments)} 個。請確認後才會寫入本機任務清單。")
        frame: tk.Frame = self.panel_widgets["draft_frame"]  # type: ignore[assignment]
        frame.pack(fill="x", pady=(10, 0))
        frame.lift()
        self.play("think", 2, "idle", "我整理好了，請你確認。")

    @staticmethod
    def _parse_date(text: str) -> str:
        explicit = re.search(r"(20\d{2})[年/-](\d{1,2})[月/-](\d{1,2})", text)
        if explicit:
            return date(int(explicit.group(1)), int(explicit.group(2)), int(explicit.group(3))).isoformat()
        target = date.today()
        if "後天" in text:
            target += timedelta(days=2)
        elif "明天" in text:
            target += timedelta(days=1)
        return target.isoformat()

    def _confirm_draft(self) -> None:
        if not self.draft:
            return
        self.data["tasks"].append(self.draft)
        self._save_data()
        self.draft = None
        handoff: tk.Text = self.panel_widgets["handoff"]  # type: ignore[assignment]
        handoff.delete("1.0", "end")
        self.attachments = []
        self._render_attachments()
        frame: tk.Frame = self.panel_widgets["draft_frame"]  # type: ignore[assignment]
        frame.pack_forget()
        self._render_dashboard()
        self.play("success", 2, "idle", "完成！已加入桌面秘書任務清單。")

    def _save_note(self) -> None:
        handoff: tk.Text = self.panel_widgets["handoff"]  # type: ignore[assignment]
        text = handoff.get("1.0", "end").strip()
        if not text and not self.attachments:
            messagebox.showinfo(APP_NAME, "目前沒有可以儲存的內容。", parent=self.panel)
            return
        self.data["notes"].insert(0, {"text": text, "attachments": [path.name for path in self.attachments], "created_at": now_iso()})
        self._save_data()
        handoff.delete("1.0", "end")
        self.attachments = []
        self._render_attachments()
        self.play("success", 2, "idle", "記事已保存在本機。")


if __name__ == "__main__":
    SecretaryPet().run()
