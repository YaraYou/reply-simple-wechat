import unittest

from bot.chat_models import ChatMessage
from bot.memory_extractor import MemoryExtractor


class TestMemoryExtractor(unittest.TestCase):
    def test_extract_preference_dislike_plan_commitment(self):
        ext = MemoryExtractor()
        messages = [
            ChatMessage(msg_id="1", sender_role="other", text="我喜欢吃火锅"),
            ChatMessage(msg_id="2", sender_role="other", text="我不吃香菜"),
            ChatMessage(msg_id="3", sender_role="other", text="明天我要去医院复查"),
            ChatMessage(msg_id="4", sender_role="other", text="你上次答应我的事记得"),
        ]

        items = ext.extract_from_messages(messages, owner="小王")
        types = {i.memory_type for i in items}
        self.assertIn("preference", types)
        self.assertIn("dislike", types)
        self.assertIn("plan", types)
        self.assertIn("commitment", types)

    def test_deduplicate_memory_item(self):
        ext = MemoryExtractor()
        msg = [ChatMessage(msg_id="1", sender_role="other", text="我喜欢咖啡")]
        first = ext.extract_from_messages(msg, owner="A")
        second = ext.extract_from_messages(msg, owner="A")

        self.assertGreaterEqual(len(first), 1)
        self.assertEqual(0, len(second))


if __name__ == "__main__":
    unittest.main()
