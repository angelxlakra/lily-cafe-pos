"""
Migration script to add is_served column to order_items table.
Run this script to update existing databases with the new is_served field.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine
from app.core.config import settings


def migrate():
    """Add is_served column to order_items table if it doesn't exist."""
    print("Running migration: Add is_served to order_items")
    print(f"Database: {settings.DATABASE_URL}")

    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("PRAGMA table_info(order_items)"))
        columns = [row[1] for row in result]

        if 'is_served' in columns:
            print("✓ Column 'is_served' already exists. Skipping migration.")
            return

        # Add the column with default value False
        print("Adding 'is_served' column to order_items table...")
        conn.execute(text(
            "ALTER TABLE order_items ADD COLUMN is_served BOOLEAN DEFAULT 0 NOT NULL"
        ))
        conn.commit()

        print("✓ Migration completed successfully!")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
