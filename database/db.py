"""
database/db.py - Database initialisation and low-level CRUD helpers.

All SQL lives here so the rest of the application never writes raw SQL.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator, List, Optional

from config import get_config
from models.task import Task


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that opens a database connection and guarantees cleanup.

    Yields a sqlite3.Connection with row_factory set so columns can be
    accessed by name as well as by index.
    """
    cfg = get_config()
    conn = sqlite3.connect(cfg.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like access
    try:
        yield conn
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create the tasks table if it does not already exist."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT    DEFAULT '',
                category    TEXT    DEFAULT 'General',
                priority    TEXT    DEFAULT 'medium',
                due_date    TEXT,
                completed   INTEGER DEFAULT 0,
                created_at  TEXT    NOT NULL
            )
            """
        )


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

def insert_task(task: Task) -> int:
    """
    Persist a new Task and return the auto-assigned primary key.

    Parameters
    ----------
    task : Task
        The task object to insert. Its ``id`` field is ignored.

    Returns
    -------
    int
        The new row's primary key.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, category, priority, due_date, completed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.title,
                task.description,
                task.category,
                task.priority,
                task.due_date,
                int(task.completed),
                task.created_at,
            ),
        )
        return cursor.lastrowid


def fetch_all_tasks() -> List[Task]:
    """Return every task ordered by creation date descending."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, description, category, priority, due_date, completed, created_at
            FROM tasks
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [Task.from_row(tuple(row)) for row in rows]


def fetch_task_by_id(task_id: int) -> Optional[Task]:
    """Return a single Task or None if not found."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, title, description, category, priority, due_date, completed, created_at
            FROM tasks WHERE id = ?
            """,
            (task_id,),
        ).fetchone()
    return Task.from_row(tuple(row)) if row else None


def update_task(task: Task) -> None:
    """Overwrite all mutable columns for the given task id."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET title       = ?,
                description = ?,
                category    = ?,
                priority    = ?,
                due_date    = ?,
                completed   = ?
            WHERE id = ?
            """,
            (
                task.title,
                task.description,
                task.category,
                task.priority,
                task.due_date,
                int(task.completed),
                task.id,
            ),
        )


def delete_task(task_id: int) -> None:
    """Remove a task row by primary key."""
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def toggle_task_completion(task_id: int) -> None:
    """Flip the completed flag for the given task."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET completed = NOT completed WHERE id = ?",
            (task_id,),
        )
