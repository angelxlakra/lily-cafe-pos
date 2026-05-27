# backend/app/core/settings_store.py
"""
In-memory cache for operator-configurable application settings.

Settings are stored in the `app_settings` DB table as key/value strings.
The cache is loaded at startup and refreshed on every write — reads are
zero-latency dict lookups with no DB queries per request.

Usage:
    from app.core import settings_store

    name = settings_store.get("restaurant.name")
    rate = settings_store.get_float("app.gst_rate", 5.0)
    settings_store.set_many({"restaurant.name": "New Name"}, db)
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

# ============================================================================
# Defaults — used when a key has no row in DB or cache is not yet loaded
# ============================================================================

DEFAULTS: dict[str, str] = {
    "restaurant.name": "Lily Cafe by Mary's Kitchen",
    "restaurant.address_line1": "Shop 123, Main Street",
    "restaurant.address_line2": "City, State - 123456",
    "restaurant.phone": "+91-1234567890",
    "restaurant.email": "info@lilycafe.com",
    "restaurant.gstin": "29ABCDE1234F1Z5",
    "restaurant.fssai": "29ABCDE1234F1Z5",
    "app.max_tables": "15",
    "app.gst_rate": "5.0",
    "app.timezone": "Asia/Kolkata",
    "app.token_expiry_hours": "24",
    "receipt.paper_size": "80mm",
    "receipt.google_review_url": "https://g.page/r/your-business-review",
    "receipt.feedback_form_url": "https://forms.gle/your-feedback-form",
    "smtp.enabled": "false",
    "smtp.host": "smtp.gmail.com",
    "smtp.port": "587",
    "smtp.username": "",
    "smtp.sender_email": "",
    "smtp.report_emails": "",
}

KNOWN_KEYS: frozenset[str] = frozenset(DEFAULTS.keys())

# Module-level cache — populated by load(), read by get*()
_cache: dict[str, str] = {}


# ============================================================================
# Public API
# ============================================================================

def load(db: Session) -> None:
    """Load all settings from DB into the in-memory cache.

    Called at application startup (after init_db) and after every write.
    Falls back to DEFAULTS for keys missing from DB.
    """
    global _cache
    try:
        from app.models.settings_model import AppSetting
        rows = db.query(AppSetting).all()
        new_cache = dict(DEFAULTS)
        for row in rows:
            if row.value is not None:
                new_cache[row.key] = row.value
        _cache = new_cache
    except Exception:
        # Table may not exist yet on very first boot — use defaults
        _cache = dict(DEFAULTS)


def get(key: str, default: str = "") -> str:
    """Return cached value for key, falling back to DEFAULTS then default."""
    if _cache:
        return _cache.get(key, DEFAULTS.get(key, default))
    return DEFAULTS.get(key, default)


def get_int(key: str, default: int = 0) -> int:
    """Return cached value coerced to int."""
    return int(get(key, str(default)))


def get_float(key: str, default: float = 0.0) -> float:
    """Return cached value coerced to float."""
    return float(get(key, str(default)))


def get_bool(key: str, default: bool = False) -> bool:
    """Return cached value coerced to bool. Truthy strings: 'true', '1', 'yes'."""
    return get(key, "true" if default else "false").lower() in ("true", "1", "yes")


def set_many(updates: dict[str, str], db: Session) -> None:
    """Persist a dict of key->value updates to DB and reload the cache.

    Existing rows are updated; new keys are inserted.
    Immediately refreshes _cache so changes take effect for all
    subsequent requests without a server restart.
    """
    from app.models.settings_model import AppSetting

    for key, value in updates.items():
        row = db.query(AppSetting).filter(AppSetting.key == key).first()
        if row:
            row.value = value
            row.updated_at = datetime.now(timezone.utc)
        else:
            db.add(AppSetting(key=key, value=value, updated_at=datetime.now(timezone.utc)))
    db.commit()
    load(db)
