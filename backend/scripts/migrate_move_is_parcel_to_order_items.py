"""
Migration script to move is_parcel from orders table to order_items table.
This allows individual items to be marked as parcel instead of the entire order.

Run this script to update existing databases with the new is_parcel field on order_items.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine
from app.core.config import settings


def migrate():
    """Move is_parcel from orders to order_items table."""
    print("Running migration: Move is_parcel from orders to order_items")
    print(f"Database: {settings.DATABASE_URL}")

    with engine.connect() as conn:
        # Check if order_items already has is_parcel column
        result = conn.execute(text("PRAGMA table_info(order_items)"))
        columns = [row[1] for row in result]
        
        if 'is_parcel' in columns:
            print("✓ Column 'is_parcel' already exists in order_items. Skipping migration.")
            return

        # Check if orders table has is_parcel column
        result = conn.execute(text("PRAGMA table_info(orders)"))
        orders_columns = [row[1] for row in result]
        has_orders_is_parcel = 'is_parcel' in orders_columns

        # Add is_parcel column to order_items
        print("Adding 'is_parcel' column to order_items table...")
        conn.execute(text(
            "ALTER TABLE order_items ADD COLUMN is_parcel BOOLEAN DEFAULT 0 NOT NULL"
        ))
        conn.commit()

        # If orders table has is_parcel, copy the value to all order_items for that order
        if has_orders_is_parcel:
            print("Copying is_parcel values from orders to order_items...")
            conn.execute(text("""
                UPDATE order_items
                SET is_parcel = (
                    SELECT orders.is_parcel
                    FROM orders
                    WHERE orders.id = order_items.order_id
                )
            """))
            conn.commit()
            print("✓ Copied is_parcel values from orders to order_items")

        # Note: We don't remove is_parcel from orders table in case rollback is needed
        # It can be removed manually later if desired

        print("✓ Migration completed successfully!")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

