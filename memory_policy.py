from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, Union


class ConversationType(Enum):
    GREETING = "greeting"
    GENERAL = "general"
    QUESTION = "question"
    SCHEDULE = "schedule"
    TASK = "task"
    FEEDBACK = "feedback"


@dataclass(frozen=True)
class MemoryPolicy:
    limit: int
    default_priority: int
    sticky: bool = False


DEFAULT_POLICIES: Dict[ConversationType, MemoryPolicy] = {
    ConversationType.GREETING: MemoryPolicy(limit=2, default_priority=1),
    ConversationType.GENERAL: MemoryPolicy(limit=3, default_priority=1),
    ConversationType.QUESTION: MemoryPolicy(limit=5, default_priority=2),
    ConversationType.SCHEDULE: MemoryPolicy(limit=4, default_priority=3, sticky=True),
    ConversationType.TASK: MemoryPolicy(limit=6, default_priority=4, sticky=True),
    ConversationType.FEEDBACK: MemoryPolicy(limit=2, default_priority=1),
}


def normalize_type(value: Union[str, ConversationType, None]) -> ConversationType:
    if isinstance(value, ConversationType):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        for t in ConversationType:
            if t.value == v:
                return t
    return ConversationType.GENERAL


def normalize_types(values: Iterable[Union[str, ConversationType]]) -> set[ConversationType]:
    return {normalize_type(v) for v in values}


def get_policy(conversation_type: Union[str, ConversationType]) -> MemoryPolicy:
    return DEFAULT_POLICIES.get(normalize_type(conversation_type), DEFAULT_POLICIES[ConversationType.GENERAL])


def classify_message(msg: str) -> ConversationType:
    text = (msg or "").strip().lower()
    if not text:
        return ConversationType.GENERAL

    greeting_keywords = ["你好", "您好", "在吗", "在不", "hi", "hello", "hey", "早", "晚安"]
    feedback_keywords = ["谢谢", "感谢", "辛苦", "抱歉", "对不起", "不好意思", "thx", "sorry"]
    task_keywords = [
        "待办", "todo", "任务", "记得", "提醒", "帮我", "需要你", "跟进", "处理", "安排",
    ]
    schedule_keywords = [
        "明天", "后天", "今晚", "周一", "周二", "周三", "周四", "周五", "周六", "周日", "几点", "时间", "会议", "约",
    ]

    if any(k in text for k in feedback_keywords):
        return ConversationType.FEEDBACK
    if any(k in text for k in task_keywords):
        return ConversationType.TASK
    if any(k in text for k in schedule_keywords):
        return ConversationType.SCHEDULE
    if "?" in text or "？" in text or any(k in text for k in ["怎么", "为何", "为什么", "吗", "呢", "啥", "什么"]):
        return ConversationType.QUESTION
    if any(k in text for k in greeting_keywords):
        return ConversationType.GREETING
    return ConversationType.GENERAL