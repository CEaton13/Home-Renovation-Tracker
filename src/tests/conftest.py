"""Shared pytest fixtures for the renovation tracker test suite."""

import os
import tempfile

import pytest

from renovation_tracker.app import create_app
from tests.stubs import StubSuccessClient


@pytest.fixture
def app():
    """Provide a Flask app configured against a fresh temporary database
    for each test.
    """
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.environ["DB_PATH"] = db_path

    flask_app = create_app()
    flask_app.config["ENRICHMENT_CLIENT"] = StubSuccessClient()

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Provide a Flask test client bound to the `app` fixture."""
    return app.test_client()