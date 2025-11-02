"""
Development reset script for Lily Cafe POS System.

Removes the SQLite database file, recreates the schema, and seeds it with sample data.
Use this during development to quickly return to the default dataset.

Usage:
    uv run python -m scripts.reset_db_with_seed
"""

from pathlib import Path
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.db.session import init_db
from scripts.seed_data import seed_database


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def resolve_sqlite_path() -> Path:
    """Resolve the filesystem path of the SQLite database."""
    url = make_url(settings.DATABASE_URL)

    if url.drivername != "sqlite":
        raise RuntimeError(
            "reset_db_with_seed is only intended for SQLite databases. "
            f"Current URL: {settings.DATABASE_URL}"
        )

    if not url.database:
        raise RuntimeError("SQLite database path is empty in DATABASE_URL.")

    db_path = Path(url.database)
    if not db_path.is_absolute():
        db_path = (BACKEND_ROOT / db_path).resolve()

    return db_path


def reset_and_seed_database():
    """Delete the database, recreate tables, and populate seed data."""
    db_path = resolve_sqlite_path()

    if db_path.exists():
        print(f"Deleting database file: {db_path}")
        db_path.unlink()
    else:
        print(f"No existing database file found at {db_path}")

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print("Recreating database schema...")
    init_db()

    print("Seeding database with default data...")
    seed_database()
    print("Database reset and seed complete.")


if __name__ == "__main__":
    reset_and_seed_database()
