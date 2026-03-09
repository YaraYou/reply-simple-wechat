import unittest

import numpy as np

from bot.chat_message_builder import ChatMessageBuilder
from bot.chat_models import DetectionResult


class _QueueOCR:
    def __init__(self, texts):
        self.texts = list(texts)

    def __call__(self, _crop):
        if not self.texts:
            return ""
        return self.texts.pop(0)


class TestChatMessageBuilder(unittest.TestCase):
    def test_detection_parsing_roles_and_timestamp(self):
        image = np.zeros((300, 500, 3), dtype=np.uint8)
        detections = [
            DetectionResult(label="timestamp", confidence=0.99, bbox=(180, 20, 320, 45)),
            DetectionResult(label="bubble_other", confidence=0.96, bbox=(20, 60, 240, 120)),
            DetectionResult(label="bubble_me", confidence=0.95, bbox=(260, 140, 480, 200)),
        ]
        builder = ChatMessageBuilder(ocr_text_reader=_QueueOCR(["昨天 21:35", "你在吗", "我在开会"]))

        messages = builder.build_messages(image, detections)

        self.assertEqual(3, len(messages))
        self.assertTrue(messages[0].is_timestamp)
        self.assertEqual("system", messages[0].sender_role)
        self.assertEqual("other", messages[1].sender_role)
        self.assertEqual("me", messages[2].sender_role)
        self.assertEqual("昨天 21:35", messages[1].raw_timestamp)
        self.assertFalse(messages[1].is_timestamp)

    def test_ordering_and_timestamp_binding(self):
        image = np.zeros((350, 500, 3), dtype=np.uint8)
        detections = [
            DetectionResult(label="bubble_me", confidence=0.88, bbox=(280, 160, 480, 220)),
            DetectionResult(label="timestamp", confidence=0.98, bbox=(180, 30, 330, 50)),
            DetectionResult(label="bubble_other", confidence=0.93, bbox=(20, 90, 250, 150)),
        ]
        # build_messages 会按 y 排序，因此 OCR 调用顺序应为：timestamp -> other -> me。
        builder = ChatMessageBuilder(ocr_text_reader=_QueueOCR(["2026/03/09 09:30", "收到", "我先回你"]))

        messages = builder.build_messages(image, detections)

        self.assertEqual(["system", "other", "me"], [m.sender_role for m in messages])
        self.assertEqual("2026/03/09 09:30", messages[1].raw_timestamp)
        self.assertEqual("2026/03/09 09:30", messages[2].raw_timestamp)


if __name__ == "__main__":
    unittest.main()
