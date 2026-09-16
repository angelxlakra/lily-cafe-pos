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


def ensure_order_columns(bind=None) -> list[str]:
    """
    Add any missing columns to the orders table.

    Idempotent — safe to call on every startup. Returns the names of the
    columns that were actually added.
    """
    bind = bind or engine
    inspector = inspect(bind)

    if "orders" not in inspector.get_table_names():
        return []

    existing = {col["name"] for col in inspector.get_columns("orders")}
    added = []

    with bind.connect() as conn:
        for name, ddl_type in _ORDER_ADDED_COLUMNS.items():
            if name in existing:
                continue
            conn.execute(text(f"ALTER TABLE orders ADD COLUMN {name} {ddl_type}"))
            added.append(name)
        if added:
            conn.commit()

    return added


def init_db():
    """
    Initialize database by creating all tables.
    Should be called on application startup.
    """
    from app.models import models  # noqa
    from app.models.settings_model import AppSetting  # noqa - ensures app_settings table is created

    Base.metadata.create_all(bind=engine)

    # create_all() does not alter existing tables, so bring older databases
    # up to date with the columns added to `orders` since it shipped.
    ensure_order_columns(engine)
