from __future__ import annotations

import datetime as dt
import json
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


WEEKDAY_MAP = {
    "周一": 0,
    "周二": 1,
    "周三": 2,
    "周四": 3,
    "周五": 4,
    "周六": 5,
    "周日": 6,
    "周天": 6,
}


@dataclass
class ReminderTask:
    id: str
    sender: str
    summary: str
    due_at: str
    created_at: str
    triggered: bool = False
    source: str = "user_task"
    overdue: bool = False


class ReminderStore:
    """Persistent local reminder storage with due-task polling."""

    def __init__(self, file_path: str = "tasks.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def add_task_from_analysis(
        self,
        sender: str,
        raw_message: str,
        analysis: Dict[str, Any],
        now: Optional[dt.datetime] = None,
    ) -> Optional[ReminderTask]:
        if (analysis or {}).get("intent") != "task":
            return None

        now_dt = now or dt.datetime.now()
        due_at = self._parse_due_datetime(raw_message, analysis.get("entities") or {}, now_dt)
        if due_at is None:
            due_at = now_dt + dt.timedelta(minutes=30)

        summary = (analysis.get("summary") or raw_message or "任务提醒").strip()
        task = ReminderTask(
            id=uuid.uuid4().hex,
            sender=sender,
            summary=summary,
            due_at=due_at.isoformat(timespec="seconds"),
            created_at=now_dt.isoformat(timespec="seconds"),
            triggered=False,
            source="user_task",
            overdue=False,
        )

        items = self._load()
        items.append(asdict(task))
        self._save(items)
        return task

    def pop_due_tasks(
        self,
        now: Optional[dt.datetime] = None,
        allow_overdue: bool = True,
        overdue_before: Optional[dt.datetime] = None,
    ) -> list[ReminderTask]:
        now_dt = now or dt.datetime.now()
        items = self._load()

        due: list[ReminderTask] = []
        changed = False
        for item in items:
            if item.get("triggered"):
                continue
            due_at_str = item.get("due_at")
            if not due_at_str:
                continue
            try:
                due_at = dt.datetime.fromisoformat(due_at_str)
            except ValueError:
                continue

            if due_at > now_dt:
                continue

            is_overdue = overdue_before is not None and due_at < overdue_before
            if is_overdue and not allow_overdue:
                item["overdue"] = True
                item["triggered"] = True
                changed = True
                continue

            item["triggered"] = True
            changed = True
            due.append(ReminderTask(**self._normalize_item(item)))

        if changed:
            self._save(items)
        return due

    def _normalize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(item)
        normalized.setdefault("source", "user_task")
        normalized.setdefault("overdue", False)
        return normalized

    def _load(self) -> list[Dict[str, Any]]:
        try:
            rows = json.loads(self.file_path.read_text(encoding="utf-8"))
            return [self._normalize_item(it) for it in rows]
        except Exception:
            return []

    def _save(self, items: list[Dict[str, Any]]):
        self.file_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    def _parse_due_datetime(self, text: str, entities: Dict[str, Any], now: dt.datetime) -> Optional[dt.datetime]:
        date_base = now.date()

        if "后天" in text:
            date_base = (now + dt.timedelta(days=2)).date()
        elif "明天" in text:
            date_base = (now + dt.timedelta(days=1)).date()
        elif "今天" in text or "今晚" in text:
            date_base = now.date()

        for weekday_key, weekday_idx in WEEKDAY_MAP.items():
            if weekday_key in text:
                delta = (weekday_idx - now.weekday()) % 7
                if delta == 0:
                    delta = 7
                date_base = (now + dt.timedelta(days=delta)).date()
                break

        explicit_time = self._parse_explicit_time(text)
        if explicit_time is not None:
            candidate = dt.datetime.combine(date_base, explicit_time)
            if candidate <= now and "明天" not in text and "后天" not in text and not any(k in text for k in WEEKDAY_MAP):
                candidate = candidate + dt.timedelta(days=1)
            return candidate

        times = entities.get("time") or []
        if times:
            first = str(times[0])
            parsed = self._parse_explicit_time(first)
            if parsed is not None:
                candidate = dt.datetime.combine(date_base, parsed)
                if candidate <= now:
                    candidate = candidate + dt.timedelta(days=1)
                return candidate

            if first in {"今天", "今晚"}:
                return dt.datetime.combine(now.date(), dt.time(21, 0))
            if first == "明天":
                return dt.datetime.combine((now + dt.timedelta(days=1)).date(), dt.time(9, 0))
            if first == "后天":
                return dt.datetime.combine((now + dt.timedelta(days=2)).date(), dt.time(9, 0))

        return None

    def _parse_explicit_time(self, text: str) -> Optional[dt.time]:
        hm = re.search(r"(\d{1,2})[:：](\d{2})", text)
        if hm:
            h = int(hm.group(1))
            m = int(hm.group(2))
            if 0 <= h <= 23 and 0 <= m <= 59:
                return dt.time(h, m)

        cn = re.search(r"(\d{1,2})点(半|(\d{1,2})分)?", text)
        if cn:
            h = int(cn.group(1))
            if not (0 <= h <= 23):
                return None
            if cn.group(2) == "半":
                m = 30
            elif cn.group(3):
                m = int(cn.group(3))
            else:
                m = 0
            if 0 <= m <= 59:
                return dt.time(h, m)

        return None
