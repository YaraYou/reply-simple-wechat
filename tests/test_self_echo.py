import unittest

from bot.chat_models import ChatMessage
from bot.conversation_manager import ConversationManager
from bot.wechat_client import WeChatClient


class TestSelfEcho(unittest.TestCase):
    def test_recently_sent_is_ignored(self):
        client = WeChatClient()
        client.register_recently_sent("收到，我先记下这个任务。", source="assistant")

        mgr = ConversationManager(confirm_rounds=1)
        mgr.set_recently_sent_matcher(client.match_recently_sent)

        msg = ChatMessage(
            msg_id="m1",
            sender_role="other",
            text="收到，我先记下这个任务。",
            confidence=0.9,
        )
        result = mgr.get_new_other_messages([msg])
        self.assertEqual(0, len(result))

    def test_internal_reminder_in_sent_cache_is_ignored(self):
        client = WeChatClient()
        client.register_recently_sent("提醒：你还记得我叫你干嘛吗", source="internal_reminder")

        mgr = ConversationManager(confirm_rounds=1)
        mgr.set_recently_sent_matcher(client.match_recently_sent)

        msg = ChatMessage(
            msg_id="m2",
            sender_role="other",
            text="提醒：你还记得我叫你干嘛吗",
            confidence=0.95,
        )
        result = mgr.get_new_other_messages([msg])
        self.assertEqual(0, len(result))


if __name__ == "__main__":
    unittest.main()
