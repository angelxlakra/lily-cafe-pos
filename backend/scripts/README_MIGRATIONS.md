# Database Migrations Guide

## Overview

Lily Cafe POS uses a **single comprehensive migration script** (`migrate_database.py`) that maintains the complete database schema. This approach is simpler and more maintainable than having multiple separate migration scripts.

## Quick Start

### Running Migrations

To ensure your database is up-to-date, simply run:

```bash
cd backend
uv run python scripts/migrate_database.py
```

This script:
- ✅ Checks ALL tables, columns, and indexes
- ✅ Applies only missing changes
- ✅ Safe to run multiple times (idempotent)
- ✅ Shows detailed progress and summary

### When to Run Migrations

Run migrations after:
- Pulling new code from the repository
- Checking out a different branch
- Upgrading to a new version
- Fresh database setup

## How It Works

### Schema-Driven Approach

The `migrate_database.py` script contains the **complete target schema** for your database in the `SCHEMA_DEFINITIONS` dictionary. When you run it:

1. **Checks Tables**: Verifies each table exists, creates if missing
2. **Checks Columns**: Verifies all columns exist in each table, adds if missing
3. **Checks Indexes**: Verifies all indexes exist, creates if missing
4. **Reports**: Shows what was changed and current schema status

### Example Output

```
📊 SCHEMA VALIDATION & MIGRATION
--------------------------------------------------------------------------------

Checking table: categories
  ✓ All columns present
  ✓ All indexes present

Checking table: order_items
  ⚠️  Missing 1 column(s) - adding...
    ✓ Added column 'order_items.quantity_served'
  ✓ All indexes present

================================================================================
✅ MIGRATION COMPLETED SUCCESSFULLY!
   Applied 1 schema change(s)
```

## Adding New Migrations

When the schema needs to evolve (new features, new columns, etc.), update the migration script:

### Adding a New Table

Edit `scripts/migrate_database.py` and add to `SCHEMA_DEFINITIONS`:

```python
SCHEMA_DEFINITIONS = {
    # ... existing tables ...

    "customer_loyalty": {
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("phone", "VARCHAR(15)", "UNIQUE NOT NULL"),
            ("name", "VARCHAR(200)", "NOT NULL"),
            ("points", "INTEGER", "DEFAULT 0"),
            ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
        ],
        "indexes": [
            ("ix_customer_loyalty_id", ["id"]),
            ("ix_customer_loyalty_phone", ["phone"]),
        ],
    },
}
```

### Adding a New Column to Existing Table

Find the table in `SCHEMA_DEFINITIONS` and add the column:

```python
"order_items": {
    "columns": [
        # ... existing columns ...
        ("discount_amount", "INTEGER", "DEFAULT 0"),  # New column
    ],
    # ...
},
```

### Adding a New Index

Find the table and add to the `indexes` list:

```python
"orders": {
    "columns": [ ... ],
    "indexes": [
        # ... existing indexes ...
        ("ix_orders_customer_name", ["customer_name"]),  # New index
    ],
},
```

### That's It!

After updating `SCHEMA_DEFINITIONS`:

1. Run the script: `uv run python scripts/migrate_database.py`
2. The script automatically detects and applies changes
3. Commit both the script and your model changes

## Version History

### Current Schema (v0.2.0)

**Core POS Tables (v0.1.0+):**
- `categories` - Menu categories
- `menu_items` - Menu items with pricing
- `orders` - Customer orders
- `order_items` - Order line items
- `payments` - Payment records

**Enhanced Columns:**
- `order_items.quantity_served` (v0.1.2) - Partial serving support
- `order_items.is_parcel` (v0.1.3) - Item-level parcel marking

**Inventory System (v0.2.0):**
- `inventory_categories` - Inventory item categories
- `inventory_items` - Inventory items with quantities
- `inventory_transactions` - Purchase/usage/adjustment tracking

**Cash Counter (v0.2.0):**
- `daily_cash_counter` - Daily cash reconciliation

## Legacy Migration Scripts

The following old migration scripts are **deprecated** and should not be used:

- ❌ `migrate_add_quantity_served.py` - Use `migrate_database.py` instead
- ❌ `migrate_move_is_parcel_to_order_items.py` - Use `migrate_database.py` instead
- ❌ `migrate_v01x_to_v020.py` - Use `migrate_database.py` instead

These files are kept for historical reference only.

## Troubleshooting

### Script Reports No Changes But Feature Doesn't Work

1. **Check Backend Logs**: Look for database errors
2. **Verify Models Match Schema**: Ensure SQLAlchemy models match `SCHEMA_DEFINITIONS`
3. **Restart Backend**: `uv run uvicorn app.main:app --reload`

### Migration Fails with Error

```bash
# 1. Check database isn't locked
lsof backend/restaurant.db

# 2. Verify database integrity
sqlite3 backend/restaurant.db "PRAGMA integrity_check;"

# 3. Check permissions
ls -l backend/restaurant.db
```

### Need to Rollback

If migration causes issues:

1. **Stop backend server**
2. **Restore from backup**: `cp restaurant_backup.db restaurant.db`
3. **Report issue with error logs**

## Best Practices

### Always Backup Before Migrations

```bash
# Create timestamped backup
cp backend/restaurant.db backend/restaurant_backup_$(date +%Y%m%d_%H%M%S).db
```

### Test Migrations on Copy First

```bash
# Copy production database
cp restaurant.db restaurant_test.db

# Test migration on copy
DATABASE_URL=sqlite:///./restaurant_test.db uv run python scripts/migrate_database.py

# If successful, run on production
uv run python scripts/migrate_database.py
```

### Keep Schema Definition Organized

- Group related tables together
- Add comments for feature versions
- Use consistent column ordering
- Document breaking changes

### Commit Schema and Code Together

When adding features:
1. Update SQLAlchemy models
2. Update `SCHEMA_DEFINITIONS` in migration script
3. Commit both changes together
4. Document in CHANGELOG.md

## Safety Features

The migration script is designed to be safe:

- ✅ **Idempotent**: Safe to run multiple times
- ✅ **Non-destructive**: Never drops tables or columns
- ✅ **Checks First**: Validates before making changes
- ✅ **Atomic Commits**: Each change is committed separately
- ✅ **Error Handling**: Detailed error messages and rollback guidance

## FAQ

**Q: Do I need to run migrations on a fresh database?**
A: No, the application will create tables on startup. But running migrations ensures everything is correct.

**Q: Can I have multiple migrations for different features?**
A: No need! Just add to `SCHEMA_DEFINITIONS` and run the single script.

**Q: What if I need to rename a column?**
A: SQLite doesn't support column renaming easily. Best approach:
1. Add new column
2. Copy data in application code
3. Remove references to old column
4. Document as breaking change

**Q: How do I verify migration was successful?**
A: The script shows a summary. Also check backend startup logs for errors.

**Q: Should I run migrations in production?**
A: Yes, but always backup first! See deployment guide for production procedures.

## Related Documentation

- [Migration Guide v0.2.0](../../docs/MIGRATION_V0.2.md) - Upgrading from v0.1.x
- [Database Schema](../../docs/DATABASE_SCHEMA.md) - Complete schema documentation
- [Deployment Guide](../../docs/DEPLOYMENT.md) - Production deployment procedures
