"""
Database reset script for Lily Cafe POS System.

Removes the SQLite database file and recreates an empty schema.
Intended for production handover when you want a clean slate with no seed data.

Usage:
    uv run python -m scripts.reset_db_clean
"""

from pathlib import Path
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.db.session import init_db


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def resolve_sqlite_path() -> Path:
    """Resolve the filesystem path of the SQLite database."""
    url = make_url(settings.DATABASE_URL)

    if url.drivername != "sqlite":
        raise RuntimeError(
            "reset_db_clean is only intended for SQLite databases. "
            f"Current URL: {settings.DATABASE_URL}"
        )

    if not url.database:
        raise RuntimeError("SQLite database path is empty in DATABASE_URL.")

    db_path = Path(url.database)
    if not db_path.is_absolute():
        db_path = (BACKEND_ROOT / db_path).resolve()

    return db_path


def reset_database():
    """Delete the existing database file and recreate tables."""
    db_path = resolve_sqlite_path()

    if db_path.exists():
        print(f"Deleting database file: {db_path}")
        db_path.unlink()
    else:
        print(f"No existing database file found at {db_path}")

    # Ensure parent directory exists (important if path is nested)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print("Recreating empty database schema...")
    init_db()
    print("Database reset complete. You now have an empty schema.")


if __name__ == "__main__":
    reset_database()
