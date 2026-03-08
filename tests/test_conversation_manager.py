import unittest

from bot.chat_models import ChatMessage
from bot.conversation_manager import ConversationManager


class TestConversationManager(unittest.TestCase):
    def _msg(self, mid, role, text, y):
        return ChatMessage(msg_id=mid, sender_role=role, text=text, bbox=(10, y, 100, y + 20), confidence=0.9)

    def test_deduplicate_and_new_other(self):
        mgr = ConversationManager(max_messages=10)
        batch1 = [
            self._msg("a", "other", "你好", 10),
            self._msg("b", "me", "在呢", 40),
        ]
        new_other_1 = mgr.get_new_other_messages(batch1)
        self.assertEqual(1, len(new_other_1))
        self.assertEqual("你好", new_other_1[0].text)

        # 第二次重复同样消息，不应再次识别为新消息
        new_other_2 = mgr.get_new_other_messages(batch1)
        self.assertEqual(0, len(new_other_2))

    def test_context_format_order(self):
        mgr = ConversationManager(max_messages=10)
        mgr.update_messages(
            [
                self._msg("a", "other", "第一句", 10),
                self._msg("b", "me", "第二句", 40),
                self._msg("c", "other", "第三句", 70),
            ]
        )
        text = mgr.format_context(limit=2)
        self.assertIn("我：第二句", text)
        self.assertIn("对方：第三句", text)
        self.assertNotIn("第一句", text)


if __name__ == "__main__":
    unittest.main()
