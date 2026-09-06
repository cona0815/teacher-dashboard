"""小綿助 v2.0 雲端連線與專注偵測模組。

安全契約（2026-09-04 使用者核定「方案 B」）：
- 桌寵只允許連線到老師自己的 Google Apps Script（script.google.com /
  script.googleusercontent.com），其他任何網域一律拒絕，程式內硬擋。
- 讀為主：工作台快照、LINE 待整理（只看不確認）、大屏提示狀態。
- 唯一的寫入動作是 prompt_set（遙控大屏提示）。
- 專注偵測只讀「作用中視窗標題」，不截圖、不上傳、不記錄標題內容。
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date
from typing import Callable
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ALLOWED_HOSTS = ("script.google.com", "script.googleusercontent.com")
CLOUD_TIMEOUT_SECONDS = 15
PROMPT_SET_ACTION = "prompt_set"
READ_ACTIONS = ("ping", "snapshot_get", "pull", "prompt_get")
DEFAULT_FOCUS_KEYWORDS = [
    "youtube", "facebook", "instagram", "threads", "蝦皮", "shopee", "momo",
    "netflix", "shorts", "reels", "tiktok", "抖音",
]
BIG_SCREEN_MARKERS = ("晨間大屏", "教材小工場")


def cloud_url_allowed(url: str) -> bool:
    """只放行 https 且主機在白名單內的 Apps Script 網址。"""
    try:
        parsed = urlparse(str(url or "").strip())
    except ValueError:
        return False
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS


class CloudLink:
    """經 urllib 直連老師自己的 GAS。"""

    def __init__(self, opener: Callable | None = None) -> None:
        self.url = ""
        self.token = ""
        self.opener = opener or self._default_opener
        self.backoff_until = 0.0
        self.failures = 0
        self.last_error = ""

    def configure(self, url: str, token: str) -> None:
        self.url = str(url or "").strip()
        self.token = str(token or "").strip()
        self.backoff_until = 0.0
        self.failures = 0

    @property
    def ready(self) -> bool:
        return bool(self.token) and cloud_url_allowed(self.url)

    @staticmethod
    def _default_opener(url: str, body: bytes) -> dict:
        request = Request(url, data=body, method="POST", headers={"Content-Type": "text/plain;charset=utf-8"})
        with urlopen(request, timeout=CLOUD_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))

    def call(self, action: str, extra: dict | None = None) -> dict:
        if action != PROMPT_SET_ACTION and action not in READ_ACTIONS:
            raise ValueError(f"桌寵不允許的動作：{action}")
        if not cloud_url_allowed(self.url):
            raise ValueError("只允許連線到 script.google.com 的 Apps Script 網址")
        if not self.token:
            raise ValueError("尚未設定 🔑C 老師金鑰")
        if time.time() < self.backoff_until:
            raise RuntimeError("連線暫時退避中")
        payload = {"action": action, "token": self.token}
        payload.update(extra or {})
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            result = self.opener(self.url, body)
        except (URLError, OSError, ValueError) as error:
            self._register_failure(str(error))
            raise RuntimeError(f"雲端連線失敗：{error}") from error
        if not isinstance(result, dict) or not result.get("ok"):
            message = str(result.get("error") if isinstance(result, dict) else "雲端回應異常")
            self._register_failure(message)
            raise RuntimeError(message)
        self.failures = 0
        self.last_error = ""
        return result

    def _register_failure(self, message: str) -> None:
        self.failures += 1
        self.last_error = message
        # 退避：2、4、8 分鐘，最多 10 分鐘，避免斷網時一直敲門
        self.backoff_until = time.time() + min(600, 120 * (2 ** min(self.failures - 1, 3)))

    def fetch_dashboard(self) -> dict:
        """一次拉齊桌寵要顯示的三樣東西；個別失敗不影響其他。"""
        result = {"fetchedAt": time.strftime("%H:%M"), "errors": []}
        for action, key in (("snapshot_get", "snapshot"), ("pull", "line"), ("prompt_get", "prompt")):
            try:
                response = self.call(action)
            except (RuntimeError, ValueError) as error:
                result["errors"].append(f"{key}: {error}")
                continue
            if key == "snapshot":
                result["snapshot"] = response.get("snapshot") or None
            elif key == "line":
                items = response.get("items") if isinstance(response.get("items"), list) else []
                result["lineCount"] = len(items)
                result["linePreview"] = [str(item.get("title") or item.get("text") or "")[:60] for item in items[:3] if isinstance(item, dict)]
            else:
                result["prompt"] = response.get("prompt") or None
        return result


class ForegroundMonitor:
    """作用中視窗標題偵測（純本機；沒有 Windows 時安靜地回傳空字串）。"""

    def __init__(self, title_reader: Callable[[], str] | None = None) -> None:
        self.read_title = title_reader or self._windows_title

    @staticmethod
    def _windows_title() -> str:
        if sys.platform != "win32":
            return ""
        try:
            import ctypes

            user32 = ctypes.windll.user32
            handle = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(handle)
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(handle, buffer, length + 1)
            return buffer.value
        except Exception:  # noqa: BLE001 - 偵測失敗只當作沒有視窗
            return ""

    @staticmethod
    def classify(title: str, keywords: list[str], whitelist: list[str]) -> str:
        """回傳 'drift' / 'focus' / 'pause'（大屏投影中或白名單）。"""
        lowered = str(title or "").lower()
        if not lowered:
            return "focus"
        if any(marker in title for marker in BIG_SCREEN_MARKERS):
            return "pause"
        if any(item and item.lower() in lowered for item in whitelist):
            return "pause"
        if any(keyword and str(keyword).lower() in lowered for keyword in keywords):
            return "drift"
        return "focus"


class FocusTracker:
    """累計今日專注／分心分鐘，並決定何時該提醒。"""

    def __init__(self, threshold_minutes: int = 3, cooldown_minutes: int = 10) -> None:
        self.threshold = max(1, int(threshold_minutes))
        self.cooldown = max(1, int(cooldown_minutes))
        self.drift_streak_seconds = 0
        self.last_alert_at = 0.0
        self.session_until = 0.0

    def start_session(self, minutes: int) -> None:
        self.session_until = time.time() + max(1, int(minutes)) * 60

    def stop_session(self) -> None:
        self.session_until = 0.0

    @property
    def in_session(self) -> bool:
        return time.time() < self.session_until

    def observe(self, status: str, health: dict, seconds: int = 2) -> bool:
        """更新統計並回傳「現在該提醒嗎」。"""
        today = date.today().isoformat()
        if health.get("focus_date") != today:
            health["focus_date"] = today
            health["focus_seconds"] = 0
            health["drift_seconds"] = 0
        if status == "drift":
            health["drift_seconds"] = int(health.get("drift_seconds") or 0) + seconds
            self.drift_streak_seconds += seconds
        elif status == "focus":
            health["focus_seconds"] = int(health.get("focus_seconds") or 0) + seconds
            self.drift_streak_seconds = 0
        else:
            self.drift_streak_seconds = 0
        if status != "drift":
            return False
        needed = 10 if self.in_session else self.threshold * 60
        if self.drift_streak_seconds < needed:
            return False
        if time.time() - self.last_alert_at < self.cooldown * 60:
            return False
        self.last_alert_at = time.time()
        self.drift_streak_seconds = 0
        return True
