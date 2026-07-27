"""Application factory for the Home Renovation Tracker API."""
from flask import Flask, g
from pathlib import Path
import os

from renovation_tracker.api.blueprints.projects import projects_bp
from renovation_tracker.api.blueprints.tasks import tasks_bp
from renovation_tracker.storage.db import init_db

_DEFAULT_DB_PATH = (
    Path(__file__).resolve().parent.parent / "renovation_tracker.db"
)

def create_app(db_path: Path | str | None = None) -> Flask:
    """Creating and configuring the Flask app"""
    app = Flask(__name__)

    app.config["DB_PATH"] = str(
        db_path or os.environ.get("DB_PATH") or _DEFAULT_DB_PATH
    )

    init_db(app.config["DB_PATH"])

    # mount the blueprints to the flask app to allow them to be accessable.
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)



    @app.teardown_appcontext
    def _close_db(_exc): # function that will close db connction when app is closed.
        db = g.pop("db", None)
        if db is not None:
            db.close()

    return app 


if __name__ == "__main__":
    create_app().run(debug=True)