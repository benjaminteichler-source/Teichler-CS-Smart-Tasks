"""
routes/task_routes.py - Flask Blueprint that maps HTTP requests to service calls.

All routes follow the pattern:
  1. Parse request data.
  2. Delegate to the service layer.
  3. Flash a user-friendly message.
  4. Redirect or render a template.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from models.task import InvalidTaskError, Task, TaskNotFoundError
from services.task_service import (
    complete_task,
    create_task,
    edit_task,
    fetch_task_by_id,
    get_filtered_tasks,
    get_task_stats,
    remove_task,
)

task_bp = Blueprint("tasks", __name__)

# Choices surfaced to templates
CATEGORIES = ["General", "Work", "School", "Personal", "Health", "Finance", "Other"]
PRIORITIES = ["low", "medium", "high"]


# ---------------------------------------------------------------------------
# Index / list
# ---------------------------------------------------------------------------

@task_bp.route("/")
def index():
    """Render the main task list, honouring optional filter query-params."""
    category = request.args.get("category", "")
    priority = request.args.get("priority", "")
    keyword = request.args.get("keyword", "")

    tasks = get_filtered_tasks(
        category=category or None,
        priority=priority or None,
        keyword=keyword or None,
    )
    stats = get_task_stats()

    return render_template(
        "index.html",
        tasks=tasks,
        stats=stats,
        categories=CATEGORIES,
        priorities=PRIORITIES,
        selected_category=category,
        selected_priority=priority,
        keyword=keyword,
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@task_bp.route("/task/new", methods=["POST"])
def create():
    """Handle the new-task form submission."""
    try:
        create_task(
            title=request.form.get("title", ""),
            description=request.form.get("description", ""),
            category=request.form.get("category", "General"),
            priority=request.form.get("priority", "medium"),
            due_date=request.form.get("due_date", ""),
        )
        flash("Task created successfully! ✅", "success")
    except InvalidTaskError as exc:
        flash(str(exc), "error")
    return redirect(url_for("tasks.index"))


# ---------------------------------------------------------------------------
# Edit (GET = show form, POST = process form)
# ---------------------------------------------------------------------------

@task_bp.route("/task/<int:task_id>/edit", methods=["GET", "POST"])
def edit(task_id: int):
    """Show the edit form or process submitted edits."""
    task = fetch_task_by_id(task_id)
    if task is None:
        flash("Task not found.", "error")
        return redirect(url_for("tasks.index"))

    if request.method == "POST":
        try:
            edit_task(
                task_id=task_id,
                title=request.form.get("title", ""),
                description=request.form.get("description", ""),
                category=request.form.get("category", "General"),
                priority=request.form.get("priority", "medium"),
                due_date=request.form.get("due_date", ""),
            )
            flash("Task updated successfully! ✏️", "success")
            return redirect(url_for("tasks.index"))
        except (InvalidTaskError, TaskNotFoundError) as exc:
            flash(str(exc), "error")

    return render_template(
        "edit.html",
        task=task,
        categories=CATEGORIES,
        priorities=PRIORITIES,
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@task_bp.route("/task/<int:task_id>/delete", methods=["POST"])
def delete(task_id: int):
    """Delete a task by id."""
    try:
        remove_task(task_id)
        flash("Task deleted. 🗑️", "success")
    except TaskNotFoundError as exc:
        flash(str(exc), "error")
    return redirect(url_for("tasks.index"))


# ---------------------------------------------------------------------------
# Toggle completion
# ---------------------------------------------------------------------------

@task_bp.route("/task/<int:task_id>/toggle", methods=["POST"])
def toggle(task_id: int):
    """Toggle the completed state of a task."""
    try:
        complete_task(task_id)
    except TaskNotFoundError as exc:
        flash(str(exc), "error")
    return redirect(url_for("tasks.index"))
