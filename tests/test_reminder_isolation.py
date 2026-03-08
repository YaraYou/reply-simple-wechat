import datetime as dt
import os
import unittest
from pathlib import Path

from bot.reminders import ReminderStore


class TestReminderIsolation(unittest.TestCase):
    def _make_store_path(self, suffix: str):
        return Path(f"tasks_test_{suffix}.json")

    def test_overdue_not_popped_when_disallowed(self):
        fp = self._make_store_path("overdue")
        try:
            if fp.exists():
                fp.unlink()
            store = ReminderStore(str(fp))

            now = dt.datetime(2026, 3, 8, 12, 0, 0)
            task = store.add_task_from_analysis(
                sender="u1",
                raw_message="明天提醒我开会",
                analysis={"intent": "task", "summary": "开会", "entities": {"time": ["明天"]}},
                now=now - dt.timedelta(days=2),
            )
            self.assertIsNotNone(task)

            popped = store.pop_due_tasks(now=now, allow_overdue=False, overdue_before=now - dt.timedelta(hours=1))
            self.assertEqual(0, len(popped))
        finally:
            if fp.exists():
                fp.unlink()

    def test_due_task_still_pops_normally(self):
        fp = self._make_store_path("normal")
        try:
            if fp.exists():
                fp.unlink()
            store = ReminderStore(str(fp))

            now = dt.datetime(2026, 3, 8, 12, 0, 0)
            task = store.add_task_from_analysis(
                sender="u1",
                raw_message="今天13:00提醒我开会",
                analysis={"intent": "task", "summary": "开会", "entities": {"time": ["13:00"]}},
                now=now,
            )
            self.assertIsNotNone(task)

            popped = store.pop_due_tasks(now=now + dt.timedelta(hours=2), allow_overdue=True)
            self.assertEqual(1, len(popped))
            self.assertEqual("user_task", popped[0].source)
        finally:
            if fp.exists():
                fp.unlink()


if __name__ == "__main__":
    unittest.main()
