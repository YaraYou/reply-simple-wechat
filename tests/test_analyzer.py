import datetime
import unittest

from bot.analyzer import MessageAnalyzer
from memory import ShortTermMemory
from bot import reply


class _Msg:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Msg(content)


class CapturingCompletions:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return type("Resp", (), {"choices": [_Choice("回复：好的")]})


class CapturingClient:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": CapturingCompletions()})()


class _FakeMLClassifier:
    class _Pred:
        def __init__(self, label: str, confidence: float):
            self.label = label
            self.confidence = confidence

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    def predict(self, text: str):
        if self.should_fail:
            raise RuntimeError("ml failed")
        return self._Pred("question", 0.88)


class TestMessageAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = MessageAnalyzer()

    def test_classify_greeting(self):
        analysis = self.analyzer.analyze("你好呀")
        self.assertEqual(analysis.intent, "greeting")

    def test_classify_question(self):
        analysis = self.analyzer.analyze("今天的天气怎么样？")
        self.assertEqual(analysis.intent, "question")
        self.assertTrue(analysis.entities.get("question"))

    def test_classify_task(self):
        analysis = self.analyzer.analyze("帮我设置一个明天下午3点的会议提醒")
        self.assertEqual(analysis.intent, "task")
        self.assertIn("time", analysis.entities)

    def test_classify_feedback(self):
        analysis = self.analyzer.analyze("谢谢，帮到我了")
        self.assertEqual(analysis.intent, "feedback")

    def test_ml_mode_predicts_with_classifier(self):
        analyzer = MessageAnalyzer(mode="ml", classifier=_FakeMLClassifier(), rule_fallback=True)
        analysis = analyzer.analyze("随便一条消息")
        self.assertEqual(analysis.intent, "question")
        self.assertAlmostEqual(analysis.confidence, 0.88, places=2)

    def test_ml_mode_fallbacks_to_rule_when_classifier_fails(self):
        analyzer = MessageAnalyzer(mode="ml", classifier=_FakeMLClassifier(should_fail=True), rule_fallback=True)
        analysis = analyzer.analyze("你好")
        self.assertEqual(analysis.intent, "greeting")
        self.assertGreaterEqual(analysis.confidence, 0.5)

    def test_memory_accepts_analysis_and_uses_summary(self):
        analysis = self.analyzer.analyze("这个问题有点复杂，能帮我梳理一下步骤吗？")

        memory = ShortTermMemory(max_rounds=5)
        memory.add_round("u1", "原始消息", "回复", analysis=analysis.to_dict(), conversation_type="question", priority=2)

        prompt = memory.format_for_prompt("u1")
        self.assertIn(analysis.summary, prompt)
        self.assertIn("类型: question", prompt)

    def test_reply_prompt_contains_analysis_context(self):
        client = CapturingClient()
        analysis_context = {
            "intent": "question",
            "summary": "询问天气",
            "sentiment": "neutral",
            "entities": {"question": True},
            "confidence": 1.0,
            "priority": 2,
        }

        text = reply.get_smart_reply(
            "u1",
            "今天天气怎么样",
            "",
            llm_client=client,
            vector_collection=None,
            now=datetime.datetime(2026, 3, 6, 10, 0),
            analysis_context=analysis_context,
        )
        self.assertEqual(text, "好的")

        user_msg = client.chat.completions.kwargs["messages"][1]["content"]
        self.assertIn("消息分析结果", user_msg)
        self.assertIn("询问天气", user_msg)

    def test_reply_task_intent_uses_quick_path(self):
        analysis_context = {
            "intent": "task",
            "summary": "明天提醒开会",
            "sentiment": "neutral",
            "entities": {"time": ["明天"]},
            "confidence": 1.0,
            "priority": 4,
        }

        text = reply.get_smart_reply(
            "u1",
            "明天提醒我开会",
            "",
            llm_client=CapturingClient(),
            vector_collection=None,
            now=datetime.datetime(2026, 3, 6, 10, 0),
            analysis_context=analysis_context,
        )
        self.assertIn("收到", text)


if __name__ == "__main__":
    unittest.main()

