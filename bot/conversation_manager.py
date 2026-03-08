from __future__ import annotations

from typing import Iterable, List

from bot.chat_models import ChatMessage


class ConversationManager:
    """维护结构化对话上下文，负责去重和新消息检测。"""

    def __init__(self, max_messages: int = 80):
        self.max_messages = max_messages
        self._messages: List[ChatMessage] = []
        self._seen_ids: set[str] = set()

    def update_messages(self, messages: Iterable[ChatMessage]) -> List[ChatMessage]:
        new_messages: List[ChatMessage] = []
        for msg in sorted(list(messages), key=lambda x: (x.bbox[1], x.bbox[0])):
            if not msg.msg_id or msg.msg_id in self._seen_ids:
                continue
            self._seen_ids.add(msg.msg_id)
            self._messages.append(msg)
            new_messages.append(msg)

        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages :]

        return new_messages

    def get_new_other_messages(self, messages: Iterable[ChatMessage]) -> List[ChatMessage]:
        new_messages = self.update_messages(messages)
        return [m for m in new_messages if m.sender_role == "other" and m.text.strip()]

    def get_recent_messages(self, limit: int = 12) -> List[ChatMessage]:
        if limit <= 0:
            return []
        return list(self._messages[-limit:])

    def format_context(self, limit: int = 12) -> str:
        role_map = {"me": "我", "other": "对方", "system": "系统"}
        lines = []
        for m in self.get_recent_messages(limit=limit):
            role = role_map.get(m.sender_role, m.sender_role)
            ts = m.raw_timestamp or m.timestamp
            if ts:
                lines.append(f"{role}({ts})：{m.text}")
            else:
                lines.append(f"{role}：{m.text}")
        return "\n".join(lines)
