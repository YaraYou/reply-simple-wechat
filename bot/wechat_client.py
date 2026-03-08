import hashlib
import time

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

    def send_message(self, msg, chat=None):
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

        left_offset, top_offset, right_offset, bottom_offset = self.msg_bbox_offsets
        bbox = (
            win.left + left_offset,
            win.top + top_offset,
            win.left + right_offset,
            win.top + bottom_offset,
        )

        try:
            screenshot = ImageGrab.grab(bbox=bbox)
            img_np = np.array(screenshot)
            result = reader.readtext(img_np, detail=0)
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
