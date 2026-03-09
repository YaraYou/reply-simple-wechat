from __future__ import annotations

import datetime as dt
import json
import os
import re
import signal
import subprocess
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
LOG_CANDIDATES = [BASE_DIR / "bot.log", BASE_DIR / "app" / "bot.log"]

_RECEIVED_RE = re.compile(r"Received message:\s*(.*?)\.\.\.\s*intent=.*?conf=([0-9.]+)")
_SENT_RE = re.compile(r"Sent message:\s*(.*?)(?:\.\.\.|$)")
_LOG_LINE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?) \|\s*(\w+)\s*\|\s*(.*)$")


class BotController:
    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen[str]] = None
        self._started_at: Optional[dt.datetime] = None
        self._lock = threading.Lock()

    def _is_running_unlocked(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def is_running(self) -> bool:
        with self._lock:
            return self._is_running_unlocked()

    def start(self) -> Dict[str, Any]:
        with self._lock:
            if self._is_running_unlocked():
                return {"accepted": True, "state": "running"}

            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

            process = subprocess.Popen(
                [sys.executable, "-m", "app.main"],
                cwd=str(BASE_DIR),
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                creationflags=creationflags,
            )

            # app.main contains input("Press Enter to start..."); auto-continue it.
            if process.stdin is not None:
                process.stdin.write("\n")
                process.stdin.flush()
                process.stdin.close()

            self._process = process
            self._started_at = dt.datetime.now()
            return {"accepted": True, "state": "running"}

    def stop(self) -> Dict[str, Any]:
        with self._lock:
            if not self._is_running_unlocked():
                self._process = None
                self._started_at = None
                return {"accepted": True, "state": "stopped"}

            assert self._process is not None
            process = self._process

            try:
                if os.name == "nt":
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                    process.wait(timeout=5)
                else:
                    process.terminate()
                    process.wait(timeout=5)
            except Exception:
                process.kill()
                process.wait(timeout=5)

            self._process = None
            self._started_at = None
            return {"accepted": True, "state": "stopped"}

    def uptime_seconds(self) -> int:
        with self._lock:
            if self._started_at is None or not self._is_running_unlocked():
                return 0
            return int((dt.datetime.now() - self._started_at).total_seconds())


controller = BotController()


def _read_log_lines(limit: int = 400) -> List[str]:
    existing = next((p for p in LOG_CANDIDATES if p.exists()), None)
    if existing is None:
        return []

    try:
        with existing.open("r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            return [line.rstrip("\n") for line in lines[-limit:]]
    except OSError:
        return []


def _parse_timestamp(raw: str) -> str:
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(raw, fmt).isoformat()
        except ValueError:
            continue
    return dt.datetime.now().isoformat()


def _get_recent_messages(limit: int = 30) -> List[Dict[str, Any]]:
    lines = _read_log_lines(1200)
    messages: List[Dict[str, Any]] = []

    for i, line in enumerate(lines):
        match = _LOG_LINE_RE.match(line)
        if not match:
            continue

        ts_raw, _level, payload = match.groups()
        ts = _parse_timestamp(ts_raw)

        got = _RECEIVED_RE.search(payload)
        if got:
            text = got.group(1).strip()
            confidence = float(got.group(2)) if got.group(2) else 1.0
            messages.append(
                {
                    "id": f"msg_recv_{i}",
                    "senderRole": "other",
                    "text": text,
                    "timestamp": ts,
                    "source": "yolo_ocr",
                    "confidence": confidence,
                }
            )
            continue

        sent = _SENT_RE.search(payload)
        if sent:
            text = sent.group(1).strip()
            messages.append(
                {
                    "id": f"msg_sent_{i}",
                    "senderRole": "me",
                    "text": text,
                    "timestamp": ts,
                    "source": "manual",
                    "confidence": 1.0,
                }
            )

    return messages[-limit:]


def _get_status() -> Dict[str, Any]:
    recent_messages = _get_recent_messages(limit=1)
    latest_message_at = recent_messages[0]["timestamp"] if recent_messages else dt.datetime.now().isoformat()

    state = "running" if controller.is_running() else "stopped"

    return {
        "state": state,
        "analyzerMode": settings.analyzer_mode,
        "detectorEnabled": bool(settings.use_yolo_detector),
        "latestMessageAt": latest_message_at,
        "queueDepth": 0,
        "uptimeSeconds": controller.uptime_seconds(),
    }


def _get_current_context() -> Dict[str, Any]:
    recent_messages = _get_recent_messages(limit=12)
    reply_candidate = next((m for m in reversed(recent_messages) if m["senderRole"] == "other"), None)
    return {
        "chatKey": "微信",
        "recentMessages": recent_messages,
        "replyCandidate": reply_candidate,
    }


def _get_latest_detections() -> Dict[str, Any]:
    recent_messages = _get_recent_messages(limit=8)
    detections: List[Dict[str, Any]] = []

    for idx, msg in enumerate(recent_messages):
        y = 80 + idx * 54
        detections.append(
            {
                "id": f"det_{idx}",
                "label": "bubble_other" if msg["senderRole"] == "other" else "bubble_me",
                "confidence": msg.get("confidence", 1.0),
                "bbox": [30 if msg["senderRole"] == "other" else 460, y, 430 if msg["senderRole"] == "other" else 920, y + 48],
                "ocrText": msg["text"],
            }
        )

    if not detections:
        detections = [
            {
                "id": "det_fallback",
                "label": "system_tip",
                "confidence": 0.5,
                "bbox": [220, 120, 740, 180],
                "ocrText": "No detection data yet",
            }
        ]

    return {
        "capturedAt": dt.datetime.now().isoformat(),
        "imageUrl": "https://placehold.co/960x540/e8eefc/1f2a44?text=Live+Detection+Placeholder",
        "detections": detections,
    }


def _get_memories() -> List[Dict[str, Any]]:
    reminders_path = Path(settings.reminders_file)
    if not reminders_path.exists():
        return []

    try:
        raw = json.loads(reminders_path.read_text(encoding="utf-8", errors="ignore"))
    except (json.JSONDecodeError, OSError):
        return []

    items: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw[-40:]):
        items.append(
            {
                "id": item.get("id", f"mem_{idx}"),
                "owner": "other",
                "type": "plan",
                "content": item.get("summary", ""),
                "createdAt": item.get("created_at", dt.datetime.now().isoformat()),
                "confidence": 0.8,
            }
        )
    return items


def _get_settings() -> Dict[str, Any]:
    return {
        "analyzerMode": settings.analyzer_mode,
        "useYoloDetector": bool(settings.use_yolo_detector),
        "yoloConfThreshold": float(settings.yolo_conf_threshold),
        "yoloIouThreshold": float(settings.yolo_iou_threshold),
        "replyMaxLength": int(settings.reply_max_length),
    }


def _write_env_updates(updates: Dict[str, str]) -> None:
    existing: Dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                existing[key.strip()] = value.strip()

    existing.update(updates)
    content = "\n".join(f"{k}={v}" for k, v in existing.items()) + "\n"
    ENV_FILE.write_text(content, encoding="utf-8")


def _save_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    settings.analyzer_mode = str(payload.get("analyzerMode", settings.analyzer_mode))
    settings.use_yolo_detector = bool(payload.get("useYoloDetector", settings.use_yolo_detector))
    settings.yolo_conf_threshold = float(payload.get("yoloConfThreshold", settings.yolo_conf_threshold))
    settings.yolo_iou_threshold = float(payload.get("yoloIouThreshold", settings.yolo_iou_threshold))
    settings.reply_max_length = int(payload.get("replyMaxLength", settings.reply_max_length))

    _write_env_updates(
        {
            "ANALYZER_MODE": settings.analyzer_mode,
            "USE_YOLO_DETECTOR": str(settings.use_yolo_detector),
            "YOLO_CONF_THRESHOLD": str(settings.yolo_conf_threshold),
            "YOLO_IOU_THRESHOLD": str(settings.yolo_iou_threshold),
            "REPLY_MAX_LENGTH": str(settings.reply_max_length),
        }
    )

    return _get_settings()


def _get_logs(limit: int = 150, level: Optional[str] = None, keyword: Optional[str] = None) -> List[Dict[str, Any]]:
    lines = _read_log_lines(max(limit * 4, 400))
    records: List[Dict[str, Any]] = []

    for i, line in enumerate(lines):
        match = _LOG_LINE_RE.match(line)
        if not match:
            continue

        ts_raw, lvl, payload = match.groups()
        lvl = lvl.upper()

        if level and lvl != level.upper():
            continue
        if keyword and keyword.lower() not in payload.lower():
            continue

        records.append(
            {
                "id": f"log_{i}",
                "level": lvl if lvl in {"DEBUG", "INFO", "WARNING", "ERROR"} else "INFO",
                "message": payload,
                "timestamp": _parse_timestamp(ts_raw),
            }
        )

    return records[-limit:]


class ControlAPIHandler(BaseHTTPRequestHandler):
    server_version = "ReplySimpleWeChatControlAPI/0.1"

    def _set_headers(self, status: int = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        self._set_headers(status)
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._set_headers(HTTPStatus.NO_CONTENT)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/api/status":
            self._send_json(_get_status())
            return

        if path == "/api/messages/recent":
            limit = int(params.get("limit", [30])[0])
            self._send_json(_get_recent_messages(limit=limit))
            return

        if path == "/api/context/current":
            self._send_json(_get_current_context())
            return

        if path == "/api/detections/latest":
            self._send_json(_get_latest_detections())
            return

        if path == "/api/memories":
            self._send_json(_get_memories())
            return

        if path == "/api/settings":
            self._send_json(_get_settings())
            return

        if path == "/api/logs":
            limit = int(params.get("limit", [150])[0])
            level = params.get("level", [None])[0]
            keyword = params.get("keyword", [None])[0]
            self._send_json(_get_logs(limit=limit, level=level, keyword=keyword))
            return

        self._send_json({"error": f"Unknown GET endpoint: {path}"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON body"}, status=HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/control/start":
            self._send_json(controller.start())
            return

        if path == "/api/control/stop":
            self._send_json(controller.stop())
            return

        if path == "/api/settings":
            self._send_json(_save_settings(payload))
            return

        self._send_json({"error": f"Unknown POST endpoint: {path}"}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), ControlAPIHandler)
    print(f"Control API running on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
