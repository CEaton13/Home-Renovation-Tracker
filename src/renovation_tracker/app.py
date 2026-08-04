"""Application factory for the Home Renovation Tracker API."""
import os
import uuid
import time
import structlog

from flask import Flask, app, g, request
from pathlib import Path
from werkzeug.exceptions import HTTPException
from pydantic import ValidationError as PydanticValidationError

from renovation_tracker.api.blueprints.projects import projects_bp
from renovation_tracker.api.blueprints.tasks import tasks_bp
from renovation_tracker.api.blueprints.health import health_bp
from renovation_tracker.api.errors import ConflictError, DomainError, NotFoundError, ValidationError
from renovation_tracker.storage.db import init_db, close_db
from renovation_tracker.logging_config import configure_logging
from renovation_tracker.azure_client import AzureEnrichmentClient
from renovation_tracker.azure_config import load_azure_config

_DEFAULT_DB_PATH = (
    Path(__file__).resolve().parent.parent / "renovation_tracker.db"
)

def create_app(db_path: Path | str | None = None) -> Flask:
    """Creating and configuring the Flask app"""
    # configure logging for the app before creating the app instance
    configure_logging()

    # create the Flask app instance
    app = Flask(__name__)

    # configure the database path for the app, using the provided db_path, or the environment variable, or the default path
    app.config["DB_PATH"] = str(
        db_path or os.environ.get("DB_PATH") or _DEFAULT_DB_PATH
    )
    # create the db connection 
    init_db(app.config["DB_PATH"])

    # configure the Azure OpenAI enrichment client for the app, if the required environment variables are set
    try:
        app.config["ENRICHMENT_CLIENT"] = AzureEnrichmentClient(load_azure_config())
    except RuntimeError:
        app.logger.warning("Azure OpenAI not configured — enrichment will be skipped on create/update")
        app.config["ENRICHMENT_CLIENT"] = None


    # close the db
    app.teardown_appcontext(close_db)

    # mount the blueprints to the flask app to allow them to be accessable.
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(health_bp)

    # setup request logging with a unique request ID for each request
    logger = structlog.get_logger()
    @app.before_request
    def _start_request_logging():
        g.request_id = str(uuid.uuid4())
        g.request_start_time = time.perf_counter()
        structlog.contextvars.bind_contextvars(request_id=g.request_id)
    
    @app.after_request
    def _log_request(response):
        duration_ms = round((time.perf_counter() - g.request_start_time) * 1000, 2)
        logger.info(
            "request_completed",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
    
    # clear the request logging context after each request to avoid leaking context between requests
    @app.teardown_request
    def _clear_request_logging(_exception=None):
        structlog.contextvars.clear_contextvars()

    # assign a unique request ID to each request for logging and tracing purposes
    # @app.before_request
    # def _assign_request_id():
    #     g.request_id = str(uuid.uuid4())

    # define a helper function to create a consistent error response envelope for API errors
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