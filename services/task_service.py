"""
services/task_service.py - Business logic for task management.

This layer sits between the routes and the database.  It owns:
  * Input validation (via a reusable decorator)
  * Custom exception raising
  * Generator-based task filtering
  * Statistics computation
"""

import functools
from datetime import date
from typing import Callable, Generator, List, Optional

from database.db import (
    delete_task,
    fetch_all_tasks,
    fetch_task_by_id,
    insert_task,
    toggle_task_completion,
    update_task,
)
from models.task import InvalidTaskError, Task, TaskNotFoundError


# ---------------------------------------------------------------------------
# Validation decorator
# ---------------------------------------------------------------------------

def validate_task_input(func: Callable) -> Callable:
    """
    Decorator that validates task keyword arguments before the wrapped
    function executes.

    Raises
    ------
    InvalidTaskError
        If the title is blank or the due_date is not a valid ISO date.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        title: str = kwargs.get("title", "")
        due_date: Optional[str] = kwargs.get("due_date")

        if not title or not title.strip():
            raise InvalidTaskError("Task title cannot be empty.")

        if due_date and due_date.strip():
            try:
                date.fromisoformat(due_date.strip())
            except ValueError:
                raise InvalidTaskError(
                    f"Invalid due date '{due_date}'. Use YYYY-MM-DD format."
                )

        return func(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Generator-based filtering
# ---------------------------------------------------------------------------

def filter_tasks(
    tasks: List[Task],
    category: Optional[str] = None,
    priority: Optional[str] = None,
    keyword: Optional[str] = None,
) -> Generator[Task, None, None]:
    """
    Lazily yield tasks that match ALL supplied filter criteria.

    Parameters
    ----------
    tasks    : full list of Task objects
    category : if given, only tasks whose category matches (case-insensitive)
    priority : if given, only tasks whose priority matches (case-insensitive)
    keyword  : if given, only tasks where title or description contains the
               keyword (case-insensitive)

    Yields
    ------
    Task
    """
    for task in tasks:
        if category and task.category.lower() != category.lower():
            continue
        if priority and task.priority.lower() != priority.lower():
            continue
        if keyword:
            kw = keyword.lower()
            if kw not in task.title.lower() and kw not in task.description.lower():
                continue
        yield task


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

@validate_task_input
def create_task(
    title: str,
    description: str = "",
    category: str = "General",
    priority: str = "medium",
    due_date: Optional[str] = None,
) -> Task:
    """
    Validate inputs, construct a Task, persist it and return the saved object.

    The ``@validate_task_input`` decorator runs before the function body.
    """
    task = Task(
        title=title.strip(),
        description=description.strip(),
        category=category,
        priority=priority.lower(),
        due_date=due_date.strip() if due_date and due_date.strip() else None,
    )
    new_id = insert_task(task)
    task.id = new_id
    return task


@validate_task_input
def edit_task(
    task_id: int,
    title: str,
    description: str = "",
    category: str = "General",
    priority: str = "medium",
    due_date: Optional[str] = None,
) -> Task:
    """
    Fetch an existing task, apply updates and persist them.

    Raises
    ------
    TaskNotFoundError
        If no task with ``task_id`` exists.
    """
    existing = fetch_task_by_id(task_id)
    if existing is None:
        raise TaskNotFoundError(f"Task with id {task_id} not found.")

    existing.title = title.strip()
    existing.description = description.strip()
    existing.category = category
    existing.priority = priority.lower()
    existing.due_date = due_date.strip() if due_date and due_date.strip() else None

    update_task(existing)
    return existing


def remove_task(task_id: int) -> None:
    """
    Delete a task by id.

    Raises
    ------
    TaskNotFoundError
        If no task with ``task_id`` exists.
    """
    if fetch_task_by_id(task_id) is None:
        raise TaskNotFoundError(f"Task with id {task_id} not found.")
    delete_task(task_id)


def complete_task(task_id: int) -> None:
    """
    Toggle the completed state of a task.

    Raises
    ------
    TaskNotFoundError
        If no task with ``task_id`` exists.
    """
    if fetch_task_by_id(task_id) is None:
        raise TaskNotFoundError(f"Task with id {task_id} not found.")
    toggle_task_completion(task_id)


def get_filtered_tasks(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    keyword: Optional[str] = None,
) -> List[Task]:
    """
    Return a list of tasks matching the given filters.

    Internally uses the ``filter_tasks`` generator, materialised into a list
    for template consumption.
    """
    all_tasks = fetch_all_tasks()
    # Normalise empty strings to None so the generator skips them
    cat = category if category and category.strip() else None
    pri = priority if priority and priority.strip() else None
    kw = keyword if keyword and keyword.strip() else None
    return list(filter_tasks(all_tasks, category=cat, priority=pri, keyword=kw))


def get_task_stats() -> dict:
    """
    Compute and return a summary statistics dictionary.

    Returns
    -------
    dict with keys: total, completed, pending, overdue
    """
    all_tasks = fetch_all_tasks()
    total = len(all_tasks)
    completed = sum(1 for t in all_tasks if t.completed)
    overdue = sum(1 for t in all_tasks if t.is_overdue)
    return {
        "total": total,
        "completed": completed,
        "pending": total - completed,
        "overdue": overdue,
    }
