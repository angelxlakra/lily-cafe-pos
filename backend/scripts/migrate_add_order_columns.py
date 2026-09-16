"""
Migration script to add the newer columns to the orders table.

Adds:
  - canceled_at / canceled_by / cancel_reason — who soft-deleted an order and why
  - last_edited_at / last_edited_by / edit_count — who corrected it after billing
  - notes — kitchen/bar instruction printed on the chit

Run this script to update existing databases. It is idempotent: columns that
already exist are skipped. The same check also runs automatically on app
startup (see app.db.session.ensure_order_columns).
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import engine, ensure_order_columns
from app.core.config import settings


def migrate():
    """Add the newer columns to the orders table if they don't exist."""
    print("Running migration: Add newer columns to orders")
    print(f"Database: {settings.DATABASE_URL}")

    added = ensure_order_columns(engine)

    if added:
        for column in added:
            print(f"  + Added column '{column}'")
        print("✓ Migration completed successfully!")
    else:
        print("✓ All columns already exist. Nothing to do.")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
