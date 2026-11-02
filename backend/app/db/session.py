"""
Database connection and session management for Lily Cafe POS.
Uses SQLAlchemy with SQLite for local data storage.
"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create database engine
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all database models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.
    Used in FastAPI route dependencies for automatic session management.

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Columns added to `orders` after the table already shipped. Kept here so both
# init_db() and scripts/migrate_add_order_columns.py apply them the same way.
# create_all() only creates missing *tables*, never missing columns.
_ORDER_ADDED_COLUMNS = {
    "canceled_at": "DATETIME",
    "canceled_by": "VARCHAR(50)",
    "cancel_reason": "VARCHAR(255)",
    "last_edited_at": "DATETIME",
    "last_edited_by": "VARCHAR(50)",
    "edit_count": "INTEGER DEFAULT 0 NOT NULL",
    "notes": "VARCHAR(500)",
}


# Columns added to inventory tables after they shipped.
_INVENTORY_ADDED_COLUMNS = {
    "inventory_categories": {"sort_order": "INTEGER DEFAULT 0 NOT NULL"},
    "inventory_items": {
        "sort_order": "INTEGER DEFAULT 0 NOT NULL",
        "count_mode": "VARCHAR(10) DEFAULT 'number' NOT NULL",
        "pack_size": "NUMERIC(10, 3)",
        "pack_unit": "VARCHAR(20)",
        "needs_setup": "BOOLEAN DEFAULT 0 NOT NULL",
        # vendors is created by create_all() before this runs.
        "default_vendor_id": "INTEGER REFERENCES vendors(id)",
        "brand": "VARCHAR(100)",
    },
    "inventory_transactions": {
        "total_amount": "NUMERIC(10, 2)",
        # vendors is created by create_all() before this runs.
        "vendor_id": "INTEGER REFERENCES vendors(id)",
        "pack_count": "NUMERIC(10, 3)",
        "unit": "VARCHAR(20)",
        "price_status": "VARCHAR(10)",
        "price_reviewed_at": "DATETIME",
    },
}


# Coins, added after the cash counter shipped with notes only.
_CASH_ADDED_COLUMNS = {
    "daily_cash_counter": {
        **{f"opening_{d}s": "INTEGER DEFAULT 0 NOT NULL" for d in (5, 2, 1)},
        **{f"closing_{d}s": "INTEGER" for d in (5, 2, 1)},
    },
}


def _ensure_columns(bind, table: str, columns: dict[str, str]) -> list[str]:
    """Add any of ``columns`` missing from ``table``. Idempotent."""
    inspector = inspect(bind)
    if table not in inspector.get_table_names():
        return []

    existing = {col["name"] for col in inspector.get_columns(table)}
    added = []

    with bind.connect() as conn:
        for name, ddl_type in columns.items():
            if name in existing:
                continue
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl_type}"))
            added.append(name)
        if added:
            conn.commit()

    return added


def ensure_order_columns(bind=None) -> list[str]:
    """
    Add any missing columns to the orders table.

    Idempotent — safe to call on every startup. Returns the names of the
    columns that were actually added.
    """
    return _ensure_columns(bind or engine, "orders", _ORDER_ADDED_COLUMNS)


def ensure_inventory_columns(bind=None) -> list[str]:
    """Add columns introduced after the inventory tables shipped. Idempotent."""
    bind = bind or engine
    added = []
    for table, columns in _INVENTORY_ADDED_COLUMNS.items():
        added += _ensure_columns(bind, table, columns)
    _backfill_transaction_units(bind)
    return added


def _backfill_transaction_units(bind) -> None:
    """Give rows from before transactions recorded a unit their item's current one.

    That is the unit everything already assumed they were in, so nothing that
    worked before changes; from here on each new row records its own.
    """
    tables = set(inspect(bind).get_table_names())
    if not {"inventory_transactions", "inventory_items"} <= tables:
        return
    with bind.begin() as conn:
        conn.execute(text(
            "UPDATE inventory_transactions SET unit = "
            "(SELECT unit FROM inventory_items WHERE inventory_items.id = inventory_transactions.item_id) "
            "WHERE unit IS NULL"
        ))


def ensure_cash_columns(bind=None) -> list[str]:
    """Add the coin columns to older cash counters. Idempotent."""
    bind = bind or engine
    added = []
    for table, columns in _CASH_ADDED_COLUMNS.items():
        added += _ensure_columns(bind, table, columns)
    return added


def ensure_costing_made_items(bind=None) -> bool:
    """Let a costing belong to a kitchen-made inventory item instead of a menu item.

    SQLite can't drop NOT NULL, so an older dish_costings is rebuilt with the
    documented procedure: build the new table beside it, copy, drop the old,
    rename the new. The old table is never renamed, which would make SQLite
    rewrite the foreign key in dish_costing_ingredients. Idempotent; returns
    whether it rebuilt.
    """
    from sqlalchemy.schema import CreateTable
    from app.models.costing_models import DishCosting

    bind = bind or engine
    if "dish_costings" not in inspect(bind).get_table_names():
        return False
    old = {r[1]: r[3] for r in _table_info(bind, "dish_costings")}
    if "inventory_item_id" in old and not old["menu_item_id"]:
        return False

    table = DishCosting.__table__
    ddl = str(CreateTable(table).compile(dialect=bind.dialect)).replace(
        "CREATE TABLE dish_costings", "CREATE TABLE dish_costings_new", 1
    )
    shared = ", ".join(c.name for c in table.columns if c.name in old)
    conn = bind.connect()
    try:
        # A no-op inside a transaction, so it goes first.
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
        conn.exec_driver_sql("DROP TABLE IF EXISTS dish_costings_new")
        conn.exec_driver_sql(ddl)
        conn.exec_driver_sql(f"INSERT INTO dish_costings_new ({shared}) SELECT {shared} FROM dish_costings")
        conn.exec_driver_sql("DROP TABLE dish_costings")
        conn.exec_driver_sql("ALTER TABLE dish_costings_new RENAME TO dish_costings")
        for index in table.indexes:
            index.create(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        conn.close()
    return True


def _table_info(bind, table: str):
    with bind.connect() as conn:
        return conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()


def init_db():
    """
    Initialize database by creating all tables.
    Should be called on application startup.
    """
    from app.models import models  # noqa
    from app.models.settings_model import AppSetting  # noqa - ensures app_settings table is created
    from app.models.digest_models import DailyDigest  # noqa - ensures daily_digests table is created
    from app.models.costing_models import DishCosting, DishCostingIngredient  # noqa - ensures dish costing tables are created

    Base.metadata.create_all(bind=engine)

    # create_all() does not alter existing tables, so bring older databases
    # up to date with the columns added to `orders` since it shipped.
    ensure_order_columns(engine)
    ensure_inventory_columns(engine)
    ensure_costing_made_items(engine)
    ensure_cash_columns(engine)
