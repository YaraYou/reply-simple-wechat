import unittest

import numpy as np

from bot.chat_models import ChatMessage
from bot.chat_pipeline import parse_messages_with_fallback


class _DetectorNoResult:
    enabled = True

    @property
    def available(self):
        return True

    def detect(self, _image):
        return []


class _DetectorUnavailable:
    enabled = True

    @property
    def available(self):
        return False

    def detect(self, _image):
        return []


class _Builder:
    def build_messages(self, _panel, _detections):
        return []


class _Parser:
    def __init__(self, output):
        self.output = output

    def parse_image(self, _panel):
        return self.output


class TestYoloFallback(unittest.TestCase):
    def test_fallback_when_yolo_unavailable(self):
        panel = np.zeros((120, 300, 3), dtype=np.uint8)
        parser_output = [
            ChatMessage(msg_id="1", sender_role="other", text="fallback message", confidence=0.9),
        ]
        messages, source = parse_messages_with_fallback(
            panel,
            _DetectorUnavailable(),
            _Builder(),
            _Parser(parser_output),
        )

        self.assertEqual("ocr_fallback", source)
        self.assertEqual(1, len(messages))
        self.assertEqual("fallback message", messages[0].text)

    def test_fallback_when_no_detection(self):
        panel = np.zeros((120, 300, 3), dtype=np.uint8)
        parser_output = [
            ChatMessage(msg_id="2", sender_role="other", text="fallback message 2", confidence=0.9),
        ]
        messages, source = parse_messages_with_fallback(
            panel,
            _DetectorNoResult(),
            _Builder(),
            _Parser(parser_output),
        )

        self.assertEqual("ocr_fallback", source)
        self.assertEqual(1, len(messages))

    def test_no_image_should_return_empty(self):
        messages, source = parse_messages_with_fallback(
            None,
            _DetectorNoResult(),
            _Builder(),
            _Parser([]),
        )
        self.assertEqual("no_image", source)
        self.assertEqual([], messages)


if __name__ == "__main__":
    unittest.main()
