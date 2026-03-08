from __future__ import annotations

import datetime as dt
import hashlib
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image
from loguru import logger

from bot.chat_models import ChatMessage


class ChatOCRParser:
    """整段聊天窗口 OCR 解析器：将碎片文本合并为结构化消息。"""

    def __init__(self, y_merge_threshold: int = 22):
        self.y_merge_threshold = y_merge_threshold
        self._ocr_reader = None
        self._ocr_init_failed = False

    def parse_image(self, image: Any) -> List[ChatMessage]:
        image_np = self._preprocess_image(image)
        if image_np is None:
            return []

        ocr_result = self._run_ocr(image_np)
        if not ocr_result:
            return []

        merged_blocks = self._merge_ocr_boxes(ocr_result)
        messages: List[ChatMessage] = []
        width = image_np.shape[1]

        for block in merged_blocks:
            text = self._normalize_text(block.get("text", ""))
            if not text:
                continue

            raw_ts, parsed_ts = self._extract_timestamp(text)
            sender_role = self._classify_sender(block["bbox"], width, text, raw_ts)
            msg_id = self._build_msg_id(sender_role, text, raw_ts, block["bbox"])

            messages.append(
                ChatMessage(
                    msg_id=msg_id,
                    sender_role=sender_role,
                    text=text,
                    timestamp=parsed_ts,
                    raw_timestamp=raw_ts,
                    bbox=block["bbox"],
                    confidence=float(block.get("confidence", 0.0)),
                )
            )

        messages.sort(key=lambda m: (m.bbox[1], m.bbox[0]))
        return messages

    def _preprocess_image(self, image: Any) -> Optional[np.ndarray]:
        if image is None:
            return None

        if isinstance(image, np.ndarray):
            return image

        if isinstance(image, Image.Image):
            return np.array(image)

        logger.warning(f"Unsupported image type for OCR parse: {type(image)}")
        return None

    def _get_reader(self):
        if self._ocr_reader is not None:
            return self._ocr_reader
        if self._ocr_init_failed:
            return None

        try:
            import easyocr

            self._ocr_reader = easyocr.Reader(["ch_sim", "en"])
            return self._ocr_reader
        except Exception as e:
            self._ocr_init_failed = True
            logger.error(f"ChatOCRParser init reader failed: {e}")
            return None

    def _run_ocr(self, image_np: np.ndarray):
        reader = self._get_reader()
        if reader is None:
            return []

        try:
            return reader.readtext(image_np, detail=1)
        except Exception as e:
            logger.error(f"ChatOCRParser OCR failed: {e}")
            return []

    def _merge_ocr_boxes(self, ocr_result: Sequence) -> List[Dict[str, Any]]:
        fragments: List[Dict[str, Any]] = []
        for item in ocr_result:
            if not item or len(item) < 3:
                continue
            points, text, conf = item[0], str(item[1]), item[2]
            xs = [int(p[0]) for p in points]
            ys = [int(p[1]) for p in points]
            x1, x2 = min(xs), max(xs)
            y1, y2 = min(ys), max(ys)
            fragments.append(
                {
                    "text": text,
                    "confidence": float(conf or 0.0),
                    "bbox": (x1, y1, x2, y2),
                    "center_y": (y1 + y2) // 2,
                }
            )

        fragments.sort(key=lambda x: (x["center_y"], x["bbox"][0]))
        if not fragments:
            return []

        groups: List[List[Dict[str, Any]]] = []
        for frag in fragments:
            if not groups:
                groups.append([frag])
                continue

            last_group = groups[-1]
            last_y = sum(it["center_y"] for it in last_group) / max(1, len(last_group))
            if abs(frag["center_y"] - last_y) <= self.y_merge_threshold:
                last_group.append(frag)
            else:
                groups.append([frag])

        merged: List[Dict[str, Any]] = []
        for group in groups:
            group.sort(key=lambda x: x["bbox"][0])
            text = " ".join(self._normalize_text(it["text"]) for it in group if self._normalize_text(it["text"]))
            if not text:
                continue
            x1 = min(it["bbox"][0] for it in group)
            y1 = min(it["bbox"][1] for it in group)
            x2 = max(it["bbox"][2] for it in group)
            y2 = max(it["bbox"][3] for it in group)
            conf = sum(it["confidence"] for it in group) / max(1, len(group))
            merged.append(
                {
                    "text": text,
                    "confidence": conf,
                    "bbox": (x1, y1, x2, y2),
                }
            )

        return merged

    def _classify_sender(
        self,
        bbox: Tuple[int, int, int, int],
        panel_width: int,
        text: str,
        raw_timestamp: Optional[str],
    ) -> str:
        x1, _, x2, _ = bbox
        center_x = (x1 + x2) / 2.0
        norm_x = center_x / max(1, panel_width)

        if raw_timestamp and 0.35 <= norm_x <= 0.65:
            return "system"

        if self._looks_like_system_text(text) and 0.3 <= norm_x <= 0.7:
            return "system"

        if norm_x <= 0.45:
            return "other"
        if norm_x >= 0.55:
            return "me"
        return "system"

    def _looks_like_system_text(self, text: str) -> bool:
        t = text.strip()
        if not t:
            return False
        if t in {"以下为新消息", "以上是打招呼的内容", "消息已发出"}:
            return True
        return bool(re.fullmatch(r"\d{1,2}:\d{2}", t))

    def _extract_timestamp(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        patterns = [
            r"\d{4}[/-]\d{1,2}[/-]\d{1,2}\s+\d{1,2}:\d{2}",
            r"\u6628\u5929\s*\d{1,2}:\d{2}",
            r"\u661f\u671f[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u65e5\u5929]\s*\d{1,2}:\d{2}",
            r"\b\d{1,2}:\d{2}\b",
        ]
        for p in patterns:
            m = re.search(p, text)
            if not m:
                continue
            raw = m.group(0)
            return raw, self._try_parse_timestamp(raw)

        return None, None

    def _try_parse_timestamp(self, raw: str) -> Optional[str]:
        raw = raw.strip()
        now = dt.datetime.now()

        for fmt in ("%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M"):
            try:
                return dt.datetime.strptime(raw, fmt).isoformat(timespec="minutes")
            except ValueError:
                continue

        m_time = re.fullmatch(r"(\d{1,2}):(\d{2})", raw)
        if m_time:
            h, m = int(m_time.group(1)), int(m_time.group(2))
            if 0 <= h <= 23 and 0 <= m <= 59:
                return now.replace(hour=h, minute=m, second=0, microsecond=0).isoformat(timespec="minutes")

        m_yesterday = re.fullmatch(r"昨天\s*(\d{1,2}):(\d{2})", raw)
        if m_yesterday:
            h, m = int(m_yesterday.group(1)), int(m_yesterday.group(2))
            base = now - dt.timedelta(days=1)
            return base.replace(hour=h, minute=m, second=0, microsecond=0).isoformat(timespec="minutes")

        m_weekday = re.fullmatch(r"星期([一二三四五六日天])\s*(\d{1,2}):(\d{2})", raw)
        if m_weekday:
            weekday_map = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
            target = weekday_map[m_weekday.group(1)]
            h, m = int(m_weekday.group(2)), int(m_weekday.group(3))
            delta = (now.weekday() - target) % 7
            base = now - dt.timedelta(days=delta)
            return base.replace(hour=h, minute=m, second=0, microsecond=0).isoformat(timespec="minutes")

        return None

    def _build_msg_id(
        self,
        sender_role: str,
        text: str,
        raw_timestamp: Optional[str],
        bbox: Tuple[int, int, int, int],
    ) -> str:
        payload = f"{sender_role}|{text}|{raw_timestamp or ''}|{bbox[0]}|{bbox[1]}|{bbox[2]}|{bbox[3]}"
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]

    def _normalize_text(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = re.sub(r"\s+", " ", text)
        return text.strip()
