"""
Migration script to add v0.2.0 inventory and cash counter tables.
Creates 4 new tables:
- inventory_categories
- inventory_items
- inventory_transactions
- daily_cash_counter

Run this script to update existing databases with v0.2.0 schema.
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


def migrate():
    """Create v0.2.0 database tables."""
    print("Running migration: Add v0.2.0 inventory and cash counter tables")
    print(f"Database: {settings.DATABASE_URL}")
    print("")

    with engine.connect() as conn:
        # 1. Create inventory_categories table
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
            print("✓ Created 'inventory_categories' table")

        # 2. Create inventory_items table
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
            print("✓ Created 'inventory_items' table with indexes")

        # 3. Create inventory_transactions table
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
            print("✓ Created 'inventory_transactions' table with indexes")

        # 4. Create daily_cash_counter table
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
            print("✓ Created 'daily_cash_counter' table with indexes")

        print("")
        print("✓ Migration completed successfully!")
        print("")
        print("Created tables:")
        print("  - inventory_categories")
        print("  - inventory_items")
        print("  - inventory_transactions")
        print("  - daily_cash_counter")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
