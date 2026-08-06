"""Functions to access the data from the db for projects."""

import sqlite3
from sqlite3 import IntegrityError

from renovation_tracker.models.project import ProjectCreate, ProjectUpdate

from renovation_tracker.api.errors import NotFoundError
from renovation_tracker.api.errors import ConflictError

def create_project(conn: sqlite3.Connection, data: ProjectCreate) -> int:
    """Create a new project with status default to 'planning'."""
    cursor = conn.execute(
        """
        INSERT INTO projects (name, room, budget, start_date, target_completion_date, project_status)
        VALUES (?, ?, ?, ?, ?, 'planning')
        """,
        (data.name, data.room, data.budget, data.start_date.isoformat(), data.target_completion_date.isoformat()),
    )
    conn.commit()
    return cursor.lastrowid

def get_project(conn: sqlite3.Connection, project_id: int) -> sqlite3.Row:
    """Access a single project by the id."""
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Project {project_id} not found")
    return row


def update_project(conn: sqlite3.Connection, project_id: int, data: ProjectUpdate) -> sqlite3.Row:
    """Update the fields stored for the project."""
    get_project(conn, project_id)  # raises NotFoundError if missing

    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return get_project(conn, project_id)

    if updates.get("project_status") == "completed":
        open_task_ids = _get_open_task_ids(conn, project_id)
        if open_task_ids:
            raise ConflictError(
                f"Project {project_id} cannot be completed — tasks not done: {open_task_ids}"
            )

    set_clause = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values())
    values.append(project_id)

    conn.execute(f"UPDATE projects SET {set_clause}, updated_at = datetime('now') WHERE id = ?", values)
    conn.commit()
    return get_project(conn, project_id)

def delete_project(conn: sqlite3.Connection, project_id: int) -> None:
    """The ability to delete a project based on id. Must not have any tasks still open with the project before deletion."""
    get_project(conn, project_id)  # raises NotFoundError if missing

    try:
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
    except IntegrityError as e:
        conn.rollback()
        raise ConflictError(f"Project {project_id} has existing tasks and cannot be deleted") from e

def list_projects_with_aggregates(
    conn: sqlite3.Connection,
    room: str | None = None,
    status: str | None = None,
    budget_min: int | None = None,
    budget_max: int | None = None,
    target_date_from: str | None = None,
    target_date_to: str | None = None,
) -> list[sqlite3.Row]:
    """List all projects with optional filters and aggregate data."""

    query = """
        SELECT
            p.*,
            COALESCE(SUM(t.est_cost), 0) AS total_est_cost,
            COALESCE(SUM(t.actual_cost), 0) AS total_actual_cost,
            p.budget - COALESCE(SUM(t.actual_cost), 0) AS remaining_budget,
            CASE WHEN COALESCE(SUM(t.actual_cost), 0) > p.budget THEN 1 ELSE 0 END AS over_budget,
            COUNT(t.id) AS task_count
        FROM projects p
        LEFT JOIN tasks t ON t.project_id = p.id
        WHERE 1 = 1
    """
    params: list = []

    if room:
        query += " AND p.room LIKE ?"
        params.append(f"%{room}%")
    if status:
        query += " AND p.project_status = ?"
        params.append(status)
    if budget_min is not None:
        query += " AND p.budget >= ?"
        params.append(budget_min)
    if budget_max is not None:
        query += " AND p.budget <= ?"
        params.append(budget_max)
    if target_date_from:
        query += " AND p.target_completion_date >= ?"
        params.append(target_date_from)
    if target_date_to:
        query += " AND p.target_completion_date <= ?"
        params.append(target_date_to)

    query += " GROUP BY p.id ORDER BY p.id"

    return conn.execute(query, params).fetchall()

def get_project_totals(conn: sqlite3.Connection, project_id: int) -> dict:
    """Compute live cost aggregates for a single project."""
    row = conn.execute(
        """
        SELECT
            p.budget,
            COALESCE(SUM(t.est_cost), 0) AS total_est_cost,
            COALESCE(SUM(t.actual_cost), 0) AS total_actual_cost
        FROM projects p
        LEFT JOIN tasks t ON t.project_id = p.id
        WHERE p.id = ?
        GROUP BY p.id
        """,
        (project_id,),
    ).fetchone()

    if row is None:
        raise NotFoundError(f"Project {project_id} not found")

    total_actual_cost = row["total_actual_cost"]
    return {
        "total_est_cost": row["total_est_cost"],
        "total_actual_cost": total_actual_cost,
        "remaining_budget": row["budget"] - total_actual_cost,
        "over_budget": total_actual_cost > row["budget"],
    }


def _get_open_task_ids(conn: sqlite3.Connection, project_id: int) -> list[int]:
    """Return ids of tasks under a project that are not yet 'done'."""
    rows = conn.execute(
        "SELECT id FROM tasks WHERE project_id = ? AND task_status != 'done'",
        (project_id,),
    ).fetchall()
    return [row["id"] for row in rows]

def update_project_enrichment(
    conn: sqlite3.Connection, project_id: int, enrichment_payload: str | None, enrichment_status: str) -> None:
    """Persist the result of an enrichment attempt on a project."""
    conn.execute(
        "UPDATE projects SET enrichment_payload = ?, enrichment_status = ?, updated_at = datetime('now') WHERE id = ?",
        (enrichment_payload, enrichment_status, project_id),
    )
    conn.commit()