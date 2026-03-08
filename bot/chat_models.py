from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class ChatMessage:
    """聊天窗口解析后的结构化消息。"""

    msg_id: str
    sender_role: str  # me | other | system
    text: str
    timestamp: Optional[str] = None
    raw_timestamp: Optional[str] = None
    bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)
    confidence: float = 0.0


@dataclass
class MemoryItem:
    """从对话中提炼出的可记忆信息。"""

    memory_id: str
    owner: str
    content: str
    memory_type: str
    importance: float
    created_at: str
    expires_at: Optional[str] = None
