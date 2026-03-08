from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


DEFAULT_TRAINING_SAMPLES: list[tuple[str, str]] = [
    ("你好", "greeting"),
    ("在吗", "greeting"),
    ("hi", "greeting"),
    ("hello", "greeting"),
    ("这个怎么做", "question"),
    ("为什么会这样", "question"),
    ("可以帮我解释下吗", "question"),
    ("你知道原因吗", "question"),
    ("明天提醒我交报告", "task"),
    ("帮我记录待办", "task"),
    ("记得下午三点开会", "task"),
    ("帮我安排一下", "task"),
    ("谢谢你", "feedback"),
    ("辛苦了", "feedback"),
    ("抱歉刚刚语气不好", "feedback"),
    ("感谢你的帮助", "feedback"),
    ("明天晚上有空吗", "schedule"),
    ("周五几点见", "schedule"),
    ("我们约个时间", "schedule"),
    ("今晚能聊吗", "schedule"),
    ("最近怎么样", "general"),
    ("我刚到家", "general"),
    ("今天有点累", "general"),
    ("聊聊天", "general"),
]


@dataclass
class IntentPrediction:
    label: str
    confidence: float


class IntentClassifier:
    """Sentence-transformers embedding + Logistic Regression intent classifier."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", random_state: int = 42):
        self.model_name = model_name
        self.random_state = random_state
        self._embedder = None
        self._label_encoder = None
        self._model = None
        self._trained = False

    def _ensure_runtime(self):
        if self._embedder is not None and self._model is not None and self._label_encoder is not None:
            return

        from sentence_transformers import SentenceTransformer
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import LabelEncoder

        self._embedder = SentenceTransformer(self.model_name)
        self._label_encoder = LabelEncoder()
        self._model = LogisticRegression(max_iter=1200, random_state=self.random_state)

    def train(self, samples: Sequence[Tuple[str, str]]):
        if not samples:
            raise ValueError("training samples cannot be empty")

        self._ensure_runtime()
        texts = [t for t, _ in samples]
        labels = [l for _, l in samples]

        y = self._label_encoder.fit_transform(labels)
        x = self._embedder.encode(texts, convert_to_numpy=True)
        self._model.fit(x, y)
        self._trained = True

    def predict(self, text: str) -> IntentPrediction:
        if not self._trained:
            raise RuntimeError("classifier is not trained")

        x = self._embedder.encode([text], convert_to_numpy=True)
        prob = self._model.predict_proba(x)[0]
        idx = int(prob.argmax())
        label = self._label_encoder.inverse_transform([idx])[0]
        return IntentPrediction(label=label, confidence=float(prob[idx]))

    @classmethod
    def from_default_samples(
        cls,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        samples: Iterable[Tuple[str, str]] | None = None,
    ) -> "IntentClassifier":
        classifier = cls(model_name=model_name)
        classifier.train(list(samples) if samples is not None else DEFAULT_TRAINING_SAMPLES)
        return classifier
