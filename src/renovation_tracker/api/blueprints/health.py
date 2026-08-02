"""Liveness and readiness endpoints."""

from flask import Blueprint, current_app

from renovation_tracker.storage.db import get_db

health_bp = Blueprint("health", __name__)