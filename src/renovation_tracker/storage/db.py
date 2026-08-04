"""Database connection management for the app."""
import sqlite3
from pathlib import Path
from flask import current_app, g

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open a SQLite connection configured for this application."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # w/o this rows come back as tuples rather than dict
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(db_path: Path | str | None = None) -> None:
    """Create tables if they do not already exist."""
    conn = connect(db_path)
    try:
        conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8")) # read in all the schema DDL for our tables and execute it 
        conn.commit()
    finally:
        conn.close()

def get_db() -> sqlite3.Connection:
    """Get the SQLite connection for the current request.
    """
    if "db" not in g:
        g.db = connect(current_app.config["DB_PATH"])
    return g.db


def close_db(_exception: Exception | None = None) -> None:
    """Close the request-scoped connection, if one was opened.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()