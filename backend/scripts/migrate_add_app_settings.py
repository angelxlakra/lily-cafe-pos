#!/usr/bin/env python3
# backend/scripts/migrate_add_app_settings.py
"""
Migration: Create app_settings table and seed defaults from env vars.

Idempotent — safe to run multiple times. Skips keys that already exist.

Usage:
    uv run python backend/scripts/migrate_add_app_settings.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # On production (Fly.io), env vars are already injected as secrets

from sqlalchemy import inspect
from app.db.session import engine, SessionLocal
from app.db.base import Base  # ensures AppSetting is in metadata
from app.models.settings_model import AppSetting
from app.core.settings_store import DEFAULTS


def get_seed_values() -> dict[str, str]:
    """Build seed dict: prefer current env var, fall back to DEFAULTS."""
    env_map = {
        "restaurant.name": "RESTAURANT_NAME",
        "restaurant.address_line1": "RESTAURANT_ADDRESS_LINE1",
        "restaurant.address_line2": "RESTAURANT_ADDRESS_LINE2",
        "restaurant.phone": "RESTAURANT_PHONE",
        "restaurant.email": "RESTAURANT_EMAIL",
        "restaurant.gstin": "RESTAURANT_GSTIN",
        "restaurant.fssai": "RESTAURANT_FSSAI",
        "app.max_tables": "MAX_TABLES",
        "app.gst_rate": "GST_RATE",
        "app.timezone": "TIMEZONE",
        "app.token_expiry_hours": "TOKEN_EXPIRY_HOURS",
        "receipt.paper_size": "RECEIPT_PAPER_SIZE",
        "receipt.google_review_url": "GOOGLE_REVIEW_URL",
        "receipt.feedback_form_url": "FEEDBACK_FORM_URL",
        "smtp.enabled": "SMTP_ENABLED",
        "smtp.host": "SMTP_HOST",
        "smtp.port": "SMTP_PORT",
        "smtp.username": "SMTP_USERNAME",
        "smtp.sender_email": "SMTP_SENDER_EMAIL",
        "smtp.report_emails": "INVENTORY_REPORT_EMAILS",
    }
    seed: dict[str, str] = {}
    for key, env_var in env_map.items():
        env_value = os.getenv(env_var)
        seed[key] = env_value if env_value is not None else DEFAULTS[key]
    return seed


def main():
    print("=== migrate_add_app_settings ===")

    # Create table if it doesn't exist
    inspector = inspect(engine)
    if "app_settings" not in inspector.get_table_names():
        print("Creating app_settings table...")
        Base.metadata.create_all(bind=engine, tables=[AppSetting.__table__])
        print("  ✓ Table created")
    else:
        print("  ✓ Table already exists")

    # Seed missing keys
    db = SessionLocal()
    try:
        seed = get_seed_values()
        inserted = 0
        skipped = 0
        for key, value in seed.items():
            existing = db.query(AppSetting).filter(AppSetting.key == key).first()
            if existing is None:
                db.add(AppSetting(key=key, value=value))
                inserted += 1
                print(f"  + {key} = {value!r}")
            else:
                skipped += 1
        db.commit()
        print(f"\nDone. Inserted: {inserted}, Skipped (already existed): {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
