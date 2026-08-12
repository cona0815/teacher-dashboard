import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from desktop_pet_secretary import LocalBridgeServer, bridge_origin_allowed, make_bridge_handler


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

    def test_rejects_foreign_origin(self):
        with self.assertRaises(HTTPError) as context:
            self.request("/health", origin="https://example.com")
        self.assertEqual(context.exception.code, 403)


if __name__ == "__main__":
    unittest.main()
