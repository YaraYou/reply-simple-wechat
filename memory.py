from collections import defaultdict, deque
import datetime
from typing import Dict, List, Optional, Union
from enum import Enum


class ConversationType(Enum):
    GREETING = "greeting"
    QUESTION = "question"
    FEEDBACK = "feedback"
    COMPLAINT = "complaint"
    GENERAL = "general"


class ShortTermMemory:
    def __init__(self, max_rounds=3, type_limits=None):
        self.max_rounds = max_rounds
        self.memory: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_rounds))
        self.type_limits = type_limits or {
            ConversationType.GENERAL: 3,
            ConversationType.QUESTION: 5,
            ConversationType.FEEDBACK: 2,
        }

    def _normalize_conversation_type(self, conversation_type: Union[str, ConversationType, None]) -> ConversationType:
        if isinstance(conversation_type, ConversationType):
            return conversation_type
        if isinstance(conversation_type, str):
            try:
                return ConversationType(conversation_type.lower())
            except ValueError:
                return ConversationType.GENERAL
        return ConversationType.GENERAL

    def add_round(
        self,
        sender: str,
        user_msg: str,
        assistant_msg: str,
        priority: int = 1,
        conversation_type: Union[str, ConversationType] = ConversationType.GENERAL,
    ):
        conversation_key = self._normalize_conversation_type(conversation_type)
        max_rounds_for_type = self.type_limits.get(conversation_key, self.max_rounds)
        self.memory[sender].append(
            {
                "user": user_msg,
                "assistant": assistant_msg,
                "time": datetime.datetime.now(),
                "priority": priority,
                "type": conversation_key.value,
            }
        )

        if len(self.memory[sender]) > max_rounds_for_type:
            self.memory[sender].popleft()

    def get_recent_rounds(
        self,
        sender: str,
        conversation_type: Optional[Union[str, ConversationType]] = None,
    ) -> List[dict]:
        rounds = list(self.memory[sender])
        if conversation_type is not None:
            expected_type = self._normalize_conversation_type(conversation_type).value
            rounds = [r for r in rounds if r["type"] == expected_type]

        # Higher priority first, then newer messages first.
        rounds.sort(key=lambda x: (x["priority"], x["time"]), reverse=True)
        return rounds

    def format_for_prompt(
        self,
        sender: str,
        conversation_type: Optional[Union[str, ConversationType]] = None,
    ) -> str:
        rounds = self.get_recent_rounds(sender, conversation_type)
        lines = []
        for r in rounds:
            lines.append(f"对方：{r['user']} (优先级: {r['priority']})")
            lines.append(f"我：{r['assistant']} (优先级: {r['priority']})")
        return "\n".join(lines)


short_memory = ShortTermMemory()
