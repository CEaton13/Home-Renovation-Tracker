"""Functions to access the data from the db for projects."""

from sqlite3 import sqlite3, IntegrityError

from renovation_tracker.models.project import ProjectCreate, ProjectUpdate\

from renovation_tracker.api.errors import NotFoundError
from renovation_tracker.api.errors import ConflictError

def create_project(conn: sqlite3.Connection, data: ProjectCreate) -> int:
    """Create a new project with status default to 'planning'."""
    cursor = conn.execute(
        """
        INSERT INTO projects (name, room, budget, start_date, target_completion_date, status)
        VALUES (?, ?, ?, ?, ?, 'planning')
        """,
        (data.name, data.room, data.budget_cents, data.start_date.isoformat(), data.target_completion_date.isoformat()),
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