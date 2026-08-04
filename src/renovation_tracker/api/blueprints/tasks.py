"""Routes for renovation task resources."""

from flask import Blueprint, request

from renovation_tracker.storage.db import get_db
from renovation_tracker.models.task import TaskCreate, TaskRead, TaskUpdate, TaskComplete
from renovation_tracker.repositories import task_repository

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.post("/projects/<int:project_id>/tasks")
def create_task(project_id: int):
    """Add a task to a project."""
    data = TaskCreate.model_validate(request.get_json())
    conn = get_db()
    task_id = task_repository.create_task(conn, project_id, data)
    row = task_repository.get_task(conn, task_id)
    return TaskRead.model_validate(dict(row)).model_dump(mode="json"), 201


@tasks_bp.get("/projects/<int:project_id>/tasks")
def list_tasks(project_id: int):
    """List tasks for a project, with optional filters."""
    conn = get_db()
    rows = task_repository.list_tasks(
        conn,
        project_id,
        status=request.args.get("status"),
        trade=request.args.get("trade_category"),
        estimated_min=request.args.get("estimated_min", type=int),
        estimated_max=request.args.get("estimated_max", type=int),
        actual_min=request.args.get("actual_min", type=int),
        actual_max=request.args.get("actual_max", type=int),
        description_contains=request.args.get("description_contains"),
    )
    tasks = [TaskRead.model_validate(dict(row)).model_dump(mode="json") for row in rows]
    return {"tasks": tasks}, 200


@tasks_bp.put("/tasks/<int:task_id>")
def update_task(task_id: int):
    """Update an existing task's fields."""
    data = TaskUpdate.model_validate(request.get_json())
    conn = get_db()
    row = task_repository.update_task(conn, task_id, data)
    return TaskRead.model_validate(dict(row)).model_dump(mode="json"), 200


@tasks_bp.delete("/tasks/<int:task_id>")
def delete_task(task_id: int):
    """Delete a task. Requires ?confirm=true to prevent accidental deletion."""
    from renovation_tracker.api.errors import ConflictError

    if request.args.get("confirm") != "true":
        raise ConflictError("Deletion requires ?confirm=true")

    conn = get_db()
    task_repository.delete_task(conn, task_id)
    return "", 204

@tasks_bp.post("/tasks/<int:task_id>/complete")
def complete_task(task_id: int):
    """Mark a task done and record its actual cost, atomically
    reflecting the change in the project's totals.
    """
    data = TaskComplete.model_validate(request.get_json())
    conn = get_db()
    updated_task, totals = task_repository.complete_task(conn, task_id, data)

    response = TaskRead.model_validate(dict(updated_task)).model_dump(mode="json")
    response["project_totals"] = totals
    return response, 200