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
        VALUES (?, ?, ?, ?, ?)
        """,
        (project_id, data.description, data.est_cost, data.trade_category, data.task_status),
    )
    conn.commit()
    return cursor.lastrowid