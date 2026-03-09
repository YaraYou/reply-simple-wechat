from __future__ import annotations

from typing import Callable, List, Optional

import numpy as np
from loguru import logger

from bot.chat_models import ChatMessage, DetectionResult
from bot.chat_ocr_parser import ChatOCRParser


class ChatMessageBuilder:
    """将 YOLO 检测结果 + OCR 组装为结构化消息流。"""

    ROLE_MAP = {
        "bubble_other": "other",
        "bubble_me": "me",
        "system_tip": "system",
    }

    def __init__(
        self,
        chat_parser: Optional[ChatOCRParser] = None,
        ocr_text_reader: Optional[Callable[[np.ndarray], str]] = None,
    ):
        self.chat_parser = chat_parser or ChatOCRParser()
        self.ocr_text_reader = ocr_text_reader

    def build_messages(self, image: np.ndarray, detections: List[DetectionResult]) -> List[ChatMessage]:
        image_np = self.chat_parser._preprocess_image(image)
        if image_np is None:
            return []

        sorted_detections = sorted(detections, key=lambda d: (d.bbox[1], d.bbox[0]))
        messages: List[ChatMessage] = []
        seen_ids: set[str] = set()

        last_raw_timestamp: Optional[str] = None
        last_parsed_timestamp: Optional[str] = None

        for det in sorted_detections:
            crop = self._crop(image_np, det.bbox)
            if crop is None:
                continue

            text = self.chat_parser._normalize_text(self._read_crop_text(crop))

            if det.label == "timestamp":
                if not text:
                    continue
                raw_ts, parsed_ts = self.chat_parser._extract_timestamp(text)
                ts_text = raw_ts or text
                last_raw_timestamp = ts_text
                last_parsed_timestamp = parsed_ts

                msg_id = self.chat_parser._build_msg_id("system", ts_text, ts_text, det.bbox)
                if msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)

                messages.append(
                    ChatMessage(
                        msg_id=msg_id,
                        sender_role="system",
                        text=ts_text,
                        timestamp=parsed_ts,
                        raw_timestamp=ts_text,
                        bbox=det.bbox,
                        confidence=det.confidence,
                        is_timestamp=True,
                        is_noise=False,
                        source="yolo_ocr",
                    )
                )
                continue

            sender_role = self.ROLE_MAP.get(det.label)
            if sender_role is None:
                continue
            if not text:
                continue

            is_noise = self.chat_parser._is_noise_text(text)
            msg_id = self.chat_parser._build_msg_id(sender_role, text, last_raw_timestamp, det.bbox)
            if msg_id in seen_ids:
                continue
            seen_ids.add(msg_id)

            messages.append(
                ChatMessage(
                    msg_id=msg_id,
                    sender_role=sender_role,
                    text=text,
                    timestamp=last_parsed_timestamp,
                    raw_timestamp=last_raw_timestamp,
                    bbox=det.bbox,
                    confidence=det.confidence,
                    is_timestamp=False,
                    is_noise=is_noise,
                    source="yolo_ocr",
                )
            )

        messages.sort(key=lambda m: (m.bbox[1], m.bbox[0]))
        return messages

    def _read_crop_text(self, crop: np.ndarray) -> str:
        if self.ocr_text_reader is not None:
            try:
                return str(self.ocr_text_reader(crop) or "")
            except Exception as e:
                logger.error(f"Custom OCR text reader failed: {e}")
                return ""

        reader = self.chat_parser._get_reader()
        if reader is None:
            return ""

        try:
            result = reader.readtext(crop, detail=0)
            return " ".join(str(it) for it in result).strip()
        except Exception as e:
            logger.error(f"Crop OCR failed: {e}")
            return ""

    @staticmethod
    def _crop(image: np.ndarray, bbox):
        if image is None:
            return None

        h, w = image.shape[:2]
        x1, y1, x2, y2 = bbox
        x1 = max(0, min(int(x1), w))
        x2 = max(0, min(int(x2), w))
        y1 = max(0, min(int(y1), h))
        y2 = max(0, min(int(y2), h))
        if x2 <= x1 or y2 <= y1:
            return None
        return image[y1:y2, x1:x2]
