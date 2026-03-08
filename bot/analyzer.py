from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Dict, Optional

from bot.intent_model import IntentClassifier


INTENT_TO_MEMORY_TYPE = {
    "greeting": "greeting",
    "question": "question",
    "task": "task",
    "feedback": "feedback",
    "general": "general",
    "noise": "general",
    "system": "general",
    "self_echo": "general",
}

PRIORITY_BY_INTENT = {
    "greeting": 1,
    "feedback": 1,
    "general": 1,
    "question": 2,
    "task": 4,
    "noise": 0,
    "system": 0,
    "self_echo": 0,
}


@dataclass
class MessageAnalysis:
    intent: str
    entities: Dict[str, Any]
    sentiment: Optional[str]
    summary: str
    priority: int
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MessageAnalyzer:
    """Message analyzer with switchable `rule` / `ml` modes."""

    def __init__(
        self,
        mode: str = "rule",
        classifier: IntentClassifier | None = None,
        rule_fallback: bool = True,
    ):
        self.mode = (mode or "rule").lower()
        if self.mode not in {"rule", "ml"}:
            self.mode = "rule"

        self.classifier = classifier
        self.rule_fallback = rule_fallback
        self._classifier_error = False

        self.intent_patterns = [
            ("greeting", [r"\b(hi|hello|hey)\b", r"你好|您好|在吗|在不|早上好|晚上好|晚安"]),
            ("feedback", [r"谢谢|感谢|辛苦了|多谢", r"抱歉|对不起|不好意思|sorry|thx"]),
            ("task", [r"待办|任务|todo|安排|跟进|处理|提交", r"帮我|记得|需要你"]),
            ("question", [r"[?？]", r"怎么|为何|为什么|啥|什么|能不能|可不可以|是否"]),
        ]

    def analyze(
        self,
        message: str,
        sender_role: Optional[str] = None,
        is_timestamp: bool = False,
        is_noise: bool = False,
        source: Optional[str] = None,
    ) -> MessageAnalysis:
        text = (message or "").strip()

        early_intent, early_conf = self._pre_classify(text, sender_role, is_timestamp, is_noise, source)
        if early_intent is not None:
            return MessageAnalysis(
                intent=early_intent,
                entities={},
                sentiment="neutral",
                summary=self._summarize(text),
                priority=self._resolve_priority(early_intent, "neutral"),
                confidence=early_conf,
            )

        intent, confidence = self._classify_intent(text)
        entities = self._extract_entities(text)
        sentiment = self._analyze_sentiment(text)
        summary = self._summarize(text)
        priority = self._resolve_priority(intent, sentiment)

        return MessageAnalysis(
            intent=intent,
            entities=entities,
            sentiment=sentiment,
            summary=summary,
            priority=priority,
            confidence=confidence,
        )

    def _pre_classify(
        self,
        text: str,
        sender_role: Optional[str],
        is_timestamp: bool,
        is_noise: bool,
        source: Optional[str],
    ) -> tuple[Optional[str], float]:
        if source in {"internal_reminder", "internal_task", "self_echo", "assistant"}:
            return "self_echo", 0.01

        if sender_role == "me":
            return "self_echo", 0.01

        if sender_role == "system" or is_timestamp:
            return "system", 0.02

        if is_noise or self._looks_like_noise_text(text):
            return "noise", 0.01

        if not text:
            return "noise", 0.0

        return None, 0.0

    def _classify_intent(self, text: str) -> tuple[str, float]:
        if self.mode == "ml":
            label, confidence = self._classify_by_ml(text)
            if label is not None:
                return label, confidence
            if not self.rule_fallback:
                return "general", 0.0

        intent = self._classify_by_rule(text)
        confidence = 0.85 if intent != "general" else 0.6
        return intent, confidence

    def _classify_by_ml(self, text: str) -> tuple[Optional[str], float]:
        if self._classifier_error:
            return None, 0.0

        if self.classifier is None:
            try:
                self.classifier = IntentClassifier.from_default_samples()
            except Exception:
                self._classifier_error = True
                return None, 0.0

        try:
            pred = self.classifier.predict(text)
            return pred.label, pred.confidence
        except Exception:
            self._classifier_error = True
            return None, 0.0

    def _classify_by_rule(self, text: str) -> str:
        for intent, patterns in self.intent_patterns:
            if intent == "task" and not self._is_valid_task_text(text):
                continue
            if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
                return intent
        return "general"

    def _is_valid_task_text(self, text: str) -> bool:
        # 仅出现“提醒”不足以认定 task，需搭配动作或时间信息
        has_reminder = bool(re.search(r"提醒", text))
        has_action = bool(re.search(r"帮我|记得|需要你|安排|跟进|处理|提交|设置", text))
        has_time = bool(re.search(r"明天|后天|今天|今晚|下周|周[一二三四五六日天]|\d{1,2}[:：]\d{2}|\d{1,2}点", text))

        if has_action:
            return True
        if has_reminder and has_time:
            return True
        return False

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        if not text:
            return {}

        entities: Dict[str, Any] = {}

        time_patterns = [
            r"明天|后天|今天|今晚|上午|下午|晚上|周[一二三四五六日天]",
            r"\d{1,2}[:：]\d{2}",
            r"\d{1,2}点(?:半|\d{1,2}分)?",
        ]
        times: list[str] = []
        for pattern in time_patterns:
            times.extend(re.findall(pattern, text))
        if times:
            entities["time"] = sorted(set(times), key=times.index)

        locations = re.findall(r"(?:在|到|去|回)([\u4e00-\u9fa5A-Za-z0-9]{2,16})", text)
        if locations:
            entities["location"] = sorted(set(locations), key=locations.index)

        if re.search(r"[?？]", text):
            entities["question"] = True

        task_keywords = [k for k in ["提醒", "安排", "跟进", "处理", "提交", "会议", "开会"] if k in text]
        if task_keywords:
            entities["task_keywords"] = task_keywords

        return entities

    def _analyze_sentiment(self, text: str) -> str:
        low = text.lower()
        positive = ["谢谢", "感谢", "太好了", "不错", "赞", "开心", "happy"]
        negative = ["抱歉", "对不起", "烦", "生气", "不行", "失败", "糟糕", "angry"]

        pos_score = sum(1 for token in positive if token in low)
        neg_score = sum(1 for token in negative if token in low)

        if pos_score > neg_score:
            return "positive"
        if neg_score > pos_score:
            return "negative"
        return "neutral"

    def _summarize(self, text: str, max_chars: int = 48) -> str:
        if not text:
            return ""
        normalized = re.sub(r"\s+", " ", text).strip()
        return normalized if len(normalized) <= max_chars else normalized[:max_chars] + "..."

    def _resolve_priority(self, intent: str, sentiment: Optional[str]) -> int:
        base = PRIORITY_BY_INTENT.get(intent, 1)
        if sentiment == "negative":
            return min(base + 1, 5)
        return base

    def _looks_like_noise_text(self, text: str) -> bool:
        t = (text or "").strip()
        if not t:
            return True
        if re.fullmatch(r"[;:：，。,.!?？！\-_/\\\s]+", t):
            return True
        if re.fullmatch(r"\d{1,3}", t):
            return True
        if re.fullmatch(r"\d{1,3}[\s;:：]+\d{1,3}([\s;:：]+\d{1,3})?", t):
            return True
        if re.fullmatch(r"\d{1,2}:\d{2}", t):
            return True
        return False

    def to_memory_kwargs(self, analysis: MessageAnalysis) -> Dict[str, Any]:
        return {
            "conversation_type": INTENT_TO_MEMORY_TYPE.get(analysis.intent, "general"),
            "priority": analysis.priority,
            "analysis": analysis.to_dict(),
        }

    def to_reply_context(self, analysis: MessageAnalysis) -> Dict[str, Any]:
        return {
            "intent": analysis.intent,
            "entities": analysis.entities,
            "sentiment": analysis.sentiment,
            "summary": analysis.summary,
            "priority": analysis.priority,
            "confidence": analysis.confidence,
        }
