"""Data-access functions for renovation tasks."""

import sqlite3

from renovation_tracker.models.task import TaskCreate, TaskUpdate
from renovation_tracker.api.errors import NotFoundError
from renovation_tracker.repositories.project_repository import get_project

def create_task(conn: sqlite3.Connection, project_id: int, data: TaskCreate) -> int:
    """Create a new task for a given project."""
    get_project(conn, project_id)  # raises NotFoundError if missing

    cursor = conn.execute(
        """
       INSERT INTO tasks (project_id, description, est_cost, trade_category, task_status)
        VALUES (?, ?, ?, ?, 'todo')
        """,
        (project_id, data.description, data.est_cost, data.trade_category),
    )
    conn.commit()
    return cursor.lastrowid

def get_task(conn: sqlite3.Connection, task_id: int) -> sqlite3.Row:
    """Fetch a single task by id."""
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Task {task_id} not found")
    return row

def list_tasks(
    conn: sqlite3.Connection,
    project_id: int,
    status: str | None = None,
    trade: str | None = None,
    estimated_min: int | None = None,
    estimated_max: int | None = None,
    actual_min: int | None = None,
    actual_max: int | None = None,
    description_contains: str | None = None,
) -> list[sqlite3.Row]:
    """List tasks for a project, with optional filters."""
    get_project(conn, project_id)  # raises NotFoundError if missing

    query = "SELECT * FROM tasks WHERE project_id = ?"
    params: list = [project_id]

    if status:
        query += " AND task_status = ?"
        params.append(status)
    if trade:
        query += " AND trade_category = ?"
        params.append(trade)
    if estimated_min is not None:
        query += " AND est_cost >= ?"
        params.append(estimated_min)
    if estimated_max is not None:
        query += " AND est_cost <= ?"
        params.append(estimated_max)
    if actual_min is not None:
        query += " AND actual_cost >= ?"
        params.append(actual_min)
    if actual_max is not None:
        query += " AND actual_cost <= ?"
        params.append(actual_max)
    if description_contains:
        query += " AND description LIKE ?"
        params.append(f"%{description_contains}%")

    query += " ORDER BY id"
    return conn.execute(query, params).fetchall()


def update_task(conn: sqlite3.Connection, task_id: int, data: TaskUpdate) -> sqlite3.Row:
    """Update only the fields provided on a task."""
    get_task(conn, task_id)  # raises NotFoundError if missing

    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return get_task(conn, task_id)

    set_clause = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values())
    values.append(task_id)

    conn.execute(f"UPDATE tasks SET {set_clause}, updated_at = datetime('now') WHERE id = ?", values)
    conn.commit()
    return get_task(conn, task_id)