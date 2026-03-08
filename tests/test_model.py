import importlib.util
import unittest


class TestModelDependency(unittest.TestCase):
    @unittest.skipIf(importlib.util.find_spec("sentence_transformers") is None, "sentence_transformers not installed")
    def test_sentence_transformers_importable(self):
        import sentence_transformers  # noqa: F401


if __name__ == "__main__":
    unittest.main()
