import unittest

import numpy as np

from bot.chat_ocr_parser import ChatOCRParser


class MockChatOCRParser(ChatOCRParser):
    def __init__(self, fake_result):
        super().__init__()
        self.fake_result = fake_result

    def _run_ocr(self, image_np):
        return self.fake_result


class TestChatOCRParser(unittest.TestCase):
    def test_merge_classify_and_timestamp(self):
        fake_result = [
            ([[20, 20], [90, 20], [90, 40], [20, 40]], "你好", 0.98),
            ([[100, 20], [170, 20], [170, 40], [100, 40]], "在吗", 0.96),
            ([[560, 70], [740, 70], [740, 95], [560, 95]], "我在开会", 0.92),
            ([[320, 120], [470, 120], [470, 145], [320, 145]], "昨天 21:35", 0.99),
        ]
        parser = MockChatOCRParser(fake_result)
        image = np.zeros((300, 800, 3), dtype=np.uint8)

        messages = parser.parse_image(image)

        self.assertEqual(3, len(messages))
        self.assertEqual("other", messages[0].sender_role)
        self.assertEqual("你好 在吗", messages[0].text)
        self.assertEqual("me", messages[1].sender_role)
        self.assertEqual("system", messages[2].sender_role)
        self.assertEqual("昨天 21:35", messages[2].raw_timestamp)
        self.assertTrue(messages[2].timestamp is not None)
        self.assertTrue(messages[2].is_timestamp)
        self.assertFalse(messages[2].is_noise)

    def test_extract_timestamp_formats(self):
        parser = MockChatOCRParser([])

        raw1, ts1 = parser._extract_timestamp("时间 21:35")
        self.assertEqual("21:35", raw1)
        self.assertIsNotNone(ts1)

        raw2, ts2 = parser._extract_timestamp("开会时间 2026/03/08 14:12")
        self.assertEqual("2026/03/08 14:12", raw2)
        self.assertTrue(ts2.startswith("2026-03-08T14:12"))

    def test_noise_detection(self):
        parser = MockChatOCRParser([])
        self.assertTrue(parser._is_noise_text("29"))
        self.assertTrue(parser._is_noise_text("29 22;56"))
        self.assertTrue(parser._is_noise_text("29 29"))
        self.assertFalse(parser._is_noise_text("明天一起吃饭"))


if __name__ == "__main__":
    unittest.main()
