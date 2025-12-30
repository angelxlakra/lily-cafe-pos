"""
Migration script to add is_parcel column to orders table.
Run this script to update existing databases with the new is_parcel field.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine
from app.core.config import settings


def migrate():
    """Add is_parcel column to orders table if it doesn't exist."""
    print("Running migration: Add is_parcel to orders")
    print(f"Database: {settings.DATABASE_URL}")

    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("PRAGMA table_info(orders)"))
        columns = [row[1] for row in result]

        if 'is_parcel' in columns:
            print("✓ Column 'is_parcel' already exists. Skipping migration.")
            return

        # Add the column with default value False
        print("Adding 'is_parcel' column to orders table...")
        conn.execute(text(
            "ALTER TABLE orders ADD COLUMN is_parcel BOOLEAN DEFAULT 0 NOT NULL"
        ))
        conn.commit()

        print("✓ Migration completed successfully!")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)

