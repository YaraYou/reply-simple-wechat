import datetime as dt
import json
import unittest
from pathlib import Path

from bot.reminders import ReminderStore


class TestReminderStore(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(".tmp_test_reminders")
        self.tmp_dir.mkdir(exist_ok=True)

    def tearDown(self):
        for p in self.tmp_dir.glob("*"):
            try:
                p.unlink()
            except FileNotFoundError:
                pass
        try:
            self.tmp_dir.rmdir()
        except OSError:
            pass

    def test_add_and_pop_due_task(self):
        path = self.tmp_dir / "tasks.json"
        store = ReminderStore(str(path))

        now = dt.datetime(2026, 3, 6, 10, 0, 0)
        analysis = {
            "intent": "task",
            "summary": "明天开会提醒",
            "entities": {"time": ["明天", "10:30"]},
        }
        task = store.add_task_from_analysis("chat_a", "明天10:30提醒我开会", analysis, now=now)
        self.assertIsNotNone(task)

        due_1 = store.pop_due_tasks(now=now)
        self.assertEqual(due_1, [])

        due_time = dt.datetime.fromisoformat(task.due_at)
        due_2 = store.pop_due_tasks(now=due_time + dt.timedelta(seconds=1))
        self.assertEqual(len(due_2), 1)
        self.assertEqual(due_2[0].id, task.id)

        due_3 = store.pop_due_tasks(now=due_time + dt.timedelta(minutes=5))
        self.assertEqual(due_3, [])

    def test_non_task_intent_is_ignored(self):
        path = self.tmp_dir / "tasks.json"
        store = ReminderStore(str(path))
        now = dt.datetime(2026, 3, 6, 10, 0, 0)

        task = store.add_task_from_analysis(
            "chat_a",
            "你好",
            {"intent": "greeting", "summary": "你好", "entities": {}},
            now=now,
        )
        self.assertIsNone(task)

        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data, [])


if __name__ == "__main__":
    unittest.main()
