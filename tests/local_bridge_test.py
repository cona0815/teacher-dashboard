import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import tkinter as tk

from desktop_pet_preview import DesktopPetPreview

from desktop_pet_secretary import (
    LocalBridgeServer,
    SecretaryPet,
    bridge_origin_allowed,
    default_data,
    make_bridge_handler,
    sanitize_line_inbox,
)


class _DeadRoot:
    """模擬已關閉的 Tk root：after 一律拋 TclError，_panel_apply_action 會吞掉。"""

    def after(self, *args, **kwargs):
        raise tk.TclError("stub root")


class PanelActionStub:
    """只帶資料層的假秘書，直接借用 SecretaryPet 的面板動作方法。"""

    _panel_apply_action = SecretaryPet._panel_apply_action
    _panel_payload = SecretaryPet._panel_payload

    def __init__(self):
        self.data = default_data()
        self.data_lock = threading.Lock()
        self.root = _DeadRoot()
        self.saved = 0

    def _save_data(self):
        self.saved += 1

    def _pet_name(self):
        return "小綿助"


class DummySecretary:
    def _bridge_allowed_origin(self):
        return "https://teacher-dashboard.netlify.app"

    def _bridge_health(self):
        return {"ok": True, "service": "test"}

    def _bridge_sync(self, payload):
        return {"ok": True, "echo": payload}


class LocalBridgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LocalBridgeServer(("127.0.0.1", 0), make_bridge_handler(DummySecretary()))
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def request(self, path, origin="http://127.0.0.1:8765", payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            method="POST" if payload is not None else "GET",
            headers={"Origin": origin, "Content-Type": "application/json"},
        )
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_origin_policy(self):
        self.assertTrue(bridge_origin_allowed("http://127.0.0.1:8765"))
        self.assertTrue(bridge_origin_allowed("https://cona0815.github.io"))
        self.assertTrue(bridge_origin_allowed("https://teacher-dashboard.netlify.app", "https://teacher-dashboard.netlify.app"))
        self.assertFalse(bridge_origin_allowed("https://teacher-dashboard.netlify.app"))
        self.assertFalse(bridge_origin_allowed("https://example.com"))
        self.assertFalse(bridge_origin_allowed("http://teacher-dashboard.netlify.app"))

    def test_health_and_sync(self):
        status, health = self.request("/health")
        self.assertEqual(status, 200)
        self.assertTrue(health["ok"])
        status, result = self.request("/sync", payload={"tasks": [], "notes": []})
        self.assertEqual(status, 200)
        self.assertEqual(result["echo"], {"tasks": [], "notes": []})

    def test_sanitize_line_inbox(self):
        self.assertEqual(sanitize_line_inbox(None), [])
        self.assertEqual(sanitize_line_inbox("not-a-list"), [])
        items = sanitize_line_inbox([
            {"id": "L-1", "title": "收回條", "type": "task", "tag": "作業缺交", "medium": "voice", "createdAt": "2026-08-25T08:00:00"},
            {"id": "L-2", "title": "", "type": "note"},
            "garbage",
            {"id": "L-3", "title": "T" * 200, "type": "weird", "medium": "hack"},
        ])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["type"], "task")
        self.assertEqual(items[0]["medium"], "voice")
        self.assertEqual(items[0]["created_at"], "2026-08-25T08:00:00")
        self.assertEqual(items[1]["type"], "note")
        self.assertEqual(items[1]["medium"], "")
        self.assertEqual(len(items[1]["title"]), 80)

    def test_panel_health_detail_actions(self):
        stub = PanelActionStub()
        result = stub._panel_apply_action({"action": "set_move_interval", "minutes": "45"})
        self.assertTrue(result["ok"])
        self.assertEqual(stub.data["health"]["move_interval"], 45)
        result = stub._panel_apply_action({"action": "set_water_interval", "minutes": 999})
        self.assertTrue(result["ok"])
        self.assertEqual(stub.data["health"]["water_interval"], 240)
        self.assertEqual(result["health"]["waterInterval"], 240)
        bad = stub._panel_apply_action({"action": "set_move_interval", "minutes": "abc"})
        self.assertFalse(bad["ok"])
        bad = stub._panel_apply_action({"action": "add_medicine_time", "time": "25:00"})
        self.assertFalse(bad["ok"])
        stub._panel_apply_action({"action": "add_medicine_time", "time": "12:30"})
        result = stub._panel_apply_action({"action": "add_medicine_time", "time": "08:00"})
        self.assertEqual(result["health"]["medicineTimes"], ["08:00", "12:30"])
        self.assertEqual(stub.data["health"]["medicine_time"], "08:00")
        result = stub._panel_apply_action({"action": "remove_medicine_time", "time": "08:00"})
        self.assertEqual(result["health"]["medicineTimes"], ["12:30"])
        self.assertEqual(stub.data["health"]["medicine_time"], "12:30")
        self.assertGreater(stub.saved, 0)

    def test_rejects_foreign_origin(self):
        with self.assertRaises(HTTPError) as context:
            self.request("/health", origin="https://example.com")
        self.assertEqual(context.exception.code, 403)

    def _raw_status(self, path, headers, body=b'{"tasks": []}'):
        request = Request(f"http://127.0.0.1:{self.port}{path}", data=body, method="POST", headers=headers)
        try:
            with urlopen(request, timeout=3) as response:
                return response.status
        except HTTPError as error:
            return error.code

    def test_security_2026_11_06(self):
        """資安稽核 2026-11-06：null 來源、DNS rebinding、免預檢的外站寫入都要擋在處理資料之前。"""
        self.assertFalse(bridge_origin_allowed("null"))
        calls = []
        original = DummySecretary._bridge_sync
        DummySecretary._bridge_sync = lambda _self, payload: calls.append(payload) or {"ok": True}
        try:
            json_headers = {"Content-Type": "application/json"}
            self.assertEqual(self._raw_status("/sync", {**json_headers, "Origin": "null"}), 403)
            self.assertEqual(self._raw_status("/sync", {"Origin": "https://example.com", "Content-Type": "text/plain"}), 403)
            self.assertEqual(self._raw_status("/sync", {"Origin": "http://127.0.0.1:8765", "Content-Type": "text/plain"}), 403)
            self.assertEqual(self._raw_status("/sync", {**json_headers, "Origin": "http://127.0.0.1:8765", "Host": "evil.example:8767"}), 403)
            self.assertEqual(calls, [], "被擋下的請求不可寫入任何資料")
            self.assertEqual(self._raw_status("/sync", {**json_headers, "Origin": "http://127.0.0.1:8765"}), 200)
            self.assertEqual(len(calls), 1)
        finally:
            DummySecretary._bridge_sync = original
        request = Request(f"http://127.0.0.1:{self.port}/health", headers={"Origin": "http://127.0.0.1:8765"})
        with urlopen(request, timeout=3) as response:
            self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")


if __name__ == "__main__":
    unittest.main()


class CloudLinkTest(unittest.TestCase):
    """v2.0 方案 B：桌寵只允許連老師自己的 Apps Script。"""

    def test_host_whitelist(self):
        from desktop_pet_cloud import cloud_url_allowed

        self.assertTrue(cloud_url_allowed("https://script.google.com/macros/s/abc/exec"))
        self.assertFalse(cloud_url_allowed("https://example.com/exec"))
        self.assertFalse(cloud_url_allowed("http://script.google.com/macros/s/abc/exec"))
        self.assertFalse(cloud_url_allowed(""))

    def test_only_read_actions_and_prompt_set(self):
        from desktop_pet_cloud import CloudLink

        calls = []

        def opener(url, body):
            calls.append(json.loads(body.decode("utf-8")))
            return {"ok": True, "items": [], "snapshot": None, "prompt": None}

        link = CloudLink(opener=opener)
        link.configure("https://script.google.com/macros/s/abc/exec", "token-c")
        link.call("prompt_set", {"text": "排隊囉"})
        with self.assertRaises(ValueError):
            link.call("ack", {"ids": ["1"]})
        with self.assertRaises(ValueError):
            link.call("backup_save", {})
        self.assertEqual(calls[0]["action"], "prompt_set")
        self.assertEqual(calls[0]["token"], "token-c")

    def test_focus_classifier_and_tracker(self):
        from desktop_pet_cloud import FocusTracker, ForegroundMonitor

        monitor = ForegroundMonitor(lambda: "")
        self.assertEqual(monitor.classify("YouTube - Chrome", ["youtube"], []), "drift")
        self.assertEqual(monitor.classify("晨間大屏｜點名", ["youtube"], []), "pause")
        self.assertEqual(monitor.classify("YouTube 教學影片", ["youtube"], ["YouTube 教學影片"]), "pause")
        self.assertEqual(monitor.classify("備課.docx - Word", ["youtube"], []), "focus")
        tracker = FocusTracker(threshold_minutes=1, cooldown_minutes=10)
        health = {}
        alerted = [tracker.observe("drift", health, 2) for _ in range(31)]
        self.assertEqual(alerted.count(True), 1)
        self.assertGreaterEqual(health["drift_seconds"], 60)

    def test_panel_set_cloud_rejects_other_hosts(self):
        stub = PanelActionStub()
        stub._configure_cloud = lambda: None
        result = stub._panel_apply_action({"action": "set_cloud", "url": "https://evil.example/exec", "token": "x"})
        self.assertFalse(result["ok"])
        result = stub._panel_apply_action({"action": "set_cloud", "url": "https://script.google.com/macros/s/abc/exec", "token": "x"})
        self.assertTrue(result["ok"])
        self.assertTrue(stub.data["settings"]["cloud_enabled"])
        self.assertIn("cloud", result)
        self.assertIn("focus", result)


class PanelLocalOnlyTest(unittest.TestCase):
    """資安修正：面板端點只接受本機來源；網站來源即使在橋接白名單也不得存取。"""

    @classmethod
    def setUpClass(cls):
        cls.server = LocalBridgeServer(("127.0.0.1", 0), make_bridge_handler(DummySecretary()))
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _status(self, path, origin, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(f"http://127.0.0.1:{self.port}{path}", data=data, headers={"Origin": origin, "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=3) as response:
                return response.status
        except HTTPError as error:
            return error.code

    def test_web_origin_cannot_touch_panel(self):
        web = "https://teacher-dashboard.netlify.app"
        self.assertEqual(self._status("/panel-data", web), 403)
        self.assertEqual(self._status("/panel-action", web, {"action": "set_cloud", "url": "https://script.google.com/macros/s/x/exec"}), 403)
        # 同一來源仍可用 /sync（既有功能不受影響）
        self.assertEqual(self._status("/sync", web, {"tasks": []}), 200)

    def test_set_cloud_url_change_clears_token(self):
        stub = PanelActionStub()
        stub._configure_cloud = lambda: None
        stub._panel_apply_action({"action": "set_cloud", "url": "https://script.google.com/macros/s/AAA/exec", "token": "secret-c"})
        self.assertEqual(stub.data["settings"]["cloud_token"], "secret-c")
        result = stub._panel_apply_action({"action": "set_cloud", "url": "https://script.google.com/macros/s/BBB/exec", "token": ""})
        self.assertEqual(stub.data["settings"]["cloud_token"], "")
        self.assertFalse(stub.data["settings"]["cloud_enabled"])
        self.assertTrue(result["ok"])


class VoiceModuleTest(unittest.TestCase):
    """v2.1 會聽的小綿助：音檔只准送 Gemini／Groq 官方網域；引擎流程用假 opener 驗證。"""

    def test_voice_host_whitelist(self):
        from desktop_pet_voice import voice_url_allowed, VOICE_ALLOWED_HOSTS
        self.assertTrue(voice_url_allowed("https://generativelanguage.googleapis.com/v1beta/models/x:generateContent"))
        self.assertTrue(voice_url_allowed("https://api.groq.com/openai/v1/audio/transcriptions"))
        self.assertFalse(voice_url_allowed("https://script.google.com/macros/s/x/exec"))
        self.assertFalse(voice_url_allowed("http://api.groq.com/openai/v1/audio/transcriptions"))
        self.assertEqual(set(VOICE_ALLOWED_HOSTS), {"generativelanguage.googleapis.com", "api.groq.com"})

    def test_wav_and_silence_and_hallucination(self):
        import numpy as np
        from desktop_pet_voice import wav_bytes, is_silent, looks_like_hallucination
        loud = (np.sin(np.linspace(0, 200, 16000)) * 8000).astype(np.int16)
        self.assertTrue(wav_bytes(loud).startswith(b"RIFF"))
        self.assertFalse(is_silent(loud))
        self.assertTrue(is_silent(np.zeros(16000, dtype=np.int16)))
        self.assertTrue(looks_like_hallucination("謝謝大家 請訂閱"))
        self.assertFalse(looks_like_hallucination("明天早上八點半家長到校"))

    def test_engine_gemini_and_groq_paths(self):
        import numpy as np
        from desktop_pet_voice import VoiceEngine
        calls = []

        def opener(url, headers, body):
            calls.append((url, headers))
            if "generativelanguage" in url:
                return 200, json.dumps({"candidates": [{"content": {"parts": [{"text": "明天要交同意书。"}]}}]}).encode()
            if url.endswith("/audio/transcriptions"):
                return 200, json.dumps({"text": "嗯 明天要交同意书"}).encode()
            return 200, json.dumps({"choices": [{"message": {"content": "明天要交同意書。"}}]}).encode()

        audio = (np.sin(np.linspace(0, 200, 16000)) * 8000).astype(np.int16)
        engine = VoiceEngine(opener=opener)
        engine.configure({"voice_provider": "auto", "voice_gemini_key": "AIza-test"})
        self.assertEqual(engine.resolved_provider(), "gemini")
        text = engine.transcribe(audio)
        self.assertIn("同意", text)
        self.assertEqual(calls[0][1]["x-goog-api-key"], "AIza-test")
        # 兩把都有：自動模式 Gemini 優先（老師只要申請一把 Gemini 金鑰）
        engine.configure({"voice_provider": "auto", "voice_gemini_key": "AIza-test", "voice_groq_key": "gsk_test"})
        self.assertEqual(engine.resolved_provider(), "gemini")
        engine.configure({"voice_provider": "auto", "voice_groq_key": "gsk_test"})
        self.assertEqual(engine.resolved_provider(), "groq")
        engine.configure({"voice_provider": "groq", "voice_gemini_key": "AIza-test", "voice_groq_key": "gsk_test"})
        self.assertEqual(engine.resolved_provider(), "groq")
        self.assertEqual(engine.transcribe(audio), "明天要交同意書。")
        self.assertTrue(calls[-2][0].endswith("/audio/transcriptions"))
        self.assertTrue(calls[-2][1]["Content-Type"].startswith("multipart/form-data"))

    def test_engine_gemini_quota_falls_back_to_groq(self):
        import numpy as np
        from desktop_pet_voice import VoiceEngine
        calls = []

        def opener(url, headers, body):
            calls.append(url)
            if "generativelanguage" in url:
                return 429, b'{"error":{"message":"quota"}}'
            if url.endswith("/audio/transcriptions"):
                return 200, json.dumps({"text": "明天要交同意書"}).encode()
            return 200, json.dumps({"choices": [{"message": {"content": "明天要交同意書。"}}]}).encode()

        audio = (np.sin(np.linspace(0, 200, 16000)) * 8000).astype(np.int16)
        engine = VoiceEngine(opener=opener, lister=lambda url, headers: (200, b'{"models":[]}'))
        engine.configure({"voice_provider": "auto", "voice_gemini_key": "AIza-test", "voice_groq_key": "gsk_test"})
        self.assertEqual(engine.transcribe(audio), "明天要交同意書。")
        self.assertEqual(engine.last_provider, "groq")
        self.assertIn("generativelanguage", calls[0])

    def test_groq_models_follow_groq(self):
        """Groq 把寫死的模型全部停用、只剩新名字：自動問 Groq 清單、改用新模型，第二次直接用記住的。"""
        import numpy as np
        from desktop_pet_voice import VoiceEngine, rank_groq_models
        alive = {"whisper-large-v9", "llama-9-90b-chat"}
        used = []

        def opener(url, headers, body):
            model = json.loads(body)["model"] if url.endswith("/chat/completions") else body.split(b'name="model"\r\n\r\n')[1].split(b"\r\n")[0].decode()
            used.append(model)
            if model not in alive:
                return 400, b'{"error":{"message":"The model has been decommissioned","code":"model_decommissioned"}}'
            if url.endswith("/audio/transcriptions"):
                return 200, json.dumps({"text": "明天要交同意書"}).encode()
            return 200, json.dumps({"choices": [{"message": {"content": "明天要交同意書。"}}]}).encode()

        listing = {"data": [{"id": "whisper-large-v9"}, {"id": "distil-whisper-large-v9-en"}, {"id": "llama-9-90b-chat"},
                            {"id": "llama-guard-9-8b"}, {"id": "llama-9-8b-instant"}, {"id": "playai-tts"}]}
        engine = VoiceEngine(opener=opener, lister=lambda url, headers: (200, json.dumps(listing).encode()))
        engine.configure({"voice_provider": "groq", "voice_groq_key": "gsk_test"})
        audio = (np.sin(np.linspace(0, 200, 16000)) * 8000).astype(np.int16)
        self.assertEqual(engine.transcribe(audio), "明天要交同意書。")
        self.assertEqual(engine.groq_last_good, {"stt": "whisper-large-v9", "chat": "llama-9-90b-chat"})
        used.clear()
        engine.transcribe(audio)
        self.assertEqual(used, ["whisper-large-v9", "llama-9-90b-chat"])
        self.assertEqual(rank_groq_models([m["id"] for m in listing["data"]], "stt"), ["whisper-large-v9"])
        self.assertEqual(rank_groq_models([m["id"] for m in listing["data"]], "chat"), ["llama-9-90b-chat", "llama-9-8b-instant"])

    def test_engine_errors(self):
        import numpy as np
        from desktop_pet_voice import VoiceEngine, VoiceError
        audio = (np.sin(np.linspace(0, 200, 16000)) * 8000).astype(np.int16)
        engine = VoiceEngine(opener=lambda url, headers, body: (429, b'{"error":{"message":"quota"}}'))
        with self.assertRaises(VoiceError) as context:
            engine.transcribe(audio)
        self.assertEqual(context.exception.kind, "no_key")
        engine.configure({"voice_gemini_key": "AIza-test"})
        with self.assertRaises(VoiceError) as context:
            engine.transcribe(audio)
        self.assertEqual(context.exception.kind, "rate")
        self.assertEqual(engine.transcribe(np.zeros(16000, dtype=np.int16)), "")

    def test_spoken_classifier(self):
        from desktop_pet_voice import classify_spoken_item, strip_spoken_prefix
        self.assertEqual(classify_spoken_item("明天要交校外教學同意書"), "task")
        self.assertEqual(classify_spoken_item("記事：小明今天很認真"), "note")
        self.assertEqual(classify_spoken_item("任務：整理教室"), "task")
        self.assertEqual(classify_spoken_item("下次班會討論座位"), "note")
        self.assertEqual(strip_spoken_prefix("任務：整理教室"), "整理教室")

    def test_panel_set_voice_validation(self):
        stub = PanelActionStub()
        stub._configure_voice = lambda: None
        stub.voice = None
        bad = stub._panel_apply_action({"action": "set_voice", "geminiKey": "notakey"})
        self.assertFalse(bad["ok"])
        bad = stub._panel_apply_action({"action": "set_voice", "hotkey": "ctrl_r", "petHotkey": "ctrl_r"})
        self.assertFalse(bad["ok"])
        result = stub._panel_apply_action({"action": "set_voice", "geminiKey": "AIza" + "x" * 35, "hotkey": "ctrl_r", "petHotkey": "f9", "style": "精簡重點"})
        self.assertTrue(result["ok"])
        self.assertEqual(stub.data["settings"]["voice_pet_hotkey"], "f9")
        self.assertEqual(stub.data["settings"]["voice_style"], "精簡重點")
        self.assertTrue(stub.data["settings"]["voice_gemini_key"].startswith("AIza"))
        result = stub._panel_apply_action({"action": "set_voice", "clearGeminiKey": True})
        self.assertEqual(stub.data["settings"]["voice_gemini_key"], "")

    def test_secretary_main_never_calls_urlopen_directly(self):
        import pathlib
        source = pathlib.Path(__file__).resolve().parent.parent.joinpath("desktop_pet_secretary.py").read_text(encoding="utf-8")
        self.assertNotIn("urlopen(", source)


class NoticeQueueTest(unittest.TestCase):
    """v2.2 訊息分級排隊：重要不被蓋、閒聊有待看就不講、勿擾只放行重要與操作回應。"""

    def _q(self):
        from desktop_pet_ui import NoticeQueue
        return NoticeQueue([])

    def test_urgent_never_overwritten(self):
        from desktop_pet_ui import Notice
        q = self._q()
        self.assertEqual(q.push(Notice("吃藥", "urgent", key="med")), "show")
        self.assertEqual(q.push(Notice("LINE 2 則", "urgent", key="line")), "queued")
        self.assertEqual(q.push(Notice("喝水", "normal", key="water")), "queued")
        self.assertEqual(q.push(Notice("好的", "feedback")), "queued")
        self.assertEqual(q.current.text, "吃藥")
        self.assertEqual(q.close_current().text, "LINE 2 則")

    def test_chatter_dropped_when_anything_pending(self):
        from desktop_pet_ui import Notice
        q = self._q()
        self.assertEqual(q.push(Notice("我去巡一下", "chatter")), "show")
        q.close_current()
        q.push(Notice("吃藥", "urgent"))
        self.assertEqual(q.push(Notice("我去巡一下", "chatter")), "dropped")

    def test_urgent_preempts_normal_and_requeues_it(self):
        from desktop_pet_ui import Notice
        q = self._q()
        q.push(Notice("喝水", "normal", key="water"))
        self.assertEqual(q.push(Notice("逾期 3 件", "urgent", key="overdue")), "show")
        self.assertEqual(q.pending[0].text, "喝水")

    def test_key_dedupe_and_update(self):
        from desktop_pet_ui import Notice
        q = self._q()
        q.push(Notice("LINE 1 則", "urgent", key="line"))
        self.assertEqual(q.push(Notice("LINE 3 則", "urgent", key="line")), "update")
        self.assertEqual(q.current.text, "LINE 3 則")
        self.assertEqual(sum(1 for e in q.log if e["key"] == "line"), 1)

    def test_dnd_only_urgent_and_feedback(self):
        import time as _t
        from desktop_pet_ui import Notice
        q = self._q()
        q.dnd_until = _t.time() + 60
        self.assertEqual(q.push(Notice("喝水", "normal")), "dropped")
        self.assertEqual(q.push(Notice("我去巡一下", "chatter")), "dropped")
        self.assertEqual(q.push(Notice("吃藥", "urgent")), "show")
        self.assertEqual(len(q.log), 2)   # 勿擾期間的一般提醒仍寫進通知紀錄

    def test_timeout_keeps_urgent_unread(self):
        from desktop_pet_ui import Notice
        q = self._q()
        q.push(Notice("逾期 3 件", "urgent", key="overdue"))
        q.close_current(read=False)
        self.assertEqual(q.unread_count(), 1)
        q.mark_all_read()
        self.assertEqual(q.unread_count(), 0)

    def test_duration_bounds(self):
        from desktop_pet_ui import Notice
        self.assertEqual(Notice("短", "normal").duration_ms(), 3090)
        self.assertEqual(Notice("字" * 200, "normal").duration_ms(), 10000)
        self.assertGreaterEqual(Notice("吃藥", "urgent").duration_ms(), 8000)

    def test_right_click_does_not_use_tk_menu(self):
        import pathlib
        source = pathlib.Path(__file__).resolve().parent.parent.joinpath("desktop_pet_secretary.py").read_text(encoding="utf-8")
        start = source.index("def _show_menu")
        body = source[start:source.index("\n    def ", start + 10)]
        self.assertIn("self.popup.open", body)
        self.assertNotIn("tk_popup", body)


class PetV5PackTest(unittest.TestCase):
    """v5 動畫包：四隻角色都有 16 種動作，檔案與 manifest 一致，程式用到的動作名都對得到。"""

    def setUp(self):
        from desktop_pet_v5 import ALIASES, CHARACTERS, PACK_ROOT

        self.root = PACK_ROOT
        self.aliases = ALIASES
        self.characters = CHARACTERS
        self.manifest = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))

    def test_every_character_has_the_same_actions_and_files(self):
        chars = self.manifest["characters"]
        self.assertEqual(set(chars), set(self.characters))
        actions = set(chars["lamb"])
        self.assertEqual(len(actions), 16)
        for char, items in chars.items():
            self.assertEqual(set(items), actions, char)
            for action, info in items.items():
                path = self.root / info["file"]
                self.assertTrue(path.is_file(), f"{char}/{action}")
                self.assertEqual(sum(info["durations"]), info["duration_ms"], f"{char}/{action}")
                if "source_frames" in info:   # v5（25fps 原始影格）才有
                    self.assertEqual(info["duration_ms"], info["source_frames"] * 40, f"{char}/{action}")
                self.assertEqual(len(info["durations"]), info["unique_frames"], f"{char}/{action}")

    def test_webp_frames_match_manifest(self):
        from PIL import Image

        info = self.manifest["characters"]["robot"]["remind"]
        with Image.open(self.root / info["file"]) as image:
            self.assertEqual(image.n_frames, len(info["durations"]))
            self.assertEqual(image.size, (320, 320))
            image.seek(image.n_frames // 2)
            image.load()
            self.assertEqual(image.info["duration"], info["durations"][image.n_frames // 2])
            self.assertEqual(image.convert("RGBA").getchannel("A").getextrema()[0], 0)   # 真的有透明

    def test_every_state_the_program_uses_maps_to_a_v5_action(self):
        actions = set(self.manifest["characters"]["lamb"])
        for state, action in self.aliases.items():
            self.assertIn(action, actions, state)
        used = set(DesktopPetPreview.FRAME_COUNTS) | set(DesktopPetPreview.OPTIONAL_FRAME_COUNTS)
        for choices in list(SecretaryPet.NOTICE_ANIMATIONS.values()) + list(SecretaryPet.ACTION_ANIMATIONS.values()):
            used |= set(choices)
        missing = {s for s in used if s not in self.aliases} - {"walk_left", "walk_right", "peek", "peek_left"}
        self.assertEqual(missing, set())

    def test_player_decodes_lazily_and_releases(self):
        from desktop_pet_v5 import PetPack

        pack = PetPack(self.root, "cat", 64, layered=True)
        states = pack.states()
        self.assertNotIn("walk_right", states)
        player = states["success"]
        self.assertTrue(all(frame is None for frame in player.cache))
        frame = player.frame(3)
        self.assertEqual(frame.size, (64, 64))
        self.assertIsNotNone(player.cache[3])
        for name in ("idle", "listen", "think", "note", "success"):
            pack.touch(states[name])
        self.assertTrue(all(f is None for f in player.cache) or len(pack.recent) <= PetPack.KEEP)
        self.assertTrue(pack.set_character("robot"))
        self.assertFalse(pack.set_character("robot"))
        self.assertFalse(pack.set_character("shiba"))


class PetV3AssetsTest(unittest.TestCase):
    """v3 動作圖：安裝好的單格圖要和程式的格數、規格表一致。"""

    def setUp(self):
        from pathlib import Path
        from desktop_pet_preview import DesktopPetPreview

        self.root = Path(__file__).resolve().parents[1]
        self.pet = DesktopPetPreview
        self.frames = self.root / "assets" / "pet" / "frames"
        self.spec = json.loads((self.root / "assets" / "pet" / "v3" / "spec.json").read_text(encoding="utf-8"))

    def test_required_frames_installed_with_exact_counts(self):
        from PIL import Image

        for state, count in self.pet.FRAME_COUNTS.items():
            paths = sorted((self.frames / f"pet_{state}").glob("*.png"))
            self.assertEqual(len(paths), count, state)
            with Image.open(paths[0]) as image:
                self.assertEqual(image.size, (512, 512), state)
                self.assertEqual(image.mode, "RGBA", state)

    def test_optional_frames_either_absent_or_complete(self):
        for state, count in self.pet.OPTIONAL_FRAME_COUNTS.items():
            paths = sorted((self.frames / f"pet_{state}").glob("*.png"))
            self.assertIn(len(paths), (0, count), state)

    def test_counts_match_spec_and_every_state_has_speed(self):
        spec = {a["name"]: a["frames"] for a in self.spec["actions"]}
        mirrored = {"walk_left": "walk_right", "peek_left": "peek"}
        for state, count in {**self.pet.FRAME_COUNTS, **self.pet.OPTIONAL_FRAME_COUNTS}.items():
            self.assertEqual(spec[mirrored.get(state, state)], count, state)
            self.assertIn(state, self.pet.FRAME_DELAYS, state)
        self.assertEqual(set(spec) - set(self.pet.FRAME_COUNTS) - set(self.pet.OPTIONAL_FRAME_COUNTS), set())

    def test_notice_and_action_animations_use_known_states(self):
        known = set(self.pet.FRAME_COUNTS) | set(self.pet.OPTIONAL_FRAME_COUNTS)
        for choices in list(SecretaryPet.NOTICE_ANIMATIONS.values()) + list(SecretaryPet.ACTION_ANIMATIONS.values()):
            for state in choices:
                self.assertIn(state, known)

    def test_fullscreen_probe_never_raises(self):
        from desktop_pet_cloud import ForegroundMonitor

        self.assertIsInstance(ForegroundMonitor.is_fullscreen(), bool)
