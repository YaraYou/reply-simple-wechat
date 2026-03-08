from __future__ import annotations

from typing import Callable, Iterable, List, Optional

from bot.chat_models import ChatMessage
from bot.chat_ocr_parser import ChatOCRParser


class ConversationManager:
    """维护结构化对话上下文，负责去重和新消息检测。"""

    def __init__(self, max_messages: int = 80, min_confidence: float = 0.35, confirm_rounds: int = 2):
        self.max_messages = max_messages
        self.min_confidence = min_confidence
        self.confirm_rounds = max(1, int(confirm_rounds))

        self._messages: List[ChatMessage] = []
        self._seen_ids: set[str] = set()
        self._processed_msg_ids: set[str] = set()
        self._processed_signatures: set[str] = set()
        self._candidate_seen_count: dict[str, int] = {}
        self._recently_sent_matcher: Optional[Callable[[str], Optional[str]]] = None

    def set_recently_sent_matcher(self, matcher: Optional[Callable[[str], Optional[str]]] = None):
        """注入最近发送匹配器，返回 source 或 None。"""
        self._recently_sent_matcher = matcher

    def update_messages(self, messages: Iterable[ChatMessage]) -> List[ChatMessage]:
        new_messages: List[ChatMessage] = []
        for msg in sorted(list(messages), key=lambda x: (x.bbox[1], x.bbox[0])):
            if not msg.msg_id or msg.msg_id in self._seen_ids:
                continue

            # 先标注来源，再纳入缓存
            if msg.sender_role == "me":
                msg.source = msg.source or "self_echo"

            if self._recently_sent_matcher is not None:
                matched_source = self._recently_sent_matcher(msg.text)
                if matched_source:
                    msg.source = matched_source

            self._seen_ids.add(msg.msg_id)
            self._messages.append(msg)
            new_messages.append(msg)

        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages :]

        return new_messages

    def get_new_other_messages(self, messages: Iterable[ChatMessage]) -> List[ChatMessage]:
        scan_messages = sorted(list(messages), key=lambda x: (x.bbox[1], x.bbox[0]))
        self.update_messages(scan_messages)

        confirmed: List[ChatMessage] = []
        for msg in scan_messages:
            # 每次扫描都同步一次 source 标记，避免 OCR 波动导致漏标
            if msg.sender_role == "me":
                msg.source = msg.source or "self_echo"
            if self._recently_sent_matcher is not None:
                matched_source = self._recently_sent_matcher(msg.text)
                if matched_source:
                    msg.source = matched_source

            signature = self._build_signature(msg)
            if not self._passes_hard_filters(msg):
                continue

            seen_count = self._candidate_seen_count.get(signature, 0) + 1
            self._candidate_seen_count[signature] = seen_count

            if seen_count < self.confirm_rounds:
                continue
            if signature in self._processed_signatures:
                continue
            if msg.msg_id and msg.msg_id in self._processed_msg_ids:
                continue

            self._processed_signatures.add(signature)
            if msg.msg_id:
                self._processed_msg_ids.add(msg.msg_id)
            confirmed.append(msg)

        return confirmed

    def _passes_hard_filters(self, msg: ChatMessage) -> bool:
        if msg.sender_role != "other":
            return False
        if msg.is_timestamp:
            return False
        if msg.is_noise:
            return False
        if (msg.source or "") in {"self_echo", "internal_reminder", "internal_task", "assistant"}:
            return False
        if not (msg.text or "").strip():
            return False
        if float(msg.confidence or 0.0) < self.min_confidence:
            return False
        return True

    def _build_signature(self, msg: ChatMessage) -> str:
        norm = ChatOCRParser.normalize_for_compare(msg.text)
        return f"{msg.sender_role}|{norm}|{msg.raw_timestamp or ''}"

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

    @property
    def processed_msg_ids(self) -> set[str]:
        return set(self._processed_msg_ids)

    @staticmethod
    def normalize_for_compare(text: str) -> str:
        return ChatOCRParser.normalize_for_compare(text)
