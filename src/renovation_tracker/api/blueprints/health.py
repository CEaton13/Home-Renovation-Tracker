"""Liveness and readiness endpoints."""

from flask import Blueprint, current_app

from renovation_tracker.storage.db import get_db

health_bp = Blueprint("health", __name__)

@health_bp.get("/live")
def live():
    """Confirm the process is up. Does not check downstream dependencies."""
    return {"status": "live"}, 200


@health_bp.get("/ready")
def ready():
    """Confirm downstream dependencies (the database) are reachable."""
    try:
        conn = get_db()
        conn.execute("SELECT 1").fetchone()
        return {"status": "ready"}, 200
    except Exception:
        current_app.logger.exception("Readiness check failed")
        return {"status": "not_ready"}, 503