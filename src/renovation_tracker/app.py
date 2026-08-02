"""Application factory for the Home Renovation Tracker API."""
import os
import uuid

from flask import Flask, app, g, request
from pathlib import Path
from werkzeug.exceptions import HTTPException
from pydantic import ValidationError as PydanticValidationError

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


    # assign a unique request ID to each request for logging and tracing purposes
    @app.before_request
    def _assign_request_id():
        g.request_id = str(uuid.uuid4())

    def _error_envelope(error_code: str, message: str, errors: list | None = None) -> dict:
        envelope = {"error_code": error_code, "message": message, "request_id": g.get("request_id")}
        if errors:
            envelope["errors"] = errors
        return envelope

    # map the error handling
    @app.errorhandler(NotFoundError)
    def handle_not_found(e: NotFoundError):
        return _error_envelope(e.error_code, e.message), 404

    @app.errorhandler(ConflictError)
    def handle_conflict(e: ConflictError):
        return _error_envelope(e.error_code, e.message), 409

    @app.errorhandler(ValidationError)
    def handle_validation(e: ValidationError):
        return _error_envelope(e.error_code, e.message), 422

    @app.errorhandler(DomainError)
    def handle_domain_error(e: DomainError):
        return _error_envelope(e.error_code, e.message), 400

    @app.errorhandler(PydanticValidationError)
    def handle_pydantic_validation(e: PydanticValidationError):
        field_errors = [
            {"field": ".".join(str(part) for part in err["loc"]), "message": err["msg"]}
            for err in e.errors()
        ]
        return _error_envelope("validation_error", "Request validation failed", field_errors), 422

    @app.errorhandler(Exception)
    def handle_unexpected_error(e: Exception):
        if isinstance(e, HTTPException):
            return e
        app.logger.exception("Unhandled exception")
        return _error_envelope("internal_error", "An unexpected error occurred"), 500

    return app 


if __name__ == "__main__":
    create_app().run(debug=True)