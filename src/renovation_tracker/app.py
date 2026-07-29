"""Application factory for the Home Renovation Tracker API."""
from flask import Flask, g
from pathlib import Path
import os

from renovation_tracker.api.blueprints.projects import projects_bp
from renovation_tracker.api.blueprints.tasks import tasks_bp
from renovation_tracker.api.errors import ConflictError, DomainError, NotFoundError, ValidationError

from renovation_tracker.storage.db import init_db, close_db

_DEFAULT_DB_PATH = (
    Path(__file__).resolve().parent.parent / "renovation_tracker.db"
)

def create_app(db_path: Path | str | None = None) -> Flask:
    """Creating and configuring the Flask app"""
    app = Flask(__name__)

    app.config["DB_PATH"] = str(
        db_path or os.environ.get("DB_PATH") or _DEFAULT_DB_PATH
    )
    # create the db connection 
    init_db(app.config["DB_PATH"])
    # close the db
    app.teardown_appcontext(close_db)

    # mount the blueprints to the flask app to allow them to be accessable.
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)

    # map the error handling
    @app.errorhandler(NotFoundError)
    def handle_not_found(e: NotFoundError):
        return {"error_code": e.error_code, "message": e.message}, 404

    @app.errorhandler(ConflictError)
    def handle_conflict(e: ConflictError):
        return {"error_code": e.error_code, "message": e.message}, 409

    @app.errorhandler(ValidationError)
    def handle_validation(e: ValidationError):
        return {"error_code": e.error_code, "message": e.message}, 422

    @app.errorhandler(DomainError)
    def handle_domain_error(e: DomainError):
        return {"error_code": e.error_code, "message": e.message}, 400

    return app 


if __name__ == "__main__":
    create_app().run(debug=True)