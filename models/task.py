"""
models/task.py - Task model using Python dataclasses.

Defines the Task data model and custom exceptions used throughout the app.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class InvalidTaskError(Exception):
    """Raised when task data fails validation."""
    pass


class TaskNotFoundError(Exception):
    """Raised when a requested task does not exist in the database."""
    pass


# ---------------------------------------------------------------------------
# Task Model
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """
    Represents a single task in the task manager.

    Attributes:
        title:       Short, required name for the task.
        description: Optional longer description.
        category:    Grouping label (e.g., Work, School, Personal).
        priority:    Urgency level — 'low', 'medium', or 'high'.
        due_date:    Optional deadline (ISO date string YYYY-MM-DD).
        completed:   Whether the task has been finished.
        id:          Auto-assigned database primary key (None before insert).
        created_at:  ISO datetime string set at creation time.
    """

    title: str
    description: str = ""
    category: str = "General"
    priority: str = "medium"
    due_date: Optional[str] = None
    completed: bool = False
    id: Optional[int] = field(default=None)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Valid choices for constrained fields
    VALID_PRIORITIES: tuple = field(default=("low", "medium", "high"), init=False, repr=False, compare=False)
    VALID_CATEGORIES: tuple = field(
        default=("General", "Work", "School", "Personal", "Health", "Finance", "Other"),
        init=False, repr=False, compare=False,
    )

    def __post_init__(self) -> None:
        """Normalise and validate field values after construction."""
        self.title = self.title.strip()
        self.priority = self.priority.lower().strip()

    @property
    def is_overdue(self) -> bool:
        """Return True if the task has a past due date and is not completed."""
        if not self.due_date or self.completed:
            return False
        try:
            return date.fromisoformat(self.due_date) < date.today()
        except ValueError:
            return False

    @property
    def priority_badge(self) -> str:
        """Return a CSS class name corresponding to the priority level."""
        return {
            "low": "badge-low",
            "medium": "badge-medium",
            "high": "badge-high",
        }.get(self.priority, "badge-medium")

    @classmethod
    def from_row(cls, row: tuple) -> "Task":
        """
        Construct a Task from a raw sqlite3 row tuple.

        Row order must match the SELECT column order in db.py:
        (id, title, description, category, priority, due_date, completed, created_at)
        """
        return cls(
            id=row[0],
            title=row[1],
            description=row[2] or "",
            category=row[3] or "General",
            priority=row[4] or "medium",
            due_date=row[5],
            completed=bool(row[6]),
            created_at=row[7],
        )

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary (useful for JSON responses)."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "due_date": self.due_date,
            "completed": self.completed,
            "created_at": self.created_at,
        }
