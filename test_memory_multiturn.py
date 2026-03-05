import unittest

from memory import ShortTermMemory
from memory_policy import ConversationType


class TestMultiTurnMemoryPolicy(unittest.TestCase):
    def setUp(self):
        self.memory = ShortTermMemory(
            max_rounds=3,
            global_max_rounds=8,
            type_limits={
                ConversationType.GREETING: 2,
                ConversationType.GENERAL: 3,
                ConversationType.QUESTION: 5,
                ConversationType.SCHEDULE: 3,
                ConversationType.TASK: 4,
                ConversationType.FEEDBACK: 2,
            },
        )

    def test_type_limits_are_different(self):
        sender = "u1"

        for i in range(5):
            self.memory.add_round(sender, f"hi{i}", f"ok{i}", conversation_type=ConversationType.GREETING)
        for i in range(7):
            self.memory.add_round(sender, f"q{i}?", f"a{i}", conversation_type=ConversationType.QUESTION)

        greeting_rounds = self.memory.get_recent_rounds(sender, conversation_type=ConversationType.GREETING)
        question_rounds = self.memory.get_recent_rounds(sender, conversation_type=ConversationType.QUESTION)

        self.assertEqual(len(greeting_rounds), 2)
        self.assertEqual(len(question_rounds), 5)

    def test_task_is_harder_to_evict_when_global_cap_reached(self):
        sender = "u2"

        # task 类型优先级更高且 sticky，在全局挤压时不应先被移除
        self.memory.add_round(sender, "帮我明天提醒交报告", "好", conversation_type=ConversationType.TASK)
        self.memory.add_round(sender, "记得下午三点开会", "收到", conversation_type=ConversationType.TASK)

        for i in range(10):
            self.memory.add_round(sender, f"闲聊{i}", "嗯", conversation_type=ConversationType.GENERAL, priority=1)

        task_rounds = self.memory.get_recent_rounds(sender, conversation_type=ConversationType.TASK)
        self.assertGreaterEqual(len(task_rounds), 1)
        self.assertTrue(any("提醒" in r["user"] or "开会" in r["user"] for r in task_rounds))

    def test_format_for_prompt_supports_type_filter(self):
        sender = "u3"
        self.memory.add_round(sender, "你好", "你好呀", conversation_type=ConversationType.GREETING)
        self.memory.add_round(sender, "这个怎么做?", "这样做", conversation_type=ConversationType.QUESTION)

        q_ctx = self.memory.format_for_prompt(sender, types=[ConversationType.QUESTION])
        self.assertIn("这个怎么做", q_ctx)
        self.assertNotIn("你好", q_ctx)


if __name__ == "__main__":
    unittest.main()