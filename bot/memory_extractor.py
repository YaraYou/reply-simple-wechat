from __future__ import annotations

import datetime as dt
import hashlib
import re
from typing import List

from bot.chat_models import ChatMessage, MemoryItem


class MemoryExtractor:
    """基于规则从消息中提炼值得记住的记忆项。"""

    def __init__(self):
        self._seen_memory_ids: set[str] = set()

    def extract_from_messages(self, messages: List[ChatMessage], owner: str = "other") -> List[MemoryItem]:
        items: List[MemoryItem] = []
        for msg in messages:
            if msg.sender_role != "other":
                continue
            items.extend(self.extract_from_text(msg.text, owner=owner))
        return items

    def extract_from_text(self, text: str, owner: str = "other") -> List[MemoryItem]:
        text = (text or "").strip()
        if not text:
            return []

        candidates = []

        m_like = re.search(r"我喜欢(.+)", text)
        if m_like:
            candidates.append((f"对方喜欢{m_like.group(1).strip()}", "preference", 0.72, None))

        m_dislike = re.search(r"我不吃(.+)|我不喜欢(.+)", text)
        if m_dislike:
            content = next((g.strip() for g in m_dislike.groups() if g), "")
            candidates.append((f"对方不喜欢{content}", "dislike", 0.78, None))

        if re.search(r"明天|后天|下周|周末|今晚", text):
            candidates.append((f"对方提到安排：{text}", "plan", 0.82, self._days_later_iso(14)))

        if re.search(r"记得|你上次答应|答应我|别忘了", text):
            candidates.append((f"对方强调承诺：{text}", "commitment", 0.9, self._days_later_iso(30)))

        if re.search(r"最近|一直在|这几天", text):
            candidates.append((f"近期话题：{text}", "recent_topic", 0.64, self._days_later_iso(21)))

        items: List[MemoryItem] = []
        for content, mem_type, importance, expires_at in candidates:
            memory_id = self._build_memory_id(owner, mem_type, content)
            if memory_id in self._seen_memory_ids:
                continue
            self._seen_memory_ids.add(memory_id)
            items.append(
                MemoryItem(
                    memory_id=memory_id,
                    owner=owner,
                    content=content,
                    memory_type=mem_type,
                    importance=importance,
                    created_at=dt.datetime.now().isoformat(timespec="seconds"),
                    expires_at=expires_at,
                )
            )

        return items

    def _build_memory_id(self, owner: str, mem_type: str, content: str) -> str:
        payload = f"{owner}|{mem_type}|{content}"
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]

    def _days_later_iso(self, days: int) -> str:
        return (dt.datetime.now() + dt.timedelta(days=days)).isoformat(timespec="seconds")
