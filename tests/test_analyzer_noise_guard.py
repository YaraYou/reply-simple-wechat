import unittest

from bot.analyzer import MessageAnalyzer


class TestAnalyzerNoiseGuard(unittest.TestCase):
    def setUp(self):
        self.analyzer = MessageAnalyzer()

    def test_noise_text_not_high_confidence(self):
        for text in ["29 22;56", "29 29", "22:56", "29"]:
            analysis = self.analyzer.analyze(text)
            self.assertIn(analysis.intent, {"noise", "system"})
            self.assertLessEqual(analysis.confidence, 0.1)

    def test_self_echo_source(self):
        analysis = self.analyzer.analyze("收到，我先记下这个任务", sender_role="other", source="internal_reminder")
        self.assertEqual("self_echo", analysis.intent)
        self.assertLessEqual(analysis.confidence, 0.1)


if __name__ == "__main__":
    unittest.main()
