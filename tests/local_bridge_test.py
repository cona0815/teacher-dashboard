import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import tkinter as tk

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
        engine.configure({"voice_provider": "auto", "voice_gemini_key": "AIza-test", "voice_groq_key": "gsk_test"})
        self.assertEqual(engine.resolved_provider(), "groq")
        self.assertEqual(engine.transcribe(audio), "明天要交同意書。")
        self.assertTrue(calls[-2][0].endswith("/audio/transcriptions"))
        self.assertTrue(calls[-2][1]["Content-Type"].startswith("multipart/form-data"))

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
