"""Serves the minimal web UI as a static file."""

from pathlib import Path

from flask import Blueprint, send_from_directory

ui_bp = Blueprint("ui", __name__)

_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


@ui_bp.get("/")
def index():
    """Serve the single-page UI."""
    return send_from_directory(_STATIC_DIR, "index.html")