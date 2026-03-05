import datetime
import unittest
from unittest.mock import patch

import reply
from memory import ConversationType, ShortTermMemory


class FakeCollection:
    def query(self, query_texts, n_results):
        self.last_query = (query_texts, n_results)
        return {"documents": [["对方：你好\n我：你好呀"]]}


class _Msg:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Msg(content)


class FakeCompletions:
    def create(self, **kwargs):
        self.kwargs = kwargs
        return type("Resp", (), {"choices": [_Choice("回复：收到")]} )


class FakeChat:
    def __init__(self):
        self.completions = FakeCompletions()


class FakeClient:
    def __init__(self):
        self.chat = FakeChat()


class TestShortTermMemory(unittest.TestCase):
    def test_recent_order_newest_first_when_same_priority(self):
        memory = ShortTermMemory(max_rounds=5)
        memory.add_round("u1", "old", "a_old", priority=1, conversation_type=ConversationType.GENERAL)
        memory.add_round("u1", "new", "a_new", priority=1, conversation_type=ConversationType.GENERAL)

        rounds = memory.get_recent_rounds("u1")
        self.assertEqual(rounds[0]["user"], "new")
        self.assertEqual(rounds[1]["user"], "old")

    def test_higher_priority_first(self):
        memory = ShortTermMemory(max_rounds=5)
        memory.add_round("u1", "normal", "a1", priority=1, conversation_type=ConversationType.GENERAL)
        memory.add_round("u1", "important", "a2", priority=3, conversation_type=ConversationType.GENERAL)

        rounds = memory.get_recent_rounds("u1")
        self.assertEqual(rounds[0]["user"], "important")


class TestReply(unittest.TestCase):
    def test_daily_reply(self):
        self.assertEqual(reply.daily_reply("在吗"), "咋了?")
        self.assertEqual(reply.daily_reply("hello"), "hi")

    @patch("reply.get_openai_client", return_value=None)
    @patch("reply.get_collection", return_value=None)
    def test_smart_reply_fallback_when_client_missing(self, _mock_collection, _mock_client):
        text = reply.get_smart_reply("u1", "你好", "")
        self.assertEqual(text, reply.FALLBACK_REPLY)

    def test_smart_reply_with_injected_client_and_collection(self):
        fake_client = FakeClient()
        fake_collection = FakeCollection()
        text = reply.get_smart_reply(
            "u1",
            "你好",
            "对方：早\n我：早",
            llm_client=fake_client,
            vector_collection=fake_collection,
            now=datetime.datetime(2026, 3, 5, 10, 0),
        )
        self.assertEqual(text, "收到")


if __name__ == "__main__":
    unittest.main()
