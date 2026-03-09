from __future__ import annotations

from typing import List, Optional, Tuple

from loguru import logger

from bot.chat_detector import ChatDetector
from bot.chat_message_builder import ChatMessageBuilder
from bot.chat_models import ChatMessage
from bot.chat_ocr_parser import ChatOCRParser


def parse_messages_with_fallback(
    panel_image,
    detector: Optional[ChatDetector],
    builder: ChatMessageBuilder,
    parser: ChatOCRParser,
) -> Tuple[List[ChatMessage], str]:
    if panel_image is None:
        return [], "no_image"

    if detector is not None and detector.enabled:
        detector_available = getattr(detector, "available", True)
        if detector_available:
            detections = detector.detect(panel_image)
            if detections:
                messages = builder.build_messages(panel_image, detections)
                if messages:
                    return messages, "yolo_ocr"
                logger.warning("YOLO 检测已命中，但未提取到有效消息，回退整屏 OCR")
            else:
                logger.debug("YOLO 本轮未检测到目标，回退整屏 OCR")

    return parser.parse_image(panel_image), "ocr_fallback"
