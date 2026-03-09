import unittest

from bot.chat_models import ChatMessage
from bot.conversation_manager import ConversationManager


class TestConversationManager(unittest.TestCase):
    def _msg(self, mid, role, text, y, **kwargs):
        return ChatMessage(msg_id=mid, sender_role=role, text=text, bbox=(10, y, 100, y + 20), confidence=0.9, **kwargs)

    def test_stable_twice_confirm(self):
        mgr = ConversationManager(max_messages=10, confirm_rounds=2)
        batch = [self._msg("a1", "other", "你好", 10)]

        r1 = mgr.get_new_other_messages(batch)
        self.assertEqual(0, len(r1))

        # 第二次出现相同文本（msg_id 可变化）才确认
        batch2 = [self._msg("a2", "other", "你好", 10)]
        r2 = mgr.get_new_other_messages(batch2)
        self.assertEqual(1, len(r2))
        self.assertEqual("你好", r2[0].text)

    def test_only_other_non_noise_non_system_can_pass(self):
        mgr = ConversationManager(max_messages=10, confirm_rounds=1)
        rows = [
            self._msg("m1", "me", "我发的", 10),
            self._msg("s1", "system", "22:56", 20, is_timestamp=True),
            self._msg("n1", "other", "29 22;56", 30, is_noise=True),
            self._msg("o1", "other", "你在吗", 40),
        ]
        result = mgr.get_new_other_messages(rows)
        self.assertEqual(1, len(result))
        self.assertEqual("你在吗", result[0].text)

    def test_processed_msg_ids_dedup(self):
        mgr = ConversationManager(max_messages=10, confirm_rounds=1)
        msg = self._msg("x1", "other", "测试", 10)
        r1 = mgr.get_new_other_messages([msg])
        self.assertEqual(1, len(r1))
        # 第二次同内容会被 processed_signatures 拦截
        r2 = mgr.get_new_other_messages([self._msg("x2", "other", "测试", 10)])
        self.assertEqual(0, len(r2))

    def test_context_format_order(self):
        mgr = ConversationManager(max_messages=10, confirm_rounds=1)
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

    def test_tail_candidate_me_should_not_reply(self):
        mgr = ConversationManager(max_messages=10, confirm_rounds=1)
        rows = [
            self._msg("o1", "other", "旧的对方消息", 10),
            self._msg("m1", "me", "我刚回复了", 30),
        ]
        candidate = mgr.get_reply_candidate_from_tail(rows)
        self.assertIsNone(candidate)

    def test_tail_candidate_other_should_reply(self):
        mgr = ConversationManager(max_messages=10, confirm_rounds=1)
        rows = [
            self._msg("m1", "me", "好的", 10),
            self._msg("o1", "other", "你晚上有空吗", 30),
        ]
        candidate = mgr.get_reply_candidate_from_tail(rows)
        self.assertIsNotNone(candidate)
        self.assertEqual("other", candidate.sender_role)
        self.assertEqual("你晚上有空吗", candidate.text)

    def test_tail_candidate_timestamp_should_not_reply_old_other(self):
        mgr = ConversationManager(max_messages=10, confirm_rounds=1)
        rows = [
            self._msg("o1", "other", "旧消息", 10),
            self._msg("t1", "system", "21:35", 30, is_timestamp=True),
        ]
        candidate = mgr.get_reply_candidate_from_tail(rows)
        self.assertIsNone(candidate)


if __name__ == "__main__":
    unittest.main()
