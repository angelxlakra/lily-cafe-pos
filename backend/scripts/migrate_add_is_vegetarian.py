"""
Migration script to add is_vegetarian column to menu_items table.

This script safely adds the is_vegetarian column to existing databases.
If the column already exists, it will skip the migration.

Usage:
    uv run python -m scripts.migrate_add_is_vegetarian
"""

import sqlite3
from pathlib import Path
from sqlalchemy.engine import make_url

from app.core.config import settings


def resolve_sqlite_path() -> Path:
    """Resolve the filesystem path of the SQLite database."""
    url = make_url(settings.DATABASE_URL)

    if url.drivername != "sqlite":
        raise RuntimeError(
            "This migration is only intended for SQLite databases. "
            f"Current URL: {settings.DATABASE_URL}"
        )

    # Extract database path from URL
    if url.database and url.database.startswith("/"):
        db_path = Path(url.database)
    else:
        # Relative path
        backend_root = Path(__file__).resolve().parents[1]
        db_path = backend_root / (url.database or "lily_cafe.db")

    return db_path


def migrate():
    """Add is_vegetarian column to menu_items table."""
    db_path = resolve_sqlite_path()

    if not db_path.exists():
        print(f"[ERROR] Database not found at {db_path}")
        print("   Run 'uv run python -m scripts.reset_db_with_seed' to create a new database.")
        return

    print(f"[INFO] Checking database at {db_path}")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(menu_items)")
        columns = [row[1] for row in cursor.fetchall()]

        if "is_vegetarian" in columns:
            print("[OK] Column 'is_vegetarian' already exists in menu_items table.")
            print("   No migration needed.")
        else:
            print("[MIGRATING] Adding 'is_vegetarian' column to menu_items table...")

            # Add the column with default value True (vegetarian by default)
            cursor.execute("""
                ALTER TABLE menu_items
                ADD COLUMN is_vegetarian BOOLEAN DEFAULT 1
            """)

            conn.commit()
            print("[SUCCESS] Successfully added 'is_vegetarian' column!")
            print("   Default value: TRUE (vegetarian)")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Add is_vegetarian column to menu_items")
    print("=" * 60)
    migrate()
    print("=" * 60)
    print("[SUCCESS] Migration complete!")
