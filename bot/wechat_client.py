import hashlib
import time
import re
from typing import Optional

import numpy as np
import pyautogui
import pygetwindow as gw
import pyperclip
from PIL import ImageGrab
from loguru import logger

from app.config import settings


class WeChatClient:
    _ocr_reader = None
    _ocr_init_failed = False

    def __init__(self):
        self.input_x_ratio = 0.3533
        self.input_y_from_bottom = 95
        self.msg_bbox_offsets = (342, 478, 556, 541)
        self.chat_panel_bbox_offsets = (250, 80, 885, 560)

        self.message_seen_at = {}
        self.message_dedup_window_seconds = 8

        self.sent_dedup_window_seconds = 18
        self._recently_sent: list[dict] = []

    @classmethod
    def _get_ocr_reader(cls):
        if cls._ocr_reader is not None:
            return cls._ocr_reader
        if cls._ocr_init_failed:
            return None

        try:
            import easyocr

            cls._ocr_reader = easyocr.Reader(["ch_sim", "en"])
            return cls._ocr_reader
        except Exception as e:
            cls._ocr_init_failed = True
            logger.error(f"OCR reader init failed: {e}")
            return None

    def _cleanup_seen_hashes(self, now_ts: float):
        expire_after = self.message_dedup_window_seconds * 6
        expired = [
            msg_hash
            for msg_hash, ts in self.message_seen_at.items()
            if (now_ts - ts) > expire_after
        ]
        for msg_hash in expired:
            del self.message_seen_at[msg_hash]

    def _cleanup_recently_sent(self, now_ts: Optional[float] = None):
        ts = now_ts if now_ts is not None else time.time()
        self._recently_sent = [it for it in self._recently_sent if (ts - it["ts"]) <= self.sent_dedup_window_seconds]

    @staticmethod
    def _normalize_for_compare(text: str) -> str:
        if not isinstance(text, str):
            return ""
        value = text.strip().lower()
        value = re.sub(r"[\s;:：，。,.!?？！\-_/\\]+", "", value)
        return value

    @staticmethod
    def _similar(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        if a == b:
            return 1.0
        common = sum(1 for ch1, ch2 in zip(a, b) if ch1 == ch2)
        return common / max(len(a), len(b))

    @staticmethod
    def _looks_like_noise_message(text: str) -> bool:
        t = (text or "").strip()
        if not t:
            return True
        if re.fullmatch(r"\d{1,4}([\s;:：]+\d{1,4}){0,2}", t):
            return True
        if re.fullmatch(r"\d{1,2}:\d{2}", t):
            return True
        if len(t) <= 4 and not re.search(r"[\u4e00-\u9fffA-Za-z]", t):
            return True
        return False

    def register_recently_sent(self, text: str, source: str = "assistant"):
        norm = self._normalize_for_compare(text)
        if not norm:
            return
        now_ts = time.time()
        self._cleanup_recently_sent(now_ts)
        self._recently_sent.append({"text": norm, "source": source, "ts": now_ts})

    def match_recently_sent(self, text: str) -> Optional[str]:
        norm = self._normalize_for_compare(text)
        if not norm:
            return None

        now_ts = time.time()
        self._cleanup_recently_sent(now_ts)

        for item in reversed(self._recently_sent):
            ratio = self._similar(norm, item["text"])
            if ratio >= 0.92:
                return item["source"]
        return None

    def is_recently_sent(self, text: str) -> bool:
        return self.match_recently_sent(text) is not None

    def _get_window(self):
        wins = gw.getWindowsWithTitle("微信")
        if not wins:
            logger.error("WeChat window not found")
            return None

        win = wins[0]
        if win.isMinimized:
            win.restore()
        try:
            win.activate()
        except Exception as e:
            logger.warning(f"Window activate failed: {e}")
        time.sleep(0.5)

        target_width = settings.wechat_window_width
        target_height = settings.wechat_window_height
        target_x = settings.wechat_window_x
        target_y = settings.wechat_window_y

        if (
            win.width != target_width
            or win.height != target_height
            or win.left != target_x
            or win.top != target_y
        ):
            try:
                if win.isMaximized:
                    win.restore()
                    time.sleep(0.2)
                win.resizeTo(target_width, target_height)
                win.moveTo(target_x, target_y)
                time.sleep(0.5)
                logger.info(
                    f"Window adjusted: width={win.width}, height={win.height}, pos=({win.left}, {win.top})"
                )
            except Exception as e:
                logger.error(f"Failed to adjust window: {e}")
        else:
            logger.debug("Window already in target position")

        return win

    def get_chat_key(self):
        win = self._get_window()
        if not win:
            return "unknown_chat"

        title = (win.title or "").strip()
        if not title:
            return "unknown_chat"

        return title

    def send_message(self, msg, chat=None, source: str = "assistant"):
        try:
            win = self._get_window()
            if not win:
                return

            input_x = win.left + int(win.width * self.input_x_ratio)
            input_y = win.top + win.height - self.input_y_from_bottom

            pyautogui.doubleClick(input_x, input_y)
            time.sleep(0.3)

            pyautogui.hotkey("ctrl", "a")
            pyautogui.press("backspace")
            time.sleep(0.2)

            pyperclip.copy(msg)
            pyautogui.hotkey("ctrl", "v")
            logger.debug("Paste complete")

            pyautogui.press("enter")
            self.register_recently_sent(msg, source=source)
            logger.info(f"Sent message: {msg[:20]}...")
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"Send failed: {e}")

    def get_latest_message(self):
        win = self._get_window()
        if not win:
            return None

        reader = self._get_ocr_reader()
        if reader is None:
            return None

        # 使用聊天面板底部区域做 OCR，避免固定小框漏掉左侧/短消息。
        panel_left, panel_top, panel_right, panel_bottom = self.chat_panel_bbox_offsets
        panel_bbox = (
            win.left + panel_left,
            win.top + panel_top,
            win.left + panel_right,
            win.top + panel_bottom,
        )

        try:
            panel_img = np.array(ImageGrab.grab(bbox=panel_bbox))
            h, w = panel_img.shape[:2]
            if h <= 0 or w <= 0:
                return None

            # 只取底部 35% 区域，聚焦最新几条消息并降低噪声。
            start_y = max(0, int(h * 0.65))
            latest_region = panel_img[start_y:h, 0:w]

            result = reader.readtext(latest_region, detail=0)
            text = " ".join(result).strip()
            text = " ".join(text.split())
            if not text:
                return None

            now_ts = time.time()
            msg_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            last_seen = self.message_seen_at.get(msg_hash)
            self.message_seen_at[msg_hash] = now_ts
            self._cleanup_seen_hashes(now_ts)

            if last_seen is not None and (now_ts - last_seen) < self.message_dedup_window_seconds:
                return None

            if self.is_recently_sent(text):
                return None

            if self._looks_like_noise_message(text):
                logger.debug(f"Skip noisy latest-message OCR: {text}")
                return None

            logger.info(f"Recognized message: {text}")
            return text
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return None

    def capture_chat_panel(self):
        """截取整个聊天消息区域，用于整段 OCR 解析。"""
        win = self._get_window()
        if not win:
            return None

        left_offset, top_offset, right_offset, bottom_offset = self.chat_panel_bbox_offsets
        bbox = (
            win.left + left_offset,
            win.top + top_offset,
            win.left + right_offset,
            win.top + bottom_offset,
        )

        try:
            screenshot = ImageGrab.grab(bbox=bbox)
            return np.array(screenshot)
        except Exception as e:
            logger.error(f"Capture chat panel failed: {e}")
            return None

    def get_new_messages(self):
        return self.get_latest_message()

