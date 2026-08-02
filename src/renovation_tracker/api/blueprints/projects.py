"""Routes for the projects resources."""
from flask import Blueprint, request

from renovation_tracker.storage.db import get_db
from renovation_tracker.api.errors import ConflictError
from renovation_tracker.models.project import ProjectCreate, ProjectRead, ProjectUpdate
from renovation_tracker.repositories import project_repository

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


@projects_bp.post("")
def create_project():
    """Create a new renovation project."""
    data = ProjectCreate.model_validate(request.get_json())
    conn = get_db()
    project_id = project_repository.create_project(conn, data)
    row = project_repository.get_project(conn, project_id)
    return ProjectRead.model_validate(dict(row)).model_dump(mode="json"), 201


@projects_bp.get("/<int:project_id>")
def get_project(project_id: int):
    """Fetch a single project by id."""
    conn = get_db()
    row = project_repository.get_project(conn, project_id)
    return ProjectRead.model_validate(dict(row)).model_dump(mode="json"), 200


@projects_bp.put("/<int:project_id>")
def update_project(project_id: int):
    """Update an existing project's fields."""
    data = ProjectUpdate.model_validate(request.get_json())
    conn = get_db()
    row = project_repository.update_project(conn, project_id, data)
    return ProjectRead.model_validate(dict(row)).model_dump(mode="json"), 200


@projects_bp.delete("/<int:project_id>")
def delete_project(project_id: int):
    """Delete a project. Requires ?confirm=true to prevent accidental deletion."""
    if request.args.get("confirm") != "true":
        raise ConflictError("Deletion requires ?confirm=true")

    conn = get_db()
    project_repository.delete_project(conn, project_id)
    return "", 204