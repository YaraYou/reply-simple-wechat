import ast
from pathlib import Path
import unittest

import reply
from memory import ConversationType, ShortTermMemory


class FakeMetadataOnlyCollection:
    def query(self, query_texts, n_results):
        self.last_query = (query_texts, n_results)
        return {
            "documents": [[]],
            "metadatas": [[{"user": "你好", "assistant": "在呢"}]],
        }


class TestMemoryTypeLimits(unittest.TestCase):
    def test_question_limit_is_effective_above_default_max_rounds(self):
        memory = ShortTermMemory(max_rounds=3)
        for i in range(6):
            memory.add_round(
                "u1",
                f"q{i}",
                f"a{i}",
                priority=1,
                conversation_type=ConversationType.QUESTION,
            )

        question_rounds = memory.get_recent_rounds("u1", ConversationType.QUESTION)
        self.assertEqual(len(question_rounds), 5)
        self.assertEqual(question_rounds[-1]["user"], "q1")


class TestVectorExamplesCompatibility(unittest.TestCase):
    def test_retrieve_examples_reconstructs_from_metadata(self):
        text = reply._retrieve_examples(FakeMetadataOnlyCollection(), "", "你好")
        self.assertIn("对方：你好", text)
        self.assertIn("我：在呢", text)


class TestReviewGuards(unittest.TestCase):
    def test_no_api_key_plaintext_print(self):
        main_text = Path("main.py").read_text(encoding="utf-8")
        self.assertNotIn("API_KEY from env", main_text)

    def test_sender_is_dynamic_chat_key(self):
        main_text = Path("main.py").read_text(encoding="utf-8")
        self.assertIn("sender = client.get_chat_key()", main_text)
        self.assertNotIn("sender = \"current_friend\"", main_text)

    def test_vector_doc_is_dialogue_pair(self):
        main_text = Path("main.py").read_text(encoding="utf-8")
        self.assertIn("dialogue_doc = f\"对方：{user_clean}\\n我：{assistant_clean}\"", main_text)
        self.assertIn("documents=[dialogue_doc]", main_text)

    def test_wechat_client_uses_lazy_ocr_init(self):
        source = Path("wechat_client.py").read_text(encoding="utf-8")
        tree = ast.parse(source.encode("utf-8").decode("utf-8-sig"))

        top_level_imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                top_level_imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_level_imports.append(node.module)

        self.assertNotIn("easyocr", top_level_imports)
        self.assertIn("def _get_ocr_reader", source)


if __name__ == "__main__":
    unittest.main()


