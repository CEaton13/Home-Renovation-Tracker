"""Application factory for the Home Renovation Tracker API."""
from flask import Flask


def create_app() -> Flask:
    """Creating and configuring the Flask app"""
    app = Flask(__name__)

    return app 


if __name__ == "__main__":
    create_app().run(debug=True)