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
