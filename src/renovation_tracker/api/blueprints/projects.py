"""Routes for the projects resources."""
from flask import Blueprint, current_app, request
import structlog

from renovation_tracker.storage.db import get_db
from renovation_tracker.api.errors import ConflictError
from renovation_tracker.models.project import ProjectCreate, ProjectDashboardRead, ProjectRead, ProjectUpdate
from renovation_tracker.repositories import project_repository
from renovation_tracker.services.enrichment_service import generate_enrichment

logger = structlog.get_logger()

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


def _run_enrichment(conn, client, project_id: int, name: str, room: str, budget: int) -> None:
    """Call the enrichment client and persist the result.

    Never raises — a failure is logged (with the request's correlation id
    via the bound structlog context) and the project is marked
    enrichment_status='failed' instead, so the caller's create/update
    always succeeds regardless of enrichment outcome.
    """
    try:
        payload = generate_enrichment(client, name, room, budget)
        project_repository.update_project_enrichment(conn, project_id, payload.model_dump_json(), "complete")
    except Exception:
        logger.exception("enrichment_failed", project_id=project_id)
        project_repository.update_project_enrichment(conn, project_id, None, "failed")


@projects_bp.post("")
def create_project():
    """Create a new renovation project."""
    data = ProjectCreate.model_validate(request.get_json())
    conn = get_db()
    project_id = project_repository.create_project(conn, data)

    client = current_app.config.get("ENRICHMENT_CLIENT")
    if client is not None:
        _run_enrichment(conn, client, project_id, data.name, data.room, data.budget)

    row = project_repository.get_project(conn, project_id)
    return ProjectRead.model_validate(project_repository._row_to_project_dict(row)).model_dump(mode="json"), 201


@projects_bp.get("/<int:project_id>")
def get_project(project_id: int):
    """Fetch a single project by id."""
    conn = get_db()
    row = project_repository.get_project(conn, project_id)
    return ProjectRead.model_validate(project_repository._row_to_project_dict(row)).model_dump(mode="json"), 200


@projects_bp.put("/<int:project_id>")
def update_project(project_id: int):
    """Update an existing project's fields."""
    data = ProjectUpdate.model_validate(request.get_json())
    conn = get_db()
    row = project_repository.update_project(conn, project_id, data)

    if data.name is not None or data.budget is not None:
        client = current_app.config.get("ENRICHMENT_CLIENT")
        if client is not None:
            _run_enrichment(conn, client, project_id, row["name"], row["room"], row["budget"])
            row = project_repository.get_project(conn, project_id)

    return ProjectRead.model_validate(project_repository._row_to_project_dict(row)).model_dump(mode="json"), 200


@projects_bp.delete("/<int:project_id>")
def delete_project(project_id: int):
    """Delete a project. Requires ?confirm=true to prevent accidental deletion."""
    if request.args.get("confirm") != "true":
        raise ConflictError("Deletion requires ?confirm=true")

    conn = get_db()
    project_repository.delete_project(conn, project_id)
    return "", 204

@projects_bp.get("")
def list_projects():
    """List all projects with cost aggregates, with optional filters."""
    conn = get_db()
    rows = project_repository.list_projects_with_aggregates(
        conn,
        room=request.args.get("room"),
        status=request.args.get("status"),
        budget_min=request.args.get("budget_min", type=int),
        budget_max=request.args.get("budget_max", type=int),
        target_date_from=request.args.get("target_date_from"),
        target_date_to=request.args.get("target_date_to"),
    )
    projects = [ProjectDashboardRead.model_validate(project_repository._row_to_project_dict(row)).model_dump(mode="json") for row in rows]
    return {"projects": projects}, 200