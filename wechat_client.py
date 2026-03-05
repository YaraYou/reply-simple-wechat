import hashlib
import time

import numpy as np
import pyautogui
import pygetwindow as gw
import pyperclip
from PIL import ImageGrab
from loguru import logger

import config


class WeChatClient:
    """微信桌面端自动化客户端：负责收消息、发消息与会话标识。"""

    _ocr_reader = None
    _ocr_init_failed = False

    def __init__(self):
        """初始化坐标参数和消息去重缓存。"""
        self.input_x_ratio = 0.3533
        self.input_y_from_bottom = 95
        self.msg_bbox_offsets = (342, 478, 556, 541)

        self.message_seen_at = {}
        self.message_dedup_window_seconds = 8

    @classmethod
    def _get_ocr_reader(cls):
        """懒加载 OCR Reader，初始化失败时做一次性降级。"""
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
        """清理过期消息哈希，避免去重缓存无限增长。"""
        expire_after = self.message_dedup_window_seconds * 6
        expired = [
            msg_hash
            for msg_hash, ts in self.message_seen_at.items()
            if (now_ts - ts) > expire_after
        ]
        for msg_hash in expired:
            del self.message_seen_at[msg_hash]

    def _get_window(self):
        """定位并激活微信窗口，必要时调整到约定位置与尺寸。"""
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

        target_width = config.settings.wechat_window_width
        target_height = config.settings.wechat_window_height
        target_x = config.settings.wechat_window_x
        target_y = config.settings.wechat_window_y

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
        """获取当前会话键，默认使用窗口标题区分会话。"""
        win = self._get_window()
        if not win:
            return "unknown_chat"

        title = (win.title or "").strip()
        if not title:
            return "unknown_chat"

        return title

    def send_message(self, msg, chat=None):
        """将文本粘贴到输入框并发送。"""
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
        """截图消息区域并 OCR，返回去重后的最新消息文本。"""
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

    def get_new_messages(self):
        """对外统一的拉取新消息接口。"""
        return self.get_latest_message()