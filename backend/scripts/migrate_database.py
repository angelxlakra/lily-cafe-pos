"""
Comprehensive Database Migration Script for Lily Cafe POS

This is the MASTER migration script that ensures your database schema is completely
up-to-date. It checks ALL tables, columns, and indexes, and applies any missing changes.

🎯 USAGE:
    uv run python scripts/migrate_database.py

📋 FEATURES:
- Checks all tables, columns, and indexes
- Idempotent (safe to run multiple times)
- Organized by feature/version for easy maintenance
- Single source of truth for database schema
- Easy to extend with new migrations

🔧 TO ADD NEW MIGRATIONS:
1. Add new table definitions to the appropriate section (CORE/INVENTORY/CASH_COUNTER/NEW_FEATURE)
2. Add new column definitions to existing tables in the SCHEMA_DEFINITIONS
3. Run this script - it will automatically detect and apply changes
4. No need for separate migration scripts!

📚 VERSION HISTORY:
- v0.1.0: Core POS tables (categories, menu_items, orders, order_items, payments)
- v0.1.2: Added quantity_served to order_items (partial serving feature)
- v0.1.3: Added is_parcel to order_items (item-level parcel marking)
- v0.2.0: Added inventory system + cash counter (4 new tables)
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from app.db.session import engine
from app.core.config import settings


# ============================================================================
# SCHEMA DEFINITIONS - Complete Target Schema
# ============================================================================
# Add new tables/columns here as the schema evolves. The script will
# automatically detect and apply missing changes.

# Column format: (name, type, constraints)
SCHEMA_DEFINITIONS = {
    # -------------------------------------------------------------------------
    # CORE POS TABLES (v0.1.0+)
    # -------------------------------------------------------------------------
    "categories": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("name", "VARCHAR(100)", "UNIQUE NOT NULL"),
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
        ],
        "indexes": [
            ("ix_categories_id", ["id"]),
            ("ix_categories_name", ["name"]),
        ],
    },

    "menu_items": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("name", "VARCHAR(200)", "NOT NULL"),
            ("description", "VARCHAR(500)", ""),
            ("price", "INTEGER", "NOT NULL"),
            ("category_id", "INTEGER", "NOT NULL"),
            ("is_vegetarian", "BOOLEAN", "DEFAULT 1"),
            ("is_beverage", "BOOLEAN", "DEFAULT 0"),
            ("is_available", "BOOLEAN", "DEFAULT 1"),
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
        ],
        "indexes": [
            ("ix_menu_items_id", ["id"]),
            ("ix_menu_items_name", ["name"]),
        ],
        "foreign_keys": [
            ("category_id", "categories", "id"),
        ],
    },

    "orders": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("order_number", "VARCHAR(50)", "UNIQUE NOT NULL"),
            ("table_number", "INTEGER", "NOT NULL"),
            ("customer_name", "VARCHAR(200)", ""),
            ("subtotal", "INTEGER", "NOT NULL"),
            ("gst_amount", "INTEGER", "NOT NULL"),
            ("total_amount", "INTEGER", "NOT NULL"),
            ("status", "VARCHAR(20)", "DEFAULT 'active' NOT NULL"),
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
        ],
        "indexes": [
            ("ix_orders_id", ["id"]),
            ("ix_orders_order_number", ["order_number"]),
            ("ix_orders_table_number", ["table_number"]),
            ("ix_orders_status", ["status"]),
            ("ix_orders_created_at", ["created_at"]),
        ],
    },

    "order_items": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("order_id", "INTEGER", "NOT NULL"),
            ("menu_item_id", "INTEGER", "NOT NULL"),
            ("menu_item_name", "VARCHAR(200)", "NOT NULL"),
            ("quantity", "INTEGER", "NOT NULL"),
            ("quantity_served", "INTEGER", "DEFAULT 0 NOT NULL"),  # v0.1.2
            ("unit_price", "INTEGER", "NOT NULL"),
            ("subtotal", "INTEGER", "NOT NULL"),
            ("is_beverage", "BOOLEAN", "DEFAULT 0"),
            ("is_served", "BOOLEAN", "DEFAULT 0"),
            ("is_parcel", "BOOLEAN", "DEFAULT 0 NOT NULL"),  # v0.1.3
        ],
        "indexes": [
            ("ix_order_items_id", ["id"]),
        ],
        "foreign_keys": [
            ("order_id", "orders", "id"),
            ("menu_item_id", "menu_items", "id"),
        ],
    },

    "payments": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("order_id", "INTEGER", "NOT NULL"),
            ("payment_method", "VARCHAR(20)", "NOT NULL"),
            ("amount", "INTEGER", "NOT NULL"),
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
        ],
        "indexes": [
            ("ix_payments_id", ["id"]),
        ],
        "foreign_keys": [
            ("order_id", "orders", "id"),
        ],
    },

    # -------------------------------------------------------------------------
    # INVENTORY SYSTEM (v0.2.0)
    # -------------------------------------------------------------------------
    "inventory_categories": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("name", "VARCHAR(100)", "UNIQUE NOT NULL"),
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME", ""),
        ],
    },

    "inventory_items": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("name", "VARCHAR(200)", "NOT NULL"),
            ("unit", "VARCHAR(20)", "NOT NULL"),
            ("current_quantity", "DECIMAL(10, 2)", "NOT NULL DEFAULT 0"),
            ("min_threshold", "DECIMAL(10, 2)", "NOT NULL DEFAULT 0"),
            ("cost_per_unit", "DECIMAL(10, 2)", ""),
            ("category_id", "INTEGER", ""),
            ("is_active", "BOOLEAN", "NOT NULL DEFAULT 1"),
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME", ""),
        ],
        "indexes": [
            ("ix_inventory_items_id", ["id"]),
            ("ix_inventory_items_category_id", ["category_id"]),
        ],
        "foreign_keys": [
            ("category_id", "inventory_categories", "id"),
        ],
    },

    "inventory_transactions": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("item_id", "INTEGER", "NOT NULL"),
            ("transaction_type", "VARCHAR(20)", "NOT NULL"),
            ("quantity", "DECIMAL(10, 2)", "NOT NULL"),
            ("notes", "VARCHAR(500)", ""),
            ("recorded_by", "VARCHAR(100)", "NOT NULL"),
            ("previous_quantity", "DECIMAL(10, 2)", "NOT NULL"),
            ("new_quantity", "DECIMAL(10, 2)", "NOT NULL"),
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
        ],
        "indexes": [
            ("ix_inventory_transactions_id", ["id"]),
            ("ix_inventory_transactions_item_id", ["item_id"]),
            ("ix_inventory_transactions_transaction_type", ["transaction_type"]),
            ("ix_inventory_transactions_created_at", ["created_at"]),
        ],
        "foreign_keys": [
            ("item_id", "inventory_items", "id"),
        ],
    },

    # -------------------------------------------------------------------------
    # CASH COUNTER SYSTEM (v0.2.0)
    # -------------------------------------------------------------------------
    "daily_cash_counter": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("date", "DATE", "UNIQUE NOT NULL"),
            ("opening_balance", "DECIMAL(10, 2)", "NOT NULL"),
            ("closing_balance", "DECIMAL(10, 2)", ""),
            ("expected_closing", "DECIMAL(10, 2)", ""),
            ("variance", "DECIMAL(10, 2)", ""),
            ("notes", "VARCHAR(500)", ""),
            ("opened_by", "VARCHAR(100)", "NOT NULL"),
            ("closed_by", "VARCHAR(100)", ""),
            ("verified_by", "VARCHAR(100)", ""),
            ("opened_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP NOT NULL"),
            ("closed_at", "DATETIME", ""),
            ("verified_at", "DATETIME", ""),
            ("is_verified", "BOOLEAN", "NOT NULL DEFAULT 0"),
        ],
        "indexes": [
            ("ix_daily_cash_counter_id", ["id"]),
            ("ix_daily_cash_counter_is_verified", ["is_verified"]),
        ],
    },

    # -------------------------------------------------------------------------
    # FUTURE FEATURES - Add new tables here
    # -------------------------------------------------------------------------
    # Example:
    # "customer_loyalty": {
    #     "columns": [
    #         ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
    #         ("phone", "VARCHAR(15)", "UNIQUE NOT NULL"),
    #         ("name", "VARCHAR(200)", "NOT NULL"),
    #         ("points", "INTEGER", "DEFAULT 0"),
    #         ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    #     ],
    #     "indexes": [
    #         ("ix_customer_loyalty_phone", ["phone"]),
    #     ],
    # },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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


def get_existing_columns(conn, table_name: str) -> List[str]:
    """Get list of all columns in a table."""
    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
    return [row[1] for row in result]


def check_index_exists(conn, index_name: str) -> bool:
    """Check if an index exists in the database."""
    result = conn.execute(text(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=:index_name"
    ), {"index_name": index_name})
    return result.fetchone() is not None


def create_table(conn, table_name: str, definition: Dict) -> bool:
    """Create a table with all its columns."""
    columns_sql = []
    foreign_keys_sql = []

    for col_name, col_type, col_constraints in definition["columns"]:
        column_def = f"{col_name} {col_type}"
        if col_constraints:
            column_def += f" {col_constraints}"
        columns_sql.append(column_def)

    # Add foreign keys if defined
    if "foreign_keys" in definition:
        for fk_column, ref_table, ref_column in definition["foreign_keys"]:
            fk_sql = f"FOREIGN KEY ({fk_column}) REFERENCES {ref_table}({ref_column})"
            foreign_keys_sql.append(fk_sql)

    all_constraints = columns_sql + foreign_keys_sql
    create_sql = f"CREATE TABLE {table_name} (\n    {',\n    '.join(all_constraints)}\n)"

    try:
        conn.execute(text(create_sql))
        conn.commit()
        print(f"    ✓ Created table '{table_name}'")
        return True
    except Exception as e:
        print(f"    ✗ Failed to create table '{table_name}': {e}")
        return False


def add_column(conn, table_name: str, col_name: str, col_type: str, col_constraints: str) -> bool:
    """Add a column to an existing table."""
    column_def = f"{col_name} {col_type}"
    if col_constraints:
        column_def += f" {col_constraints}"

    try:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_def}"))
        conn.commit()
        print(f"    ✓ Added column '{table_name}.{col_name}'")
        return True
    except Exception as e:
        print(f"    ✗ Failed to add column '{table_name}.{col_name}': {e}")
        return False


def create_index(conn, index_name: str, table_name: str, columns: List[str]) -> bool:
    """Create an index on a table."""
    columns_str = ", ".join(columns)
    try:
        conn.execute(text(f"CREATE INDEX {index_name} ON {table_name}({columns_str})"))
        conn.commit()
        print(f"    ✓ Created index '{index_name}'")
        return True
    except Exception as e:
        print(f"    ✗ Failed to create index '{index_name}': {e}")
        return False


# ============================================================================
# MIGRATION LOGIC
# ============================================================================

def migrate():
    """
    Comprehensive database migration.

    Checks ALL schema definitions and applies missing:
    - Tables
    - Columns
    - Indexes
    """
    print("=" * 80)
    print("  Lily Cafe POS - Comprehensive Database Migration")
    print("=" * 80)
    print(f"Database: {settings.DATABASE_URL}")
    print()

    changes_applied = 0

    with engine.connect() as conn:
        # Get list of existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        print("📊 SCHEMA VALIDATION & MIGRATION")
        print("-" * 80)
        print()

        # Process each table in schema definition
        for table_name, table_def in SCHEMA_DEFINITIONS.items():
            print(f"Checking table: {table_name}")

            # ----------------------------------------------------------------
            # 1. CHECK TABLE EXISTS
            # ----------------------------------------------------------------
            if not check_table_exists(conn, table_name):
                print(f"  ⚠️  Table '{table_name}' does not exist - creating...")
                if create_table(conn, table_name, table_def):
                    changes_applied += 1

                    # Create indexes for new table
                    if "indexes" in table_def:
                        for index_name, index_columns in table_def["indexes"]:
                            if create_index(conn, index_name, table_name, index_columns):
                                changes_applied += 1
                print()
                continue

            # ----------------------------------------------------------------
            # 2. CHECK COLUMNS
            # ----------------------------------------------------------------
            existing_columns = get_existing_columns(conn, table_name)
            missing_columns = []

            for col_name, col_type, col_constraints in table_def["columns"]:
                if col_name not in existing_columns:
                    missing_columns.append((col_name, col_type, col_constraints))

            if missing_columns:
                print(f"  ⚠️  Missing {len(missing_columns)} column(s) - adding...")
                for col_name, col_type, col_constraints in missing_columns:
                    if add_column(conn, table_name, col_name, col_type, col_constraints):
                        changes_applied += 1
            else:
                print(f"  ✓ All columns present")

            # ----------------------------------------------------------------
            # 3. CHECK INDEXES
            # ----------------------------------------------------------------
            if "indexes" in table_def:
                missing_indexes = []
                for index_name, index_columns in table_def["indexes"]:
                    if not check_index_exists(conn, index_name):
                        missing_indexes.append((index_name, index_columns))

                if missing_indexes:
                    print(f"  ⚠️  Missing {len(missing_indexes)} index(es) - creating...")
                    for index_name, index_columns in missing_indexes:
                        if create_index(conn, index_name, table_name, index_columns):
                            changes_applied += 1
                else:
                    print(f"  ✓ All indexes present")

            print()

        # ====================================================================
        # SUMMARY
        # ====================================================================
        print("=" * 80)
        if changes_applied == 0:
            print("✅ DATABASE IS UP-TO-DATE!")
            print("   No migrations needed - all schema definitions are present.")
        else:
            print(f"✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print(f"   Applied {changes_applied} schema change(s)")
        print()

        # Show current schema status
        print("📋 Current Database Schema:")
        print("-" * 80)

        for table_name in sorted(SCHEMA_DEFINITIONS.keys()):
            if check_table_exists(conn, table_name):
                columns = get_existing_columns(conn, table_name)
                print(f"  ✓ {table_name} ({len(columns)} columns)")

        print()
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Restart backend: uv run uvicorn app.main:app --reload")
        print("  2. Test all features to ensure migration was successful")
        print("  3. Create database backup if not already done")
        print()
        print("=" * 80)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print()
        print("=" * 80)
        print("✗ MIGRATION FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("Troubleshooting:")
        print("  1. Ensure no other process is accessing the database")
        print("  2. Check database file permissions")
        print("  3. Verify database file exists and is not corrupted")
        print("  4. Try: sqlite3 restaurant.db 'PRAGMA integrity_check;'")
        print()
        print("If issue persists, restore from backup and contact support.")
        print("=" * 80)
        sys.exit(1)
