"""
Comprehensive Database Migration Script for Lily Cafe POS

This is the MASTER migration script that ensures your database schema is completely
up-to-date. It checks ALL tables, columns, and indexes, and applies any missing changes.

═══════════════════════════════════════════════════════════════════════════════
🎯 USAGE
═══════════════════════════════════════════════════════════════════════════════

    uv run python scripts/migrate_database.py

That's it! Run this command:
  - After pulling new code
  - After checking out a different branch
  - When setting up a fresh database
  - Anytime you want to ensure schema is current

═══════════════════════════════════════════════════════════════════════════════
📋 HOW THIS WORKS
═══════════════════════════════════════════════════════════════════════════════

SCHEMA-DRIVEN APPROACH:
  1. You define the COMPLETE target schema below in SCHEMA_DEFINITIONS
  2. Script compares actual database to target schema
  3. Script applies ONLY what's missing (tables, columns, indexes)
  4. Safe to run multiple times - won't duplicate or break anything

IDEMPOTENT:
  - Run 1x = changes applied
  - Run 2x = "already up-to-date"
  - Run 100x = still safe!

═══════════════════════════════════════════════════════════════════════════════
🔧 HOW TO ADD NEW MIGRATIONS (Step-by-Step Guide)
═══════════════════════════════════════════════════════════════════════════════

╔═══════════════════════════════════════════════════════════════════════════╗
║ SCENARIO 1: ADD A NEW TABLE                                              ║
╚═══════════════════════════════════════════════════════════════════════════╝

Step 1: Find the appropriate section in SCHEMA_DEFINITIONS below
        (e.g., CORE POS TABLES, INVENTORY SYSTEM, or create NEW FEATURE section)

Step 2: Add your table definition:

    "table_name": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("name", "VARCHAR(200)", "NOT NULL"),
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
        ],
        "indexes": [
            ("ix_table_name_id", ["id"]),
        ],
        "foreign_keys": [  # Optional
            ("other_id", "other_table", "id"),
        ],
    },

Step 3: Run: uv run python scripts/migrate_database.py
Step 4: Done! Table, columns, and indexes created automatically.

Example - Adding customer loyalty table:

    # -------------------------------------------------------------------------
    # CUSTOMER LOYALTY (v0.3.0)
    # -------------------------------------------------------------------------
    "customer_loyalty": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("phone", "VARCHAR(15)", "UNIQUE NOT NULL"),
            ("name", "VARCHAR(200)", "NOT NULL"),
            ("email", "VARCHAR(200)", ""),
            ("points", "INTEGER", "DEFAULT 0"),
            ("tier", "VARCHAR(20)", "DEFAULT 'bronze'"),
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME", ""),
        ],
        "indexes": [
            ("ix_customer_loyalty_id", ["id"]),
            ("ix_customer_loyalty_phone", ["phone"]),
            ("ix_customer_loyalty_email", ["email"]),
        ],
    },


╔═══════════════════════════════════════════════════════════════════════════╗
║ SCENARIO 2: ADD A NEW COLUMN TO EXISTING TABLE                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

Step 1: Find the table in SCHEMA_DEFINITIONS
Step 2: Add your column to the "columns" list
Step 3: Run migration script
Step 4: Done!

Example - Adding 'notes' field to orders:

    "orders": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            # ... existing columns ...
            ("status", "VARCHAR(20)", "DEFAULT 'active' NOT NULL"),
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),

            # ⬇️ ADD NEW COLUMN HERE (at the end is fine)
            ("notes", "TEXT", ""),  # v0.3.0 - Staff notes for special requests
        ],
        # ...
    },

IMPORTANT:
  - Add new columns at the END of the list
  - Always include version comment: # v0.3.0 - Description
  - Use appropriate default values for existing rows


╔═══════════════════════════════════════════════════════════════════════════╗
║ SCENARIO 3: ADD AN INDEX TO EXISTING TABLE                               ║
╚═══════════════════════════════════════════════════════════════════════════╝

Step 1: Find the table in SCHEMA_DEFINITIONS
Step 2: Add to the "indexes" list
Step 3: Run migration script

Example - Speed up customer name searches:

    "orders": {
        "columns": [ ... ],
        "indexes": [
            ("ix_orders_id", ["id"]),
            ("ix_orders_order_number", ["order_number"]),

            # ⬇️ ADD NEW INDEX HERE
            ("ix_orders_customer_name", ["customer_name"]),  # v0.3.0 - Faster customer search
        ],
    },

MULTI-COLUMN INDEX (composite index):

    ("ix_orders_table_status", ["table_number", "status"]),  # Faster filtering by table+status


╔═══════════════════════════════════════════════════════════════════════════╗
║ SCENARIO 4: ADD A FOREIGN KEY CONSTRAINT                                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

Step 1: Find the table
Step 2: Add to "foreign_keys" list
Step 3: Run migration

Example:

    "order_items": {
        "columns": [ ... ],
        "indexes": [ ... ],
        "foreign_keys": [
            ("order_id", "orders", "id"),
            ("menu_item_id", "menu_items", "id"),

            # ⬇️ ADD NEW FOREIGN KEY
            ("waiter_id", "users", "id"),  # v0.3.0 - Track which waiter took order
        ],
    },

NOTE: SQLite has limited support for altering foreign keys on existing tables.
      Best to include foreign keys when creating NEW tables.


═══════════════════════════════════════════════════════════════════════════════
📖 QUICK REFERENCE: COLUMN DEFINITION FORMAT
═══════════════════════════════════════════════════════════════════════════════

Format: ("column_name", "SQL_TYPE", "CONSTRAINTS")

COMMON SQL TYPES:
  INTEGER               - Whole numbers (1, 2, 100, -5)
  VARCHAR(N)            - Text up to N characters
  TEXT                  - Unlimited text (for long descriptions, notes)
  BOOLEAN               - True/False (stored as 0/1 in SQLite)
  DECIMAL(10, 2)        - Decimal numbers with precision (e.g., 123.45)
  DATE                  - Date only (YYYY-MM-DD)
  DATETIME              - Date and time (YYYY-MM-DD HH:MM:SS)

COMMON CONSTRAINTS:
  PRIMARY KEY AUTOINCREMENT   - Auto-incrementing ID column
  NOT NULL                    - Field is required
  UNIQUE NOT NULL             - Must be unique across all rows and required
  DEFAULT 0                   - Default value if not specified
  DEFAULT 'active'            - Default string value
  DEFAULT CURRENT_TIMESTAMP   - Auto-set to current date/time on insert
  ""                          - No constraints (nullable, optional)

EXAMPLES:
  ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT")           # Primary key
  ("name", "VARCHAR(200)", "NOT NULL")                     # Required text
  ("email", "VARCHAR(200)", "UNIQUE NOT NULL")             # Must be unique
  ("phone", "VARCHAR(15)", "")                             # Optional
  ("points", "INTEGER", "DEFAULT 0")                       # Default to 0
  ("status", "VARCHAR(20)", "DEFAULT 'active' NOT NULL")   # Required with default
  ("price", "DECIMAL(10, 2)", "NOT NULL")                  # Money (e.g., 19.99)
  ("is_active", "BOOLEAN", "DEFAULT 1")                    # Boolean (1=true, 0=false)
  ("notes", "TEXT", "")                                    # Long text, optional
  ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP")  # Auto timestamp


═══════════════════════════════════════════════════════════════════════════════
⚠️  SQLITE LIMITATIONS & BEST PRACTICES
═══════════════════════════════════════════════════════════════════════════════

WHAT YOU CAN DO:
  ✅ Add new tables
  ✅ Add new columns to existing tables
  ✅ Add new indexes
  ✅ Add foreign keys to NEW tables

WHAT YOU CANNOT DO (SQLite limitations):
  ❌ Rename columns (workaround: add new column, copy data, keep old for compatibility)
  ❌ Drop columns (SQLite doesn't support ALTER TABLE DROP COLUMN)
  ❌ Add foreign keys to EXISTING tables (only on CREATE TABLE)
  ❌ Change column type (workaround: add new column with new type)

BEST PRACTICES:
  1. Always add version comment when adding columns: # v0.3.0 - Description
  2. Add new columns at END of existing column lists
  3. Use meaningful index names: ix_tablename_columnname
  4. Set appropriate DEFAULT values for new columns (existing rows will use it)
  5. Test on a database copy first for major changes
  6. Backup before running migrations in production


═══════════════════════════════════════════════════════════════════════════════
📚 VERSION HISTORY
═══════════════════════════════════════════════════════════════════════════════

v0.1.0 - Initial release
  - Core POS tables: categories, menu_items, orders, order_items, payments

v0.1.2 - Partial serving feature
  - Added: order_items.quantity_served column

v0.1.3 - Parcel feature
  - Added: order_items.is_parcel column (item-level parcel marking)

v0.2.0 - Inventory management & cash counter
  - Added: inventory_categories table
  - Added: inventory_items table
  - Added: inventory_transactions table
  - Added: daily_cash_counter table

v0.3.0 - [FUTURE] Customer loyalty, reservations, etc.
  - Add your future features here as comments for planning


═══════════════════════════════════════════════════════════════════════════════
🎨 ORGANIZATION STRUCTURE
═══════════════════════════════════════════════════════════════════════════════

Keep schema definitions organized by feature/module:

SCHEMA_DEFINITIONS = {
    # -------------------------------------------------------------------------
    # CORE POS TABLES (v0.1.0+)
    # -------------------------------------------------------------------------
    "categories": { ... },
    "menu_items": { ... },
    "orders": { ... },
    "order_items": { ... },
    "payments": { ... },

    # -------------------------------------------------------------------------
    # INVENTORY SYSTEM (v0.2.0)
    # -------------------------------------------------------------------------
    "inventory_categories": { ... },
    "inventory_items": { ... },
    "inventory_transactions": { ... },

    # -------------------------------------------------------------------------
    # CASH COUNTER SYSTEM (v0.2.0)
    # -------------------------------------------------------------------------
    "daily_cash_counter": { ... },

    # -------------------------------------------------------------------------
    # CUSTOMER LOYALTY (v0.3.0) - Example of adding new feature
    # -------------------------------------------------------------------------
    "customer_accounts": { ... },
    "loyalty_points": { ... },
}

This keeps related tables grouped together and makes the file easy to navigate.

"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from app.db.session import engine
from app.core.config import settings


# ════════════════════════════════════════════════════════════════════════════
# SCHEMA DEFINITIONS - Complete Target Schema
# ════════════════════════════════════════════════════════════════════════════
#
# This is the SINGLE SOURCE OF TRUTH for your database schema.
#
# When you add/modify anything here and run this script, it will:
#   1. Check what exists in the actual database
#   2. Compare to these definitions
#   3. Add only what's missing
#
# FORMAT:
#   "table_name": {
#       "columns": [
#           ("column_name", "SQL_TYPE", "CONSTRAINTS"),
#           ...
#       ],
#       "indexes": [                    # Optional
#           ("index_name", ["column1", "column2"]),
#           ...
#       ],
#       "foreign_keys": [               # Optional
#           ("fk_column", "ref_table", "ref_column"),
#           ...
#       ],
#   },
#
# ════════════════════════════════════════════════════════════════════════════

SCHEMA_DEFINITIONS = {

    # ═══════════════════════════════════════════════════════════════════════
    # CORE POS TABLES (v0.1.0+)
    # ═══════════════════════════════════════════════════════════════════════

    "categories": {
        "columns": [
            # Primary key - auto-incrementing ID
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),

            # Category name (unique, required) - e.g., "Coffee", "Snacks"
            ("name", "VARCHAR(100)", "UNIQUE NOT NULL"),

            # Timestamp - when category was created
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
        ],
        "indexes": [
            # Index on id (primary key, auto-indexed but explicit for clarity)
            ("ix_categories_id", ["id"]),

            # Index on name for faster lookups by category name
            ("ix_categories_name", ["name"]),
        ],
    },

    "menu_items": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("name", "VARCHAR(200)", "NOT NULL"),
            ("description", "VARCHAR(500)", ""),  # Optional description
            ("price", "INTEGER", "NOT NULL"),  # Price in paise (8000 = ₹80.00)
            ("category_id", "INTEGER", "NOT NULL"),  # Link to categories table
            ("is_vegetarian", "BOOLEAN", "DEFAULT 1"),  # 1=veg, 0=non-veg
            ("is_beverage", "BOOLEAN", "DEFAULT 0"),  # 1=beverage, 0=food
            ("is_available", "BOOLEAN", "DEFAULT 1"),  # Soft delete flag
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
            ("order_number", "VARCHAR(50)", "UNIQUE NOT NULL"),  # e.g., "ORD-20250101-0001"
            ("table_number", "INTEGER", "NOT NULL"),
            ("customer_name", "VARCHAR(200)", ""),  # Optional
            ("subtotal", "INTEGER", "NOT NULL"),  # Amount in paise before GST
            ("gst_amount", "INTEGER", "NOT NULL"),  # GST amount in paise
            ("total_amount", "INTEGER", "NOT NULL"),  # Final total in paise
            ("status", "VARCHAR(20)", "DEFAULT 'active' NOT NULL"),  # active/paid/canceled
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

            # Snapshot fields - preserve menu item details at order time
            ("menu_item_name", "VARCHAR(200)", "NOT NULL"),
            ("quantity", "INTEGER", "NOT NULL"),
            ("quantity_served", "INTEGER", "DEFAULT 0 NOT NULL"),  # v0.1.2 - Partial serving
            ("unit_price", "INTEGER", "NOT NULL"),  # Price in paise at order time
            ("subtotal", "INTEGER", "NOT NULL"),  # quantity * unit_price

            # Item flags
            ("is_beverage", "BOOLEAN", "DEFAULT 0"),  # Snapshot from menu_item
            ("is_served", "BOOLEAN", "DEFAULT 0"),  # Has this been served to customer?
            ("is_parcel", "BOOLEAN", "DEFAULT 0 NOT NULL"),  # v0.1.3 - Item-level parcel
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
            ("payment_method", "VARCHAR(20)", "NOT NULL"),  # cash/upi/card
            ("amount", "INTEGER", "NOT NULL"),  # Amount in paise
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
        ],
        "indexes": [
            ("ix_payments_id", ["id"]),
        ],
        "foreign_keys": [
            ("order_id", "orders", "id"),
        ],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # INVENTORY SYSTEM (v0.2.0)
    # ═══════════════════════════════════════════════════════════════════════

    "inventory_categories": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("name", "VARCHAR(100)", "UNIQUE NOT NULL"),  # e.g., "Dry Grocery", "Vegetables"
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME", ""),  # Nullable - set on updates
        ],
    },

    "inventory_items": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("name", "VARCHAR(200)", "NOT NULL"),  # e.g., "Milk", "Sugar", "Tomatoes"
            ("unit", "VARCHAR(20)", "NOT NULL"),  # e.g., "L", "kg", "pcs"
            ("current_quantity", "DECIMAL(10, 2)", "NOT NULL DEFAULT 0"),  # Current stock
            ("min_threshold", "DECIMAL(10, 2)", "NOT NULL DEFAULT 0"),  # Low stock alert level
            ("cost_per_unit", "DECIMAL(10, 2)", ""),  # Optional - for cost tracking
            ("category_id", "INTEGER", ""),  # Optional category
            ("is_active", "BOOLEAN", "NOT NULL DEFAULT 1"),  # Soft delete flag
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
            ("transaction_type", "VARCHAR(20)", "NOT NULL"),  # PURCHASE/USAGE/ADJUSTMENT
            ("quantity", "DECIMAL(10, 2)", "NOT NULL"),  # Positive or negative
            ("notes", "VARCHAR(500)", ""),  # Optional notes
            ("recorded_by", "VARCHAR(100)", "NOT NULL"),  # Staff name who recorded
            ("previous_quantity", "DECIMAL(10, 2)", "NOT NULL"),  # Quantity before transaction
            ("new_quantity", "DECIMAL(10, 2)", "NOT NULL"),  # Quantity after transaction
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

    # ═══════════════════════════════════════════════════════════════════════
    # CASH COUNTER SYSTEM (v0.2.0)
    # ═══════════════════════════════════════════════════════════════════════

    "daily_cash_counter": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("date", "DATE", "UNIQUE NOT NULL"),  # One record per day
            ("opening_balance", "DECIMAL(10, 2)", "NOT NULL"),  # Cash at start of day
            ("closing_balance", "DECIMAL(10, 2)", ""),  # Cash at end of day (nullable until closed)
            ("expected_closing", "DECIMAL(10, 2)", ""),  # Expected based on sales (nullable until closed)
            ("variance", "DECIMAL(10, 2)", ""),  # Difference: actual - expected
            ("notes", "VARCHAR(500)", ""),  # Notes about discrepancies
            ("opened_by", "VARCHAR(100)", "NOT NULL"),  # Staff who opened
            ("closed_by", "VARCHAR(100)", ""),  # Staff who closed (nullable until closed)
            ("verified_by", "VARCHAR(100)", ""),  # Owner who verified (nullable)
            ("opened_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP NOT NULL"),
            ("closed_at", "DATETIME", ""),  # When counter was closed
            ("verified_at", "DATETIME", ""),  # When owner verified
            ("is_verified", "BOOLEAN", "NOT NULL DEFAULT 0"),  # Owner verification status

            # v0.2 Patch - Denomination counting for opening balance
            ("opening_500s", "INTEGER", "NOT NULL DEFAULT 0"),  # Count of ₹500 notes at opening
            ("opening_200s", "INTEGER", "NOT NULL DEFAULT 0"),  # Count of ₹200 notes at opening
            ("opening_100s", "INTEGER", "NOT NULL DEFAULT 0"),  # Count of ₹100 notes at opening
            ("opening_50s", "INTEGER", "NOT NULL DEFAULT 0"),  # Count of ₹50 notes at opening
            ("opening_20s", "INTEGER", "NOT NULL DEFAULT 0"),  # Count of ₹20 notes at opening
            ("opening_10s", "INTEGER", "NOT NULL DEFAULT 0"),  # Count of ₹10 notes at opening

            # v0.2 Patch - Denomination counting for closing balance
            ("closing_500s", "INTEGER", ""),  # Count of ₹500 notes at closing (nullable until closed)
            ("closing_200s", "INTEGER", ""),  # Count of ₹200 notes at closing (nullable until closed)
            ("closing_100s", "INTEGER", ""),  # Count of ₹100 notes at closing (nullable until closed)
            ("closing_50s", "INTEGER", ""),  # Count of ₹50 notes at closing (nullable until closed)
            ("closing_20s", "INTEGER", ""),  # Count of ₹20 notes at closing (nullable until closed)
            ("closing_10s", "INTEGER", ""),  # Count of ₹10 notes at closing (nullable until closed)
        ],
        "indexes": [
            ("ix_daily_cash_counter_id", ["id"]),
            ("ix_daily_cash_counter_is_verified", ["is_verified"]),
        ],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # FUTURE FEATURES - Add new tables here
    # ═══════════════════════════════════════════════════════════════════════
    #
    # When adding new features, create a new section like this:
    #
    # # ───────────────────────────────────────────────────────────────────────
    # # CUSTOMER LOYALTY PROGRAM (v0.3.0)
    # # ───────────────────────────────────────────────────────────────────────
    #
    # "customer_accounts": {
    #     "columns": [
    #         ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
    #         ("phone", "VARCHAR(15)", "UNIQUE NOT NULL"),
    #         ("name", "VARCHAR(200)", "NOT NULL"),
    #         ("email", "VARCHAR(200)", ""),
    #         ("points", "INTEGER", "DEFAULT 0"),
    #         ("tier", "VARCHAR(20)", "DEFAULT 'bronze'"),  # bronze/silver/gold
    #         ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    #         ("updated_at", "DATETIME", ""),
    #     ],
    #     "indexes": [
    #         ("ix_customer_accounts_id", ["id"]),
    #         ("ix_customer_accounts_phone", ["phone"]),
    #     ],
    # },
    #
    # "loyalty_transactions": {
    #     "columns": [
    #         ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
    #         ("customer_id", "INTEGER", "NOT NULL"),
    #         ("order_id", "INTEGER", ""),  # Optional - links to order if points from purchase
    #         ("points_change", "INTEGER", "NOT NULL"),  # Positive=earned, Negative=redeemed
    #         ("description", "VARCHAR(200)", "NOT NULL"),
    #         ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    #     ],
    #     "indexes": [
    #         ("ix_loyalty_transactions_id", ["id"]),
    #         ("ix_loyalty_transactions_customer_id", ["customer_id"]),
    #     ],
    #     "foreign_keys": [
    #         ("customer_id", "customer_accounts", "id"),
    #         ("order_id", "orders", "id"),
    #     ],
    # },
    #
    # ═══════════════════════════════════════════════════════════════════════
}


# ════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

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
    """Create a table with all its columns, indexes, and foreign keys."""
    columns_sql = []
    foreign_keys_sql = []

    # Build column definitions
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
    join_str = ',\n    '
    create_sql = f"CREATE TABLE {table_name} (\n    {join_str.join(all_constraints)}\n)"

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


# ════════════════════════════════════════════════════════════════════════════
# MIGRATION LOGIC
# ════════════════════════════════════════════════════════════════════════════

def migrate():
    """
    Comprehensive database migration.

    Checks ALL schema definitions and applies missing:
    - Tables
    - Columns
    - Indexes

    This is the main function that does all the work.
    """
    print("=" * 80)
    print("  Lily Cafe POS - Comprehensive Database Migration")
    print("=" * 80)
    print(f"Database: {settings.DATABASE_URL}")
    print()

    changes_applied = 0

    with engine.connect() as conn:
        # Get list of existing tables for quick reference
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        print("📊 SCHEMA VALIDATION & MIGRATION")
        print("-" * 80)
        print()

        # Process each table in schema definition
        for table_name, table_def in SCHEMA_DEFINITIONS.items():
            print(f"Checking table: {table_name}")

            # ────────────────────────────────────────────────────────────────
            # 1. CHECK TABLE EXISTS
            # ────────────────────────────────────────────────────────────────
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

            # ────────────────────────────────────────────────────────────────
            # 2. CHECK COLUMNS
            # ────────────────────────────────────────────────────────────────
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

            # ────────────────────────────────────────────────────────────────
            # 3. CHECK INDEXES
            # ────────────────────────────────────────────────────────────────
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

        # ════════════════════════════════════════════════════════════════════
        # SUMMARY
        # ════════════════════════════════════════════════════════════════════
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


# ════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

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
