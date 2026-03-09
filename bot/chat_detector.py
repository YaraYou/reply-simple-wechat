from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

from loguru import logger

from bot.chat_models import DetectionResult


class ChatDetector:
    """聊天窗口 YOLO 检测器。"""

    SUPPORTED_LABELS = {"bubble_other", "bubble_me", "timestamp", "system_tip"}

    def __init__(
        self,
        model_path: str,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        enabled: bool = True,
    ):
        self.model_path = model_path
        self.conf_threshold = float(conf_threshold)
        self.iou_threshold = float(iou_threshold)
        self.enabled = bool(enabled)

        self._model = None
        self._init_failed = False

    @property
    def available(self) -> bool:
        return self._get_model() is not None

    def detect(self, image: Any) -> List[DetectionResult]:
        if not self.enabled or image is None:
            return []

        model = self._get_model()
        if model is None:
            return []

        try:
            results = model.predict(
                source=image,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                verbose=False,
            )
        except Exception as e:
            logger.error(f"YOLO detect failed: {e}")
            return []

        detections: List[DetectionResult] = []
        for result in results or []:
            names = getattr(result, "names", {}) or {}
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            cls_list = boxes.cls.tolist() if getattr(boxes, "cls", None) is not None else []
            conf_list = boxes.conf.tolist() if getattr(boxes, "conf", None) is not None else []
            xyxy_list = boxes.xyxy.tolist() if getattr(boxes, "xyxy", None) is not None else []

            for cls_id, conf, xyxy in zip(cls_list, conf_list, xyxy_list):
                label = names.get(int(cls_id), str(int(cls_id)))
                if label not in self.SUPPORTED_LABELS:
                    continue

                x1, y1, x2, y2 = [int(round(v)) for v in xyxy]
                if x2 <= x1 or y2 <= y1:
                    continue

                detections.append(
                    DetectionResult(
                        label=label,
                        confidence=float(conf),
                        bbox=(x1, y1, x2, y2),
                    )
                )

        detections.sort(key=lambda d: (d.bbox[1], d.bbox[0]))
        return detections

    def _get_model(self):
        if self._model is not None:
            return self._model
        if self._init_failed:
            return None

        model_path = Path(self.model_path)
        if not model_path.exists():
            logger.warning(f"YOLO model path not found, fallback to OCR parser: {self.model_path}")
            self._init_failed = True
            return None

        try:
            from ultralytics import YOLO

            self._model = YOLO(str(model_path))
            return self._model
        except Exception as e:
            self._init_failed = True
            logger.warning(f"YOLO unavailable, fallback to OCR parser: {e}")
            return None
