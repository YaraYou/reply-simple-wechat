from __future__ import annotations

from collections import defaultdict, deque
import datetime
from typing import Any, Dict, Iterable, List, Optional, Union

from memory_policy import (
    ConversationType,
    classify_message,
    get_policy,
    normalize_type,
    normalize_types,
)


class ShortTermMemory:
    """Maintain short-term conversation context with type-aware retention policies."""

    def __init__(
        self,
        max_rounds: int = 3,
        type_limits: Optional[Dict[ConversationType, int]] = None,
        global_max_rounds: int = 40,
        prompt_max_rounds: int = 8,
    ):
        self.max_rounds = max_rounds
        self.memory: Dict[str, deque] = defaultdict(deque)
        self.global_max_rounds = global_max_rounds
        self.prompt_max_rounds = prompt_max_rounds
        self.type_limits = type_limits or {
            ConversationType.GREETING: 2,
            ConversationType.GENERAL: 3,
            ConversationType.QUESTION: 5,
            ConversationType.SCHEDULE: 4,
            ConversationType.TASK: 6,
            ConversationType.FEEDBACK: 2,
        }

    def _resolve_type(self, conversation_type: Union[str, ConversationType, None], user_msg: str) -> ConversationType:
        if conversation_type is not None:
            return normalize_type(conversation_type)
        return classify_message(user_msg)

    def _effective_type_limit(self, conversation_key: ConversationType) -> int:
        default_limit = get_policy(conversation_key).limit
        configured_limit = self.type_limits.get(conversation_key)
        if configured_limit is not None:
            return configured_limit
        return default_limit if default_limit > 0 else self.max_rounds

    def _trim_type_limit(self, sender: str, conversation_key: ConversationType):
        sender_rounds = self.memory[sender]
        type_value = conversation_key.value
        limit = self._effective_type_limit(conversation_key)

        while sum(1 for r in sender_rounds if r["type"] == type_value) > limit:
            candidates = [
                (idx, round_item)
                for idx, round_item in enumerate(sender_rounds)
                if round_item["type"] == type_value
            ]
            remove_idx = min(candidates, key=lambda x: (x[1]["priority"], x[1]["time"]))[0]
            del sender_rounds[remove_idx]

    def _trim_global_limit(self, sender: str):
        sender_rounds = self.memory[sender]
        while len(sender_rounds) > self.global_max_rounds:
            non_sticky = [
                (idx, r)
                for idx, r in enumerate(sender_rounds)
                if not get_policy(r["type"]).sticky
            ]
            candidates = non_sticky if non_sticky else list(enumerate(sender_rounds))
            remove_idx = min(candidates, key=lambda x: (x[1]["priority"], x[1]["time"]))[0]
            del sender_rounds[remove_idx]

    def add_round(
        self,
        sender: str,
        user_msg: str,
        assistant_msg: str,
        priority: Optional[int] = None,
        conversation_type: Union[str, ConversationType, None] = None,
        analysis: Optional[Dict[str, Any]] = None,
    ):
        """Backward-compatible API. New argument `analysis` is optional."""
        conversation_key = self._resolve_type(conversation_type, user_msg)
        policy = get_policy(conversation_key)
        effective_priority = policy.default_priority if priority is None else priority

        self.memory[sender].append(
            {
                "user": user_msg,
                "assistant": assistant_msg,
                "time": datetime.datetime.now(),
                "priority": int(effective_priority),
                "type": conversation_key.value,
                "analysis": analysis or {},
            }
        )

        self._trim_type_limit(sender, conversation_key)
        self._trim_global_limit(sender)

    def _filter_rounds(
        self,
        sender: str,
        conversation_type: Optional[Union[str, ConversationType]] = None,
        types: Optional[Iterable[Union[str, ConversationType]]] = None,
    ) -> List[dict]:
        rounds = list(self.memory[sender])
        if types is not None:
            allowed = {t.value for t in normalize_types(types)}
            rounds = [r for r in rounds if r["type"] in allowed]
        elif conversation_type is not None:
            expected = normalize_type(conversation_type).value
            rounds = [r for r in rounds if r["type"] == expected]
        return rounds

    def get_recent_rounds(
        self,
        sender: str,
        conversation_type: Optional[Union[str, ConversationType]] = None,
        types: Optional[Iterable[Union[str, ConversationType]]] = None,
    ) -> List[dict]:
        rounds = self._filter_rounds(sender, conversation_type=conversation_type, types=types)
        rounds.sort(key=lambda x: (x["priority"], x["time"]), reverse=True)
        return rounds

    def format_for_prompt(
        self,
        sender: str,
        conversation_type: Optional[Union[str, ConversationType]] = None,
        types: Optional[Iterable[Union[str, ConversationType]]] = None,
        max_rounds: Optional[int] = None,
    ) -> str:
        rounds = self.get_recent_rounds(sender, conversation_type=conversation_type, types=types)

        if conversation_type is None and types is None:
            rounds = rounds[: (max_rounds or self.prompt_max_rounds)]
        elif max_rounds is not None:
            rounds = rounds[:max_rounds]

        lines = []
        for r in rounds:
            analysis = r.get("analysis") or {}
            summary = analysis.get("summary")
            intent = analysis.get("intent", r["type"])
            user_text = summary if summary else r["user"]
            lines.append(f"对方：{user_text} (类型: {intent}, 优先级: {r['priority']})")
            lines.append(f"我：{r['assistant']} (类型: {r['type']}, 优先级: {r['priority']})")
        return "\n".join(lines)


short_memory = ShortTermMemory()
