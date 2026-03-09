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
            is_timestamp = raw_ts is not None
            is_noise = self._is_noise_text(text)
            sender_role = self._classify_sender(block["bbox"], width, text, is_timestamp)
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
                    is_timestamp=is_timestamp,
                    is_noise=is_noise,
                    source="normal",
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

        # 以 y 轴邻近度做行级合并：先粗分行，再在行内按 x 排序拼接文本。
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
        is_timestamp: bool,
    ) -> str:
        x1, _, x2, _ = bbox
        center_x = (x1 + x2) / 2.0
        norm_x = center_x / max(1, panel_width)

        # 微信双栏布局启发式：左侧=对方，右侧=我，中间区域优先判系统行。
        # 阈值设计为“中间留白带”，减少头像/气泡抖动导致的角色误判。
        if is_timestamp and 0.30 <= norm_x <= 0.70:
            return "system"

        if self._looks_like_system_text(text) and 0.30 <= norm_x <= 0.70:
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
        if t in {"以下为新消息", "以上是打招呼的内容", "消息已发出", "撤回了一条消息"}:
            return True
        if re.fullmatch(r"\d{1,2}:\d{2}", t):
            return True
        if re.fullmatch(r"\d{4}[/-]\d{1,2}[/-]\d{1,2}", t):
            return True
        return False

    def _extract_timestamp(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        patterns = [
            r"\d{4}[/-]\d{1,2}[/-]\d{1,2}\s+\d{1,2}:\d{2}",
            r"昨天\s*\d{1,2}:\d{2}",
            r"星期[一二三四五六日天]\s*\d{1,2}:\d{2}",
            r"\b\d{1,2}:\d{2}\b",
            r"\d{4}[/-]\d{1,2}[/-]\d{1,2}",
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

        for fmt in ("%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M", "%Y/%m/%d", "%Y-%m-%d"):
            try:
                parsed = dt.datetime.strptime(raw, fmt)
                if "%H" in fmt:
                    return parsed.isoformat(timespec="minutes")
                return parsed.isoformat(timespec="minutes")
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

    def _is_noise_text(self, text: str) -> bool:
        t = self._normalize_text(text)
        if not t:
            return True

        # 纯标点短碎片
        if re.fullmatch(r"[;:：，。,.!?？！\-_/\\\s]+", t):
            return True

        # 纯数字短文本，如 29 / 20
        if re.fullmatch(r"\d{1,3}", t):
            return True

        # 典型 OCR 时间噪声碎片，如 29 22;56 / 29 29
        if re.fullmatch(r"\d{1,3}[\s;:：]+\d{1,3}([\s;:：]+\d{1,3})?", t):
            return True

        # 过短且不包含中文英文
        if len(t) <= 2 and not re.search(r"[\u4e00-\u9fffA-Za-z]", t):
            return True

        return False

    def _build_msg_id(
        self,
        sender_role: str,
        text: str,
        raw_timestamp: Optional[str],
        bbox: Tuple[int, int, int, int],
    ) -> str:
        norm_text = self.normalize_for_compare(text)
        # 采用粗粒度坐标，降低 OCR 抖动造成的重复误判
        qbbox = tuple(int(v / 10) for v in bbox)
        # msg_id 依赖“角色+归一化文本+粗粒度坐标+原始时间”，
        # 目标是跨帧稳定、对 OCR 轻微偏移不敏感，同时尽量区分同屏不同气泡。
        payload = f"{sender_role}|{norm_text}|{raw_timestamp or ''}|{qbbox[0]}|{qbbox[1]}|{qbbox[2]}|{qbbox[3]}"
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]

    def _normalize_text(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def normalize_for_compare(text: str) -> str:
        if not isinstance(text, str):
            return ""
        value = text.strip().lower()
        value = re.sub(r"[\s;:：，。,.!?？！\-_/\\]+", "", value)
        return value

