"""
Unified migration script for v0.1.x → v0.2.0

This script performs all database changes needed to upgrade from any v0.1.x version
to v0.2.0 in a single run. It is idempotent and safe to run multiple times.

Database changes:
1. Add quantity_served column to order_items table (v0.1.2 - partial serving)
2. Add is_parcel column to order_items table (v0.1.3 - parcel feature)
3. Create inventory_categories table (v0.2.0)
4. Create inventory_items table (v0.2.0)
5. Create inventory_transactions table (v0.2.0)
6. Create daily_cash_counter table (v0.2.0)

Run this script after updating code to v0.2.0:
    uv run python scripts/migrate_v01x_to_v020.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine
from app.core.config import settings


def check_table_exists(conn, table_name: str) -> bool:
    """Check if a table exists in the database."""
    result = conn.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
    ), {"table_name": table_name})
    return result.fetchone() is not None


def check_column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result]
    return column_name in columns


def migrate():
    """Perform all v0.2.0 database migrations."""
    print("=" * 70)
    print("  Lily Cafe POS - Database Migration v0.1.x → v0.2.0")
    print("=" * 70)
    print(f"Database: {settings.DATABASE_URL}")
    print("")

    migration_count = 0

    with engine.connect() as conn:

        # =====================================================================
        # PART 1: Order Items Enhancements (v0.1.2 & v0.1.3)
        # =====================================================================
        print("PART 1: Order Items Enhancements (v0.1.2 & v0.1.3)")
        print("-" * 70)

        # 1.1 Check for quantity_served column (v0.1.2 - Partial serving)
        if check_column_exists(conn, 'order_items', 'quantity_served'):
            print("✓ Column 'order_items.quantity_served' already exists.")
        else:
            print("Adding 'quantity_served' column to order_items table...")
            conn.execute(text(
                "ALTER TABLE order_items ADD COLUMN quantity_served INTEGER DEFAULT 0 NOT NULL"
            ))
            conn.commit()
            migration_count += 1
            print("✓ Added 'quantity_served' column to order_items")

        # 1.2 Check for is_parcel column (v0.1.3 - Parcel feature)
        if check_column_exists(conn, 'order_items', 'is_parcel'):
            print("✓ Column 'order_items.is_parcel' already exists.")
        else:
            print("Adding 'is_parcel' column to order_items table...")

            # Add is_parcel column to order_items
            conn.execute(text(
                "ALTER TABLE order_items ADD COLUMN is_parcel BOOLEAN DEFAULT 0 NOT NULL"
            ))
            conn.commit()
            migration_count += 1
            print("✓ Added 'is_parcel' column to order_items")

            # If orders table has is_parcel, copy values to order_items
            if check_column_exists(conn, 'orders', 'is_parcel'):
                print("  Copying is_parcel values from orders to order_items...")
                conn.execute(text("""
                    UPDATE order_items
                    SET is_parcel = (
                        SELECT orders.is_parcel
                        FROM orders
                        WHERE orders.id = order_items.order_id
                    )
                """))
                conn.commit()
                print("  ✓ Copied is_parcel values from orders to order_items")

        print("")

        # =====================================================================
        # PART 2: Inventory Management Tables
        # =====================================================================
        print("PART 2: Inventory Management System")
        print("-" * 70)

        # 2.1 Create inventory_categories table
        if check_table_exists(conn, 'inventory_categories'):
            print("✓ Table 'inventory_categories' already exists.")
        else:
            print("Creating 'inventory_categories' table...")
            conn.execute(text("""
                CREATE TABLE inventory_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
            """))
            conn.commit()
            migration_count += 1
            print("✓ Created 'inventory_categories' table")

        # 2.2 Create inventory_items table
        if check_table_exists(conn, 'inventory_items'):
            print("✓ Table 'inventory_items' already exists.")
        else:
            print("Creating 'inventory_items' table...")
            conn.execute(text("""
                CREATE TABLE inventory_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL,
                    unit VARCHAR(20) NOT NULL,
                    current_quantity DECIMAL(10, 2) NOT NULL DEFAULT 0,
                    min_threshold DECIMAL(10, 2) NOT NULL DEFAULT 0,
                    cost_per_unit DECIMAL(10, 2),
                    category_id INTEGER,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY (category_id) REFERENCES inventory_categories(id)
                )
            """))
            # Create indexes
            conn.execute(text("CREATE INDEX ix_inventory_items_id ON inventory_items(id)"))
            conn.execute(text("CREATE INDEX ix_inventory_items_category_id ON inventory_items(category_id)"))
            conn.commit()
            migration_count += 1
            print("✓ Created 'inventory_items' table with indexes")

        # 2.3 Create inventory_transactions table
        if check_table_exists(conn, 'inventory_transactions'):
            print("✓ Table 'inventory_transactions' already exists.")
        else:
            print("Creating 'inventory_transactions' table...")
            conn.execute(text("""
                CREATE TABLE inventory_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    transaction_type VARCHAR(20) NOT NULL,
                    quantity DECIMAL(10, 2) NOT NULL,
                    notes VARCHAR(500),
                    recorded_by VARCHAR(100) NOT NULL,
                    previous_quantity DECIMAL(10, 2) NOT NULL,
                    new_quantity DECIMAL(10, 2) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES inventory_items(id)
                )
            """))
            # Create indexes
            conn.execute(text("CREATE INDEX ix_inventory_transactions_id ON inventory_transactions(id)"))
            conn.execute(text("CREATE INDEX ix_inventory_transactions_item_id ON inventory_transactions(item_id)"))
            conn.execute(text("CREATE INDEX ix_inventory_transactions_transaction_type ON inventory_transactions(transaction_type)"))
            conn.execute(text("CREATE INDEX ix_inventory_transactions_created_at ON inventory_transactions(created_at)"))
            conn.commit()
            migration_count += 1
            print("✓ Created 'inventory_transactions' table with indexes")

        print("")

        # =====================================================================
        # PART 3: Cash Counter System
        # =====================================================================
        print("PART 3: Cash Counter System")
        print("-" * 70)

        # 3.1 Create daily_cash_counter table
        if check_table_exists(conn, 'daily_cash_counter'):
            print("✓ Table 'daily_cash_counter' already exists.")
        else:
            print("Creating 'daily_cash_counter' table...")
            conn.execute(text("""
                CREATE TABLE daily_cash_counter (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    opening_balance DECIMAL(10, 2) NOT NULL,
                    closing_balance DECIMAL(10, 2),
                    expected_closing DECIMAL(10, 2),
                    variance DECIMAL(10, 2),
                    notes VARCHAR(500),
                    opened_by VARCHAR(100) NOT NULL,
                    closed_by VARCHAR(100),
                    verified_by VARCHAR(100),
                    opened_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    closed_at DATETIME,
                    verified_at DATETIME,
                    is_verified BOOLEAN NOT NULL DEFAULT 0
                )
            """))
            # Create indexes
            conn.execute(text("CREATE INDEX ix_daily_cash_counter_id ON daily_cash_counter(id)"))
            conn.execute(text("CREATE INDEX ix_daily_cash_counter_is_verified ON daily_cash_counter(is_verified)"))
            conn.commit()
            migration_count += 1
            print("✓ Created 'daily_cash_counter' table with indexes")

        print("")
        print("=" * 70)

        if migration_count == 0:
            print("✓ Database is already up to date!")
            print("  No migrations needed - all v0.2.0 tables and columns exist.")
        else:
            print(f"✓ Migration completed successfully!")
            print(f"  Applied {migration_count} database change(s)")

        print("")
        print("Database schema now includes:")
        print("  ✓ order_items.quantity_served column (v0.1.2 - partial serving)")
        print("  ✓ order_items.is_parcel column (v0.1.3 - item-level parcel marking)")
        print("  ✓ inventory_categories table (v0.2.0 - inventory categories)")
        print("  ✓ inventory_items table (v0.2.0 - inventory items with units)")
        print("  ✓ inventory_transactions table (v0.2.0 - purchase/usage/adjustment audit trail)")
        print("  ✓ daily_cash_counter table (v0.2.0 - daily cash counter records)")
        print("")
        print("Next steps:")
        print("  1. Restart backend: uv run uvicorn app.main:app --reload")
        print("  2. Test inventory features in admin panel")
        print("  3. Import inventory from WhatsApp template (optional)")
        print("  4. Open daily cash counter")
        print("")
        print("=" * 70)


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print("")
        print("=" * 70)
        print("✗ MIGRATION FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        print("")
        import traceback
        traceback.print_exc()
        print("")
        print("Troubleshooting:")
        print("  1. Ensure no other process is accessing the database")
        print("  2. Check database file permissions")
        print("  3. Verify database file exists and is not corrupted")
        print("  4. Try: sqlite3 restaurant.db 'PRAGMA integrity_check;'")
        print("")
        print("If issue persists, restore from backup and contact support.")
        print("=" * 70)
        sys.exit(1)
