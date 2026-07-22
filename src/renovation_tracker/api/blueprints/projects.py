"""Routes for the projects resources."""
from flask import Blueprint

# A blueprint is a group of routes that we attach to the app 
projects_bp = Blueprint("tickets", __name__)