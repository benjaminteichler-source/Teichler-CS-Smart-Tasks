"""
tests/test_tasks.py — Test suite for the Smart Task Manager.

Tests cover:
  * Task model construction and validation
  * Custom exceptions
  * Service layer: create, edit, delete, complete, filter
  * Edge cases (empty title, bad date, missing task)
  * The filter_tasks generator

Run with:
    pytest tests/
    # or from the project root:
    python -m pytest tests/ -v
"""

import os
import sys
import unittest

# ── Ensure the project root is on the path so imports resolve ────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Point the app at an in-memory SQLite database for tests
os.environ["FLASK_ENV"] = "testing"

from models.task import InvalidTaskError, Task, TaskNotFoundError
from services.task_service import (
    create_task,
    edit_task,
    filter_tasks,
    get_filtered_tasks,
    get_task_stats,
    complete_task,
    remove_task,
)
from database.db import init_db


# ── Helpers ───────────────────────────────────────────────────────────────────

def _setup_db():
    """Drop and recreate the tasks table so every test starts with a clean slate."""
    import sqlite3
    from config import get_config
    cfg = get_config()
    conn = sqlite3.connect(cfg.DATABASE_PATH)
    conn.execute("DROP TABLE IF EXISTS tasks")
    conn.commit()
    conn.close()
    init_db()


# ── Task Model Tests ──────────────────────────────────────────────────────────

class TestTaskModel(unittest.TestCase):
    """Unit tests for the Task dataclass."""

    def test_defaults(self):
        """Task should have sensible defaults when only title is supplied."""
        task = Task(title="Buy milk")
        self.assertEqual(task.title, "Buy milk")
        self.assertEqual(task.category, "General")
        self.assertEqual(task.priority, "medium")
        self.assertFalse(task.completed)
        self.assertIsNone(task.id)
        self.assertIsNone(task.due_date)

    def test_title_stripped(self):
        """Leading/trailing whitespace should be stripped from the title."""
        task = Task(title="  Buy milk  ")
        self.assertEqual(task.title, "Buy milk")

    def test_priority_lowercased(self):
        """Priority should be normalised to lowercase."""
        task = Task(title="Task", priority="HIGH")
        self.assertEqual(task.priority, "high")

    def test_is_overdue_past_date(self):
        """A task with a past due_date that is not complete should be overdue."""
        task = Task(title="Old task", due_date="2000-01-01")
        self.assertTrue(task.is_overdue)

    def test_is_overdue_completed_ignored(self):
        """A completed task is never overdue."""
        task = Task(title="Done task", due_date="2000-01-01", completed=True)
        self.assertFalse(task.is_overdue)

    def test_is_overdue_no_date(self):
        """A task with no due date is never overdue."""
        task = Task(title="No date")
        self.assertFalse(task.is_overdue)

    def test_priority_badge(self):
        """priority_badge should return the correct CSS class."""
        self.assertEqual(Task(title="t", priority="low").priority_badge, "badge-low")
        self.assertEqual(Task(title="t", priority="medium").priority_badge, "badge-medium")
        self.assertEqual(Task(title="t", priority="high").priority_badge, "badge-high")

    def test_to_dict(self):
        """to_dict should return a plain dictionary with all keys."""
        task = Task(title="Buy milk", id=1)
        d = task.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["title"], "Buy milk")
        self.assertEqual(d["id"], 1)

    def test_from_row(self):
        """from_row should correctly map a tuple to a Task."""
        row = (5, "Test", "Desc", "Work", "high", "2099-12-31", 0, "2024-01-01T00:00:00")
        task = Task.from_row(row)
        self.assertEqual(task.id, 5)
        self.assertEqual(task.title, "Test")
        self.assertEqual(task.category, "Work")
        self.assertFalse(task.completed)


# ── Custom Exception Tests ────────────────────────────────────────────────────

class TestCustomExceptions(unittest.TestCase):
    """Verify custom exceptions are distinct and carry messages."""

    def test_invalid_task_error_is_exception(self):
        with self.assertRaises(Exception):
            raise InvalidTaskError("bad input")

    def test_task_not_found_error_is_exception(self):
        with self.assertRaises(Exception):
            raise TaskNotFoundError("not found")

    def test_exceptions_are_distinct(self):
        self.assertNotEqual(InvalidTaskError, TaskNotFoundError)


# ── Service Layer Tests ───────────────────────────────────────────────────────

class TestTaskService(unittest.TestCase):
    """Integration tests for the service layer (uses in-memory SQLite)."""

    def setUp(self):
        _setup_db()

    # -- create ---------------------------------------------------------------

    def test_create_task_basic(self):
        """Creating a task should return a Task with an id assigned."""
        task = create_task(title="Write tests", description="Very important")
        self.assertIsNotNone(task.id)
        self.assertEqual(task.title, "Write tests")

    def test_create_task_empty_title_raises(self):
        """An empty title should raise InvalidTaskError."""
        with self.assertRaises(InvalidTaskError):
            create_task(title="")

    def test_create_task_whitespace_title_raises(self):
        """A whitespace-only title should raise InvalidTaskError."""
        with self.assertRaises(InvalidTaskError):
            create_task(title="   ")

    def test_create_task_invalid_date_raises(self):
        """A malformed due_date should raise InvalidTaskError."""
        with self.assertRaises(InvalidTaskError):
            create_task(title="Task", due_date="not-a-date")

    def test_create_task_valid_date(self):
        """A valid ISO due date should be accepted."""
        task = create_task(title="Task with date", due_date="2099-12-31")
        self.assertEqual(task.due_date, "2099-12-31")

    def test_create_task_empty_date_accepted(self):
        """An empty string due_date should be stored as None."""
        task = create_task(title="No due date", due_date="")
        self.assertIsNone(task.due_date)

    # -- edit -----------------------------------------------------------------

    def test_edit_task(self):
        """Editing a task should persist new values."""
        task = create_task(title="Original title")
        updated = edit_task(task_id=task.id, title="Updated title", priority="high")
        self.assertEqual(updated.title, "Updated title")
        self.assertEqual(updated.priority, "high")

    def test_edit_nonexistent_task_raises(self):
        """Editing a task that does not exist should raise TaskNotFoundError."""
        with self.assertRaises(TaskNotFoundError):
            edit_task(task_id=99999, title="Ghost task")

    def test_edit_task_empty_title_raises(self):
        """Editing a task with an empty title should raise InvalidTaskError."""
        task = create_task(title="Valid title")
        with self.assertRaises(InvalidTaskError):
            edit_task(task_id=task.id, title="")

    # -- complete -------------------------------------------------------------

    def test_complete_task(self):
        """Toggling completion should flip the completed flag."""
        task = create_task(title="Finish report")
        self.assertFalse(task.completed)
        complete_task(task.id)
        # Re-fetch to verify persistence
        from database.db import fetch_task_by_id
        refreshed = fetch_task_by_id(task.id)
        self.assertTrue(refreshed.completed)

    def test_complete_task_toggle(self):
        """Toggling twice should restore the original state."""
        task = create_task(title="Toggle me")
        complete_task(task.id)
        complete_task(task.id)
        from database.db import fetch_task_by_id
        refreshed = fetch_task_by_id(task.id)
        self.assertFalse(refreshed.completed)

    def test_complete_nonexistent_task_raises(self):
        with self.assertRaises(TaskNotFoundError):
            complete_task(99999)

    # -- delete ---------------------------------------------------------------

    def test_delete_task(self):
        """Deleting a task should remove it from the database."""
        task = create_task(title="Delete me")
        remove_task(task.id)
        from database.db import fetch_task_by_id
        self.assertIsNone(fetch_task_by_id(task.id))

    def test_delete_nonexistent_task_raises(self):
        with self.assertRaises(TaskNotFoundError):
            remove_task(99999)

    # -- stats ----------------------------------------------------------------

    def test_stats(self):
        """Stats dict should contain the expected keys."""
        stats = get_task_stats()
        self.assertIn("total", stats)
        self.assertIn("completed", stats)
        self.assertIn("pending", stats)
        self.assertIn("overdue", stats)

    def test_stats_counts(self):
        """Stats should accurately reflect created/completed tasks."""
        t1 = create_task(title="Stats task 1")
        t2 = create_task(title="Stats task 2")
        complete_task(t1.id)
        stats = get_task_stats()
        self.assertGreaterEqual(stats["total"], 2)
        self.assertGreaterEqual(stats["completed"], 1)


# ── Filter Generator Tests ────────────────────────────────────────────────────

class TestFilterGenerator(unittest.TestCase):
    """Tests for the filter_tasks generator function."""

    def _make_tasks(self):
        return [
            Task(title="Work report", category="Work", priority="high"),
            Task(title="Buy groceries", category="Personal", priority="low"),
            Task(title="Study Python", category="School", priority="medium"),
            Task(title="Budget review", category="Work", priority="medium"),
        ]

    def test_filter_by_category(self):
        tasks = self._make_tasks()
        result = list(filter_tasks(tasks, category="Work"))
        self.assertEqual(len(result), 2)
        self.assertTrue(all(t.category == "Work" for t in result))

    def test_filter_by_priority(self):
        tasks = self._make_tasks()
        result = list(filter_tasks(tasks, priority="high"))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Work report")

    def test_filter_by_keyword(self):
        tasks = self._make_tasks()
        result = list(filter_tasks(tasks, keyword="python"))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Study Python")

    def test_filter_combined(self):
        tasks = self._make_tasks()
        result = list(filter_tasks(tasks, category="Work", priority="medium"))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Budget review")

    def test_filter_no_match(self):
        tasks = self._make_tasks()
        result = list(filter_tasks(tasks, category="NonExistent"))
        self.assertEqual(len(result), 0)

    def test_filter_no_filters_returns_all(self):
        tasks = self._make_tasks()
        result = list(filter_tasks(tasks))
        self.assertEqual(len(result), len(tasks))

    def test_filter_is_generator(self):
        """filter_tasks should return a generator, not a list."""
        import types
        tasks = self._make_tasks()
        result = filter_tasks(tasks)
        self.assertIsInstance(result, types.GeneratorType)

    def test_filter_empty_list(self):
        result = list(filter_tasks([]))
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
