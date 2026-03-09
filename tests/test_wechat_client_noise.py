import unittest

from bot.wechat_client import WeChatClient


class TestWeChatClientNoise(unittest.TestCase):
    def test_noise_fragments_filtered(self):
        self.assertTrue(WeChatClient._looks_like_noise_message("415 1358"))
        self.assertTrue(WeChatClient._looks_like_noise_message("22:56"))
        self.assertFalse(WeChatClient._looks_like_noise_message("晚上一起吃饭吗"))


if __name__ == "__main__":
    unittest.main()
