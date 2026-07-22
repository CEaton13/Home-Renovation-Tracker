"""Routes for the projects resources."""
from flask import Blueprint

# A blueprint is a group of routes that we attach to the app 
tasks_bp = Blueprint("tasks", __name__)