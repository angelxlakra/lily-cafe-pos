# Settings Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move non-secret env vars into a DB-backed key/value store and expose them through an owner-only Settings page in the admin UI.

**Architecture:** A new `app_settings` SQLite table stores settings as key/value strings. A module-level cache (`settings_store.py`) is loaded at startup and on every write — reads are zero-latency dict lookups. The existing `config.py` is slimmed to secrets only; all consumer files are updated to call `settings_store.get(...)` instead of `settings.*`.

**Tech Stack:** FastAPI + SQLAlchemy (backend), React + TanStack Query + sonner toasts (frontend), manual migration script (no Alembic), `uv run` for all Python commands.

---

## File Map

### New Files
| Path | Purpose |
|------|---------|
| `backend/app/models/settings_model.py` | `AppSetting` SQLAlchemy model |
| `backend/app/core/settings_store.py` | In-memory cache + DB read/write |
| `backend/app/api/v1/endpoints/settings.py` | GET/PUT `/api/v1/settings` (owner-only) |
| `backend/scripts/migrate_add_app_settings.py` | Create table + seed from env vars |
| `backend/tests/test_settings.py` | Tests for store + API |
| `frontend/src/api/settings.ts` | TanStack Query hooks |
| `frontend/src/pages/SettingsPage.tsx` | Owner settings UI |

### Modified Files
| Path | Change |
|------|--------|
| `backend/app/db/base.py` | Import `AppSetting` for metadata registration |
| `backend/app/core/config.py` | Remove non-secret fields |
| `backend/app/main.py` | Call `settings_store.load(db)` in startup |
| `backend/app/api/v1/router.py` | Register `/settings` router |
| `backend/app/api/v1/endpoints/config.py` | Read from `settings_store` |
| `backend/app/api/v1/endpoints/admin.py` | `MAX_TABLES` → `settings_store` |
| `backend/app/api/v1/endpoints/auth.py` | `TOKEN_EXPIRY_HOURS` → `settings_store` |
| `backend/app/api/v1/endpoints/orders.py` | `RECEIPT_PAPER_SIZE` → `settings_store` |
| `backend/app/api/v1/endpoints/inventory.py` | `SMTP_ENABLED` → `settings_store` |
| `backend/app/core/security.py` | `TOKEN_EXPIRY_HOURS` → `settings_store` |
| `backend/app/crud/crud.py` | `GST_RATE` → `settings_store` |
| `backend/app/utils/pdf_generator.py` | Restaurant/GST/timezone → `settings_store` |
| `backend/app/utils/printer.py` | Restaurant/GST/receipt fields → `settings_store` |
| `backend/app/utils/chit_generator.py` | `RECEIPT_PAPER_SIZE` → `settings_store` |
| `backend/app/utils/email_sender.py` | SMTP/restaurant fields → `settings_store` |
| `backend/app/schemas/schemas.py` | Add `SettingsResponse` + `SettingsUpdate` |
| `backend/tests/conftest.py` | Add `owner_token`, `owner_headers`, `loaded_settings_store` fixtures |
| `frontend/src/main.tsx` | Add `/admin/settings` route |
| `frontend/src/components/Sidebar.tsx` | Add Settings nav item (owner-only) |

---

## Task 1: AppSetting model

**Files:**
- Create: `backend/app/models/settings_model.py`
- Modify: `backend/app/db/base.py`

- [ ] **Step 1: Create the model file**

```python
# backend/app/models/settings_model.py
"""SQLAlchemy model for app_settings key/value store."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.db.session import Base


class AppSetting(Base):
    """Key/value store for operator-configurable application settings."""

    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True, nullable=False)
    value = Column(String(2000), nullable=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
```

- [ ] **Step 2: Register AppSetting in db/base.py**

In `backend/app/db/base.py`, add the import so `Base.metadata.create_all()` picks up the new table:

```python
"""
Import all models here to ensure they are registered with SQLAlchemy Base.
This allows Alembic migrations to detect all models.
"""

from app.db.session import Base  # noqa
from app.models.models import (  # noqa
    Category,
    MenuItem,
    Order,
    OrderItem,
    Payment,
    OrderStatus,
    PaymentMethod,
)
from app.models.inventory_models import (  # noqa
    InventoryCategory,
    InventoryItem,
    InventoryTransaction,
    TransactionType,
)
from app.models.cash_models import DailyCashCounter  # noqa
from app.models.settings_model import AppSetting  # noqa

__all__ = [
    "Base",
    "Category",
    "MenuItem",
    "Order",
    "OrderItem",
    "Payment",
    "OrderStatus",
    "PaymentMethod",
    "InventoryCategory",
    "InventoryItem",
    "InventoryTransaction",
    "TransactionType",
    "DailyCashCounter",
    "AppSetting",
]
```

- [ ] **Step 3: Verify import works**

```bash
cd backend && uv run python -c "from app.models.settings_model import AppSetting; print('OK', AppSetting.__tablename__)"
```

Expected: `OK app_settings`

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/settings_model.py backend/app/db/base.py
git commit -m "feat: add AppSetting model for key/value settings store"
```

---

## Task 2: Settings store

**Files:**
- Create: `backend/app/core/settings_store.py`

- [ ] **Step 1: Write the failing tests first**

Create `backend/tests/test_settings.py` with store tests:

```python
# backend/tests/test_settings.py
"""Tests for the settings store and settings API endpoints."""

import pytest
from app.core import settings_store
from app.models.settings_model import AppSetting


# ============================================================================
# Settings Store Tests
# ============================================================================

def test_get_returns_default_when_cache_empty():
    """get() returns the built-in default when cache is not loaded."""
    settings_store._cache = {}
    assert settings_store.get("restaurant.name") == "Lily Cafe by Mary's Kitchen"
    assert settings_store.get("nonexistent.key", "fallback") == "fallback"


def test_load_populates_cache_from_db(test_db):
    """load() reads rows from DB into _cache; missing keys use DEFAULTS."""
    test_db.add(AppSetting(key="restaurant.name", value="My Cafe"))
    test_db.commit()

    settings_store.load(test_db)

    assert settings_store.get("restaurant.name") == "My Cafe"
    # Keys not in DB fall back to DEFAULTS
    assert settings_store.get("app.gst_rate") == "5.0"


def test_load_with_empty_db_uses_defaults(test_db):
    """load() with no rows in DB results in cache equal to DEFAULTS."""
    settings_store.load(test_db)
    for key, default_value in settings_store.DEFAULTS.items():
        assert settings_store.get(key) == default_value


def test_get_int(test_db):
    """get_int() converts string value to int."""
    settings_store._cache = {"app.max_tables": "20"}
    assert settings_store.get_int("app.max_tables", 15) == 20


def test_get_float(test_db):
    """get_float() converts string value to float."""
    settings_store._cache = {"app.gst_rate": "12.5"}
    assert settings_store.get_float("app.gst_rate", 5.0) == 12.5


def test_get_bool_true():
    """get_bool() returns True for 'true'."""
    settings_store._cache = {"smtp.enabled": "true"}
    assert settings_store.get_bool("smtp.enabled", False) is True


def test_get_bool_false():
    """get_bool() returns False for 'false'."""
    settings_store._cache = {"smtp.enabled": "false"}
    assert settings_store.get_bool("smtp.enabled", True) is False


def test_set_many_writes_to_db_and_reloads(test_db):
    """set_many() persists values to DB and refreshes the cache."""
    settings_store.load(test_db)  # start with defaults

    settings_store.set_many({"restaurant.name": "New Name", "app.max_tables": "25"}, test_db)

    # Cache is updated immediately
    assert settings_store.get("restaurant.name") == "New Name"
    assert settings_store.get("app.max_tables") == "25"

    # Values are persisted in DB
    row = test_db.query(AppSetting).filter(AppSetting.key == "restaurant.name").first()
    assert row is not None
    assert row.value == "New Name"


def test_set_many_updates_existing_row(test_db):
    """set_many() updates an existing row rather than inserting a duplicate."""
    test_db.add(AppSetting(key="restaurant.name", value="Old Name"))
    test_db.commit()
    settings_store.load(test_db)

    settings_store.set_many({"restaurant.name": "Updated Name"}, test_db)

    rows = test_db.query(AppSetting).filter(AppSetting.key == "restaurant.name").all()
    assert len(rows) == 1
    assert rows[0].value == "Updated Name"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && uv run pytest tests/test_settings.py -v -k "store" 2>&1 | head -30
```

Expected: `ImportError` or `ModuleNotFoundError` — `settings_store` doesn't exist yet.

- [ ] **Step 3: Create settings_store.py**

```python
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
from typing import Optional
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
    """Persist a dict of key→value updates to DB and reload the cache.

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
```

- [ ] **Step 4: Run store tests — all should pass**

```bash
cd backend && uv run pytest tests/test_settings.py -v -k "store or load or get or set_many or bool or int or float"
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/settings_store.py backend/tests/test_settings.py
git commit -m "feat: add settings_store in-memory cache with DB persistence"
```

---

## Task 3: Migration script

**Files:**
- Create: `backend/scripts/migrate_add_app_settings.py`

- [ ] **Step 1: Create the migration script**

```python
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

from dotenv import load_dotenv
load_dotenv()

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
```

- [ ] **Step 2: Run the migration script locally**

```bash
cd /path/to/project && uv run python backend/scripts/migrate_add_app_settings.py
```

Expected output:
```
=== migrate_add_app_settings ===
  ✓ Table created  (or "already exists")
  + restaurant.name = 'Lily Cafe by Mary's Kitchen'
  ... (one line per inserted key)
Done. Inserted: 21, Skipped (already existed): 0
```

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/migrate_add_app_settings.py
git commit -m "feat: add migration script to create and seed app_settings table"
```

---

## Task 4: Update startup to load settings

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Update the startup event in main.py**

Replace the existing `startup_event` function:

```python
# In backend/app/main.py, replace the startup_event function:

@app.on_event("startup")
def startup_event():
    """Initialize database and load settings cache on application startup."""
    init_db()
    # Load settings from DB into the in-memory cache.
    # init_db() runs first so the app_settings table is guaranteed to exist.
    from app.db.session import SessionLocal
    from app.core import settings_store
    db = SessionLocal()
    try:
        settings_store.load(db)
    finally:
        db.close()
```

Also add the import at the top of `main.py` (it's already `from app.db.session import init_db` — no change needed there).

- [ ] **Step 2: Verify the app starts without error**

```bash
cd backend && uv run python -c "
from app.main import app
from app.core import settings_store
print('App imported OK')
print('restaurant.name default:', settings_store.get('restaurant.name'))
"
```

Expected:
```
App imported OK
restaurant.name default: Lily Cafe by Mary's Kitchen
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: load settings_store from DB at application startup"
```

---

## Task 5: Settings schemas + API endpoint + router registration

**Files:**
- Modify: `backend/app/schemas/schemas.py`
- Create: `backend/app/api/v1/endpoints/settings.py`
- Modify: `backend/app/api/v1/router.py`

- [ ] **Step 1: Add schemas to schemas.py**

At the end of `backend/app/schemas/schemas.py`, after the `AppConfig` class, add:

```python
# ============================================================================
# Settings Schemas
# ============================================================================

class SettingsResponse(BaseModel):
    """Response schema for GET /settings — all settings as a flat dict."""
    settings: dict[str, str]


class SettingsUpdate(BaseModel):
    """Request body for PUT /settings — partial dict of key→value updates."""
    settings: dict[str, str]
```

- [ ] **Step 2: Create the settings endpoint**

```python
# backend/app/api/v1/endpoints/settings.py
"""
Owner-only settings CRUD endpoints.

GET  /api/v1/settings  — return all settings (owner only)
PUT  /api/v1/settings  — update settings (owner only)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_owner
from app.core import settings_store
from app.schemas.schemas import SettingsResponse, SettingsUpdate

router = APIRouter()


@router.get("", response_model=SettingsResponse)
def get_settings(
    current_user=Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Return all current settings. Owner only."""
    # Ensure cache is fresh (no-op if already loaded)
    if not settings_store._cache:
        settings_store.load(db)
    return SettingsResponse(settings=dict(settings_store._cache))


@router.put("", response_model=SettingsResponse)
def update_settings(
    body: SettingsUpdate,
    current_user=Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Update one or more settings. Owner only. Rejects unknown keys with 400."""
    unknown_keys = set(body.settings.keys()) - settings_store.KNOWN_KEYS
    if unknown_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown settings keys: {sorted(unknown_keys)}",
        )
    settings_store.set_many(body.settings, db)
    return SettingsResponse(settings=dict(settings_store._cache))
```

- [ ] **Step 3: Register the router in router.py**

In `backend/app/api/v1/router.py`, add the import and include_router call:

```python
"""
API v1 Router - Combines all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    categories,
    menu,
    orders,
    admin,
    config,
    inventory,
    cash_counter,
    analytics,
    print_jobs,
    settings,
)

api_router = APIRouter()

# Include all endpoint routers with their prefixes and tags
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(menu.router, prefix="/menu", tags=["menu"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(cash_counter.router, prefix="/cash-counter", tags=["cash-counter"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(print_jobs.router, prefix="/print-jobs", tags=["print-relay"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
```

- [ ] **Step 4: Verify the app starts and new routes appear**

```bash
cd backend && uv run python -c "
from app.main import app
routes = [r.path for r in app.routes]
settings_routes = [r for r in routes if 'settings' in r]
print('Settings routes:', settings_routes)
"
```

Expected: `Settings routes: ['/api/v1/settings']`

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/schemas.py backend/app/api/v1/endpoints/settings.py backend/app/api/v1/router.py
git commit -m "feat: add owner-only GET/PUT /api/v1/settings endpoints"
```

---

## Task 6: Tests for the settings API

**Files:**
- Modify: `backend/tests/conftest.py`
- Modify: `backend/tests/test_settings.py`

- [ ] **Step 1: Add owner fixtures and settings_store fixture to conftest.py**

Add these fixtures at the end of `backend/tests/conftest.py`:

```python
@pytest.fixture
def owner_token(client):
    """Get a valid JWT token for the owner role."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "owner", "password": "owner123"},
    )
    assert response.status_code == 200, f"Owner login failed: {response.json()}"
    return response.json()["access_token"]


@pytest.fixture
def owner_headers(owner_token):
    """Authorization headers for owner-authenticated requests."""
    return {"Authorization": f"Bearer {owner_token}"}


@pytest.fixture
def loaded_settings_store(test_db):
    """Load settings_store from test_db and reset after the test."""
    from app.core import settings_store
    settings_store.load(test_db)
    yield settings_store
    # Reset to defaults so other tests aren't affected
    settings_store._cache = dict(settings_store.DEFAULTS)
```

- [ ] **Step 2: Add API tests to test_settings.py**

Append these tests to `backend/tests/test_settings.py`:

```python
# ============================================================================
# Settings API Tests
# ============================================================================

def test_get_settings_requires_auth(client, loaded_settings_store):
    """GET /settings returns 401 without a token."""
    response = client.get("/api/v1/settings")
    assert response.status_code == 401


def test_get_settings_forbidden_for_admin(client, auth_headers, loaded_settings_store):
    """GET /settings returns 403 for admin role (owner-only)."""
    response = client.get("/api/v1/settings", headers=auth_headers)
    assert response.status_code == 403


def test_get_settings_returns_all_keys(client, owner_headers, loaded_settings_store):
    """GET /settings returns a dict with all known setting keys."""
    response = client.get("/api/v1/settings", headers=owner_headers)
    assert response.status_code == 200
    data = response.json()
    assert "settings" in data
    from app.core.settings_store import KNOWN_KEYS
    for key in KNOWN_KEYS:
        assert key in data["settings"], f"Missing key: {key}"


def test_get_settings_returns_defaults(client, owner_headers, loaded_settings_store):
    """GET /settings default restaurant.name matches DEFAULTS."""
    response = client.get("/api/v1/settings", headers=owner_headers)
    assert response.status_code == 200
    assert response.json()["settings"]["restaurant.name"] == "Lily Cafe by Mary's Kitchen"


def test_put_settings_updates_value(client, owner_headers, loaded_settings_store, test_db):
    """PUT /settings updates a value and returns updated settings."""
    response = client.put(
        "/api/v1/settings",
        json={"settings": {"restaurant.name": "Updated Cafe"}},
        headers=owner_headers,
    )
    assert response.status_code == 200
    assert response.json()["settings"]["restaurant.name"] == "Updated Cafe"

    # Verify cache was updated
    from app.core import settings_store
    assert settings_store.get("restaurant.name") == "Updated Cafe"


def test_put_settings_persists_to_db(client, owner_headers, loaded_settings_store, test_db):
    """PUT /settings writes the value to DB."""
    client.put(
        "/api/v1/settings",
        json={"settings": {"app.max_tables": "30"}},
        headers=owner_headers,
    )
    row = test_db.query(AppSetting).filter(AppSetting.key == "app.max_tables").first()
    assert row is not None
    assert row.value == "30"


def test_put_settings_rejects_unknown_key(client, owner_headers, loaded_settings_store):
    """PUT /settings returns 400 for unknown keys."""
    response = client.put(
        "/api/v1/settings",
        json={"settings": {"bogus.key": "value"}},
        headers=owner_headers,
    )
    assert response.status_code == 400
    assert "bogus.key" in response.json()["detail"]


def test_put_settings_requires_owner(client, auth_headers, loaded_settings_store):
    """PUT /settings returns 403 for admin role."""
    response = client.put(
        "/api/v1/settings",
        json={"settings": {"restaurant.name": "Hack Cafe"}},
        headers=auth_headers,
    )
    assert response.status_code == 403
```

- [ ] **Step 3: Run all settings tests**

```bash
cd backend && uv run pytest tests/test_settings.py -v
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/conftest.py backend/tests/test_settings.py
git commit -m "test: add settings store and API endpoint tests with owner fixtures"
```

---

## Task 7: Update all consumers + slim config.py

This task updates all files that reference non-secret settings to use `settings_store` instead of `settings.*`, then removes those fields from `config.py`. Do all edits before committing.

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/core/security.py`
- Modify: `backend/app/api/v1/endpoints/auth.py`
- Modify: `backend/app/api/v1/endpoints/config.py`
- Modify: `backend/app/api/v1/endpoints/admin.py`
- Modify: `backend/app/api/v1/endpoints/orders.py`
- Modify: `backend/app/api/v1/endpoints/inventory.py`
- Modify: `backend/app/crud/crud.py`
- Modify: `backend/app/utils/pdf_generator.py`
- Modify: `backend/app/utils/printer.py`
- Modify: `backend/app/utils/chit_generator.py`
- Modify: `backend/app/utils/email_sender.py`

- [ ] **Step 1: Update security.py — TOKEN_EXPIRY_HOURS**

In `backend/app/core/security.py`, replace the `settings.TOKEN_EXPIRY_HOURS` reference:

```python
# Add import at top of security.py (alongside existing imports):
from app.core import settings_store

# Replace line ~73:
# OLD: expire = datetime.utcnow() + timedelta(hours=settings.TOKEN_EXPIRY_HOURS)
# NEW:
expire = datetime.utcnow() + timedelta(hours=settings_store.get_int("app.token_expiry_hours", 24))
```

Also remove the `from app.core.config import settings` import if it's only used for `TOKEN_EXPIRY_HOURS`. Check first:

```bash
grep -n "settings\." backend/app/core/security.py
```

If `settings.TOKEN_EXPIRY_HOURS` is the only usage, remove the `settings` import.

- [ ] **Step 2: Update auth.py endpoint — TOKEN_EXPIRY_HOURS**

In `backend/app/api/v1/endpoints/auth.py`:

```python
# Add import:
from app.core import settings_store

# Replace line ~34:
# OLD: expires_delta=timedelta(hours=settings.TOKEN_EXPIRY_HOURS),
# NEW:
expires_delta=timedelta(hours=settings_store.get_int("app.token_expiry_hours", 24)),
```

Remove `settings.TOKEN_EXPIRY_HOURS` — check if `settings` is used elsewhere in this file first:

```bash
grep -n "settings\." backend/app/api/v1/endpoints/auth.py
```

- [ ] **Step 3: Update config.py endpoint — restaurant_name, max_tables, gst_rate**

Replace the entire content of `backend/app/api/v1/endpoints/config.py`:

```python
"""
Configuration endpoints for exposing application settings to the frontend.
"""
from fastapi import APIRouter
from app.core import settings_store
from app.schemas.schemas import AppConfig

router = APIRouter()


@router.get("", response_model=AppConfig)
def get_app_config() -> AppConfig:
    """Return public application configuration."""
    return AppConfig(
        restaurant_name=settings_store.get("restaurant.name"),
        max_tables=settings_store.get_int("app.max_tables", 15),
        gst_rate=settings_store.get_float("app.gst_rate", 5.0),
    )
```

- [ ] **Step 4: Update admin.py endpoint — MAX_TABLES**

In `backend/app/api/v1/endpoints/admin.py`, find the line with `settings.MAX_TABLES`:

```python
# Add import:
from app.core import settings_store

# Replace:
# OLD: "total_tables": settings.MAX_TABLES,
# NEW:
"total_tables": settings_store.get_int("app.max_tables", 15),
```

Remove the `settings` import from admin.py if it's no longer used.

- [ ] **Step 5: Update orders.py endpoint — RECEIPT_PAPER_SIZE**

In `backend/app/api/v1/endpoints/orders.py`, find `settings.RECEIPT_PAPER_SIZE`:

```python
# Add import:
from app.core import settings_store

# Replace:
# OLD: paper_size = settings.RECEIPT_PAPER_SIZE
# NEW:
paper_size = settings_store.get("receipt.paper_size", "80mm")
```

Note: `settings.PRINTER_ENABLED` in orders.py stays as-is (uses `config.settings`).

- [ ] **Step 6: Update inventory.py endpoint — SMTP_ENABLED**

In `backend/app/api/v1/endpoints/inventory.py`, find `settings.SMTP_ENABLED`:

```python
# Add import:
from app.core import settings_store

# Replace:
# OLD: if settings.SMTP_ENABLED and created_transactions:
# NEW:
if settings_store.get_bool("smtp.enabled", False) and created_transactions:
```

- [ ] **Step 7: Update crud.py — GST_RATE (3 occurrences)**

In `backend/app/crud/crud.py`, there are three occurrences of `settings.GST_RATE`:

```python
# Add import at top:
from app.core import settings_store

# Replace all three:
# OLD: gst_amount = int(subtotal * settings.GST_RATE / 100)
# NEW:
gst_amount = int(subtotal * settings_store.get_float("app.gst_rate", 5.0) / 100)
```

Run to confirm all 3 occurrences are replaced:

```bash
grep -n "settings\.GST_RATE" backend/app/crud/crud.py
```

Expected: no output (all replaced).

- [ ] **Step 8: Update pdf_generator.py**

In `backend/app/utils/pdf_generator.py`, replace all `settings.*` references that are moving to settings_store. Add the import and replace:

```python
# Add import near top (alongside existing `from app.core.config import settings`):
from app.core import settings_store

# Line ~134 — TIMEZONE:
# OLD: local_tz = ZoneInfo(settings.TIMEZONE)
# NEW:
local_tz = ZoneInfo(settings_store.get("app.timezone", "Asia/Kolkata"))

# Lines ~304, ~323, ~327, ~335, ~338, ~342 — restaurant fields:
# OLD: restaurant_name = settings.RESTAURANT_NAME
# NEW:
restaurant_name = settings_store.get("restaurant.name")

# OLD: settings.RESTAURANT_ADDRESS_LINE1
# NEW:
settings_store.get("restaurant.address_line1")

# OLD: settings.RESTAURANT_ADDRESS_LINE2
# NEW:
settings_store.get("restaurant.address_line2")

# OLD: settings.RESTAURANT_PHONE
# NEW:
settings_store.get("restaurant.phone")

# OLD: settings.RESTAURANT_EMAIL
# NEW:
settings_store.get("restaurant.email")

# Lines ~352-353 — FSSAI, GSTIN:
# OLD: fssai_text = f"FSSAI: {settings.RESTAURANT_FSSAI}"
# OLD: gstin_text = f"GSTIN: {settings.RESTAURANT_GSTIN}"
# NEW:
fssai_text = f"FSSAI: {settings_store.get('restaurant.fssai')}"
gstin_text = f"GSTIN: {settings_store.get('restaurant.gstin')}"

# Lines ~476-477 — GST_RATE:
# OLD: half_gst_rate = settings.GST_RATE / 2
# OLD: gst_amount = int(order.subtotal * settings.GST_RATE / 100)
# NEW:
gst_rate = settings_store.get_float("app.gst_rate", 5.0)
half_gst_rate = gst_rate / 2
gst_amount = int(order.subtotal * gst_rate / 100)
```

`settings.RESTAURANT_LOGO_PATH` stays — it reads from `config.settings` (env var, excluded from DB). No change needed there.

After editing, verify no non-LOGO_PATH `settings.` usages remain:

```bash
grep -n "settings\." backend/app/utils/pdf_generator.py | grep -v "LOGO_PATH\|settings_store"
```

Expected: no output.

- [ ] **Step 9: Update printer.py**

In `backend/app/utils/printer.py`, replace settings references that move to store. `PRINTER_*` fields stay in `config.settings`.

```python
# Add import:
from app.core import settings_store

# RECEIPT_PAPER_SIZE occurrences (lines ~249, ~670):
# OLD: paper_size = settings.RECEIPT_PAPER_SIZE
# NEW:
paper_size = settings_store.get("receipt.paper_size", "80mm")

# Restaurant fields (lines ~261-274):
# OLD: printer.text(f"{settings.RESTAURANT_NAME.replace('Lily ', '')}\n")
# NEW:
printer.text(f"{settings_store.get('restaurant.name').replace('Lily ', '')}\n")

# OLD: printer.text(f"{settings.RESTAURANT_ADDRESS_LINE1}\n")
# NEW:
printer.text(f"{settings_store.get('restaurant.address_line1')}\n")

# OLD: printer.text(f"{settings.RESTAURANT_ADDRESS_LINE2}\n")
# NEW:
printer.text(f"{settings_store.get('restaurant.address_line2')}\n")

# OLD: printer.text(f"Tel: {settings.RESTAURANT_PHONE}\n")
# NEW:
printer.text(f"Tel: {settings_store.get('restaurant.phone')}\n")

# OLD: printer.text(f"{settings.RESTAURANT_EMAIL}\n")
# NEW:
printer.text(f"{settings_store.get('restaurant.email')}\n")

# OLD: printer.text(f"Tel: {settings.RESTAURANT_PHONE} | {settings.RESTAURANT_EMAIL}\n")
# NEW:
printer.text(f"Tel: {settings_store.get('restaurant.phone')} | {settings_store.get('restaurant.email')}\n")

# OLD: printer.text(f"GSTIN: {settings.RESTAURANT_GSTIN}\n")
# NEW:
printer.text(f"GSTIN: {settings_store.get('restaurant.gstin')}\n")

# Lines ~351-352 — GST_RATE:
# OLD: half_gst_rate = settings.GST_RATE / 2
# OLD: gst_amount = int(order.subtotal * settings.GST_RATE / 100)
# NEW:
_gst_rate = settings_store.get_float("app.gst_rate", 5.0)
half_gst_rate = _gst_rate / 2
gst_amount = int(order.subtotal * _gst_rate / 100)

# Line ~866 — RESTAURANT_NAME:
# OLD: printer.text(f"{settings.RESTAURANT_NAME}\n")
# NEW:
printer.text(f"{settings_store.get('restaurant.name')}\n")
```

Verify only PRINTER_* references remain for `settings.`:

```bash
grep -n "settings\." backend/app/utils/printer.py | grep -v "PRINTER_\|settings_store"
```

Expected: no output.

- [ ] **Step 10: Update chit_generator.py — RECEIPT_PAPER_SIZE**

In `backend/app/utils/chit_generator.py`:

```python
# Add import:
from app.core import settings_store

# Line ~30:
# OLD: paper_size = settings.RECEIPT_PAPER_SIZE
# NEW:
paper_size = settings_store.get("receipt.paper_size", "80mm")
```

`settings.PRINTER_NAME` on line ~188 stays (PRINTER_ fields remain in config).

- [ ] **Step 11: Update email_sender.py**

In `backend/app/utils/email_sender.py`:

```python
# Add import:
from app.core import settings_store

# Replace all references:
# OLD: msg["From"] = settings.SMTP_SENDER_EMAIL
# NEW:
msg["From"] = settings_store.get("smtp.sender_email")

# OLD: with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
# NEW:
with smtplib.SMTP(settings_store.get("smtp.host", "smtp.gmail.com"), settings_store.get_int("smtp.port", 587), timeout=30) as server:

# OLD: server.sendmail(settings.SMTP_SENDER_EMAIL, recipients, msg.as_string())
# NEW:
server.sendmail(settings_store.get("smtp.sender_email"), recipients, msg.as_string())

# OLD: {settings.RESTAURANT_NAME} - Inventory Report  (in subject/body strings)
# NEW:
{settings_store.get("restaurant.name")} - Inventory Report

# OLD: recipients = settings.INVENTORY_REPORT_EMAILS
# NEW:
report_emails_str = settings_store.get("smtp.report_emails", "")
recipients = [e.strip() for e in report_emails_str.split(",") if e.strip()]

# OLD: subject = f"Inventory Report - {settings.RESTAURANT_NAME}"
# NEW:
subject = f"Inventory Report - {settings_store.get('restaurant.name')}"
```

`settings.SMTP_PASSWORD` stays — it's a secret remaining in `config.py`.

Verify:

```bash
grep -n "settings\." backend/app/utils/email_sender.py | grep -v "SMTP_PASSWORD\|settings_store"
```

Expected: no output.

- [ ] **Step 12: Slim config.py — remove non-secret fields**

Replace `backend/app/core/config.py` with the secrets-only version:

```python
"""
Configuration management for Lily Cafe POS System.
Loads environment variables for secrets and bootstrap values only.

Non-secret settings (restaurant info, GST rate, etc.) are stored in the
database and accessed via app.core.settings_store.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Secrets and bootstrap settings loaded from environment variables."""

    # App Bootstrap
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

    # Admin Credentials
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeme123")

    # Owner Credentials
    OWNER_USERNAME: str = os.getenv("OWNER_USERNAME", "owner")
    OWNER_PASSWORD: str = os.getenv("OWNER_PASSWORD", "owner123")

    # Owner Password Hash (for cash counter verification)
    OWNER_PASSWORD_HASH: str = os.getenv(
        "OWNER_PASSWORD_HASH",
        "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
    )

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./restaurant.db")

    # CORS Origins (comma-separated) — needed at startup before DB is accessible
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
    ).split(",")

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"

    # Thesys C1 Configuration
    THESYS_API_KEY: str = os.getenv("THESYS_API_KEY", "")

    # Print Agent API Key (shared secret between backend and agent.py)
    PRINT_AGENT_API_KEY: str = os.getenv("PRINT_AGENT_API_KEY", "change-me-in-production")

    # Email / SMTP Password (secret — stays in env var)
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # Thermal Printer Configuration (local hardware — not stored in DB)
    PRINTER_ENABLED: bool = os.getenv("PRINTER_ENABLED", "false").lower() == "true"
    PRINTER_TYPE: str = os.getenv("PRINTER_TYPE", "")
    PRINTER_NAME: str = os.getenv("PRINTER_NAME", "")
    PRINTER_VENDOR_ID: str = os.getenv("PRINTER_VENDOR_ID", "")
    PRINTER_PRODUCT_ID: str = os.getenv("PRINTER_PRODUCT_ID", "")
    PRINTER_PORT: str = os.getenv("PRINTER_PORT", "")
    PRINTER_BAUDRATE: int = int(os.getenv("PRINTER_BAUDRATE", "9600"))

    # Restaurant logo path (local filesystem — not applicable in cloud deployment)
    RESTAURANT_LOGO_PATH: str = os.getenv("RESTAURANT_LOGO_PATH", "")


# Create a singleton instance
settings = Settings()
```

- [ ] **Step 13: Run the full test suite**

```bash
cd backend && uv run pytest tests/ -v --tb=short 2>&1 | tail -40
```

Expected: all tests PASS. Fix any import errors before committing.

- [ ] **Step 14: Commit**

```bash
git add backend/app/core/config.py \
        backend/app/core/security.py \
        backend/app/api/v1/endpoints/auth.py \
        backend/app/api/v1/endpoints/config.py \
        backend/app/api/v1/endpoints/admin.py \
        backend/app/api/v1/endpoints/orders.py \
        backend/app/api/v1/endpoints/inventory.py \
        backend/app/crud/crud.py \
        backend/app/utils/pdf_generator.py \
        backend/app/utils/printer.py \
        backend/app/utils/chit_generator.py \
        backend/app/utils/email_sender.py
git commit -m "feat: migrate non-secret settings from config.py to settings_store"
```

---

## Task 8: Frontend settings API hooks

**Files:**
- Create: `frontend/src/api/settings.ts`

- [ ] **Step 1: Create settings.ts**

```typescript
// frontend/src/api/settings.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from './client'

export type Settings = Record<string, string>

interface SettingsResponse {
  settings: Settings
}

// ============================================================================
// API functions
// ============================================================================

async function fetchSettings(): Promise<Settings> {
  const response = await apiClient.get<SettingsResponse>('/settings')
  return response.data.settings
}

async function patchSettings(updates: Settings): Promise<Settings> {
  const response = await apiClient.put<SettingsResponse>('/settings', { settings: updates })
  return response.data.settings
}

// ============================================================================
// TanStack Query hooks
// ============================================================================

export function useSettings() {
  return useQuery<Settings>({
    queryKey: ['settings'],
    queryFn: fetchSettings,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

export function useUpdateSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: patchSettings,
    onSuccess: () => {
      // Invalidate both settings and public config (config reads from same store)
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      queryClient.invalidateQueries({ queryKey: ['config'] })
    },
  })
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep "settings"
```

Expected: no errors for settings.ts.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/settings.ts
git commit -m "feat: add useSettings and useUpdateSettings TanStack Query hooks"
```

---

## Task 9: Settings page UI

**Files:**
- Create: `frontend/src/pages/SettingsPage.tsx`

- [ ] **Step 1: Create SettingsPage.tsx**

```tsx
// frontend/src/pages/SettingsPage.tsx
import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { Gear } from '@phosphor-icons/react'
import { useSettings, useUpdateSettings } from '../api/settings'
import type { Settings } from '../api/settings'

// ============================================================================
// Constants
// ============================================================================

const TIMEZONES = [
  'Asia/Kolkata',
  'Asia/Dubai',
  'Asia/Singapore',
  'Asia/Tokyo',
  'America/New_York',
  'America/Chicago',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Australia/Sydney',
  'UTC',
]

// ============================================================================
// Small reusable components
// ============================================================================

interface FieldProps {
  label: string
  value: string
  onChange: (v: string) => void
  type?: string
  step?: string
  placeholder?: string
  hint?: string
}

function Field({ label, value, onChange, type = 'text', step, placeholder, hint }: FieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-neutral-text-dark mb-1">{label}</label>
      <input
        type={type}
        step={step}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-neutral-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-coffee-brown/30 focus:border-coffee-brown bg-white"
      />
      {hint && <p className="text-xs text-muted mt-1">{hint}</p>}
    </div>
  )
}

interface SaveButtonProps {
  onClick: () => void
  isPending: boolean
}

function SaveButton({ onClick, isPending }: SaveButtonProps) {
  return (
    <div className="pt-2">
      <button
        type="button"
        onClick={onClick}
        disabled={isPending}
        className="btn bg-coffee-brown text-white hover:bg-coffee-dark disabled:opacity-50 disabled:cursor-not-allowed px-6"
      >
        {isPending ? 'Saving…' : 'Save'}
      </button>
    </div>
  )
}

interface SectionProps {
  title: string
  children: React.ReactNode
}

function Section({ title, children }: SectionProps) {
  return (
    <section className="bg-white rounded-lg border border-neutral-border p-6 space-y-4">
      <h2 className="text-base font-semibold text-coffee-brown border-b border-neutral-border pb-2">
        {title}
      </h2>
      {children}
    </section>
  )
}

// ============================================================================
// Main page
// ============================================================================

export default function SettingsPage() {
  const { data: settings, isLoading, isError } = useSettings()
  const updateMutation = useUpdateSettings()

  // Section-level form state — each section saves independently
  const [restaurant, setRestaurant] = useState<Settings>({})
  const [appConfig, setAppConfig] = useState<Settings>({})
  const [receipt, setReceipt] = useState<Settings>({})
  const [smtp, setSmtp] = useState<Settings>({})

  // Initialise form state when settings load
  useEffect(() => {
    if (!settings) return
    setRestaurant({
      'restaurant.name': settings['restaurant.name'] ?? '',
      'restaurant.address_line1': settings['restaurant.address_line1'] ?? '',
      'restaurant.address_line2': settings['restaurant.address_line2'] ?? '',
      'restaurant.phone': settings['restaurant.phone'] ?? '',
      'restaurant.email': settings['restaurant.email'] ?? '',
      'restaurant.gstin': settings['restaurant.gstin'] ?? '',
      'restaurant.fssai': settings['restaurant.fssai'] ?? '',
    })
    setAppConfig({
      'app.max_tables': settings['app.max_tables'] ?? '15',
      'app.gst_rate': settings['app.gst_rate'] ?? '5.0',
      'app.timezone': settings['app.timezone'] ?? 'Asia/Kolkata',
      'app.token_expiry_hours': settings['app.token_expiry_hours'] ?? '24',
    })
    setReceipt({
      'receipt.paper_size': settings['receipt.paper_size'] ?? '80mm',
      'receipt.google_review_url': settings['receipt.google_review_url'] ?? '',
      'receipt.feedback_form_url': settings['receipt.feedback_form_url'] ?? '',
    })
    setSmtp({
      'smtp.enabled': settings['smtp.enabled'] ?? 'false',
      'smtp.host': settings['smtp.host'] ?? 'smtp.gmail.com',
      'smtp.port': settings['smtp.port'] ?? '587',
      'smtp.username': settings['smtp.username'] ?? '',
      'smtp.sender_email': settings['smtp.sender_email'] ?? '',
      'smtp.report_emails': settings['smtp.report_emails'] ?? '',
    })
  }, [settings])

  const save = async (sectionSettings: Settings, sectionName: string) => {
    try {
      await updateMutation.mutateAsync(sectionSettings)
      toast.success(`${sectionName} saved`)
    } catch {
      toast.error(`Failed to save ${sectionName}`)
    }
  }

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <p className="text-muted">Loading settings…</p>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-8">
        <p className="text-error">Failed to load settings. Please refresh.</p>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <Gear size={28} weight="duotone" className="text-coffee-brown" />
        <h1 className="font-heading text-2xl text-coffee-brown">Settings</h1>
      </div>

      {/* Restaurant Info */}
      <Section title="Restaurant Info">
        <div className="space-y-3">
          <Field
            label="Restaurant Name"
            value={restaurant['restaurant.name'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.name': v }))}
          />
          <Field
            label="Address Line 1"
            value={restaurant['restaurant.address_line1'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.address_line1': v }))}
          />
          <Field
            label="Address Line 2"
            value={restaurant['restaurant.address_line2'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.address_line2': v }))}
          />
          <Field
            label="Phone"
            value={restaurant['restaurant.phone'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.phone': v }))}
          />
          <Field
            label="Email"
            value={restaurant['restaurant.email'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.email': v }))}
            type="email"
          />
          <Field
            label="GSTIN"
            value={restaurant['restaurant.gstin'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.gstin': v }))}
          />
          <Field
            label="FSSAI"
            value={restaurant['restaurant.fssai'] ?? ''}
            onChange={(v) => setRestaurant((s) => ({ ...s, 'restaurant.fssai': v }))}
          />
        </div>
        <SaveButton onClick={() => save(restaurant, 'Restaurant Info')} isPending={updateMutation.isPending} />
      </Section>

      {/* App Config */}
      <Section title="App Config">
        <div className="space-y-3">
          <Field
            label="Max Tables"
            value={appConfig['app.max_tables'] ?? '15'}
            onChange={(v) => setAppConfig((s) => ({ ...s, 'app.max_tables': v }))}
            type="number"
          />
          <Field
            label="GST Rate (%)"
            value={appConfig['app.gst_rate'] ?? '5.0'}
            onChange={(v) => setAppConfig((s) => ({ ...s, 'app.gst_rate': v }))}
            type="number"
            step="0.5"
          />
          <div>
            <label className="block text-sm font-medium text-neutral-text-dark mb-1">Timezone</label>
            <select
              value={appConfig['app.timezone'] ?? 'Asia/Kolkata'}
              onChange={(e) => setAppConfig((s) => ({ ...s, 'app.timezone': e.target.value }))}
              className="w-full border border-neutral-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-coffee-brown/30 focus:border-coffee-brown bg-white"
            >
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>
                  {tz}
                </option>
              ))}
            </select>
          </div>
          <Field
            label="Token Expiry (hours)"
            value={appConfig['app.token_expiry_hours'] ?? '24'}
            onChange={(v) => setAppConfig((s) => ({ ...s, 'app.token_expiry_hours': v }))}
            type="number"
            hint="How long login sessions last before requiring re-authentication"
          />
        </div>
        <SaveButton onClick={() => save(appConfig, 'App Config')} isPending={updateMutation.isPending} />
      </Section>

      {/* Receipt */}
      <Section title="Receipt">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-text-dark mb-2">Paper Size</label>
            <div className="flex gap-2">
              {['58mm', '80mm'].map((size) => (
                <button
                  key={size}
                  type="button"
                  onClick={() => setReceipt((s) => ({ ...s, 'receipt.paper_size': size }))}
                  className={`px-5 py-2 rounded-md text-sm font-medium border transition-colors ${
                    receipt['receipt.paper_size'] === size
                      ? 'bg-coffee-brown text-white border-coffee-brown'
                      : 'bg-white text-neutral-text-dark border-neutral-border hover:border-coffee-brown'
                  }`}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>
          <Field
            label="Google Review URL"
            value={receipt['receipt.google_review_url'] ?? ''}
            onChange={(v) => setReceipt((s) => ({ ...s, 'receipt.google_review_url': v }))}
            placeholder="https://g.page/r/your-business-review"
            hint="Printed as a QR code on receipts"
          />
          <Field
            label="Feedback Form URL"
            value={receipt['receipt.feedback_form_url'] ?? ''}
            onChange={(v) => setReceipt((s) => ({ ...s, 'receipt.feedback_form_url': v }))}
            placeholder="https://forms.gle/your-form-id"
            hint="Printed as a QR code on receipts"
          />
        </div>
        <SaveButton onClick={() => save(receipt, 'Receipt')} isPending={updateMutation.isPending} />
      </Section>

      {/* Email / SMTP */}
      <Section title="Email / SMTP">
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="smtp-enabled"
              checked={smtp['smtp.enabled'] === 'true'}
              onChange={(e) =>
                setSmtp((s) => ({ ...s, 'smtp.enabled': e.target.checked ? 'true' : 'false' }))
              }
              className="w-4 h-4 accent-coffee-brown"
            />
            <label htmlFor="smtp-enabled" className="text-sm font-medium text-neutral-text-dark">
              Enable email sending (inventory reports)
            </label>
          </div>
          <Field
            label="SMTP Host"
            value={smtp['smtp.host'] ?? ''}
            onChange={(v) => setSmtp((s) => ({ ...s, 'smtp.host': v }))}
            placeholder="smtp.gmail.com"
          />
          <Field
            label="SMTP Port"
            value={smtp['smtp.port'] ?? '587'}
            onChange={(v) => setSmtp((s) => ({ ...s, 'smtp.port': v }))}
            type="number"
          />
          <Field
            label="Username"
            value={smtp['smtp.username'] ?? ''}
            onChange={(v) => setSmtp((s) => ({ ...s, 'smtp.username': v }))}
            placeholder="your@email.com"
          />
          <Field
            label="Sender Email"
            value={smtp['smtp.sender_email'] ?? ''}
            onChange={(v) => setSmtp((s) => ({ ...s, 'smtp.sender_email': v }))}
            type="email"
            placeholder="noreply@lilycafe.com"
          />
          <Field
            label="Report Recipients"
            value={smtp['smtp.report_emails'] ?? ''}
            onChange={(v) => setSmtp((s) => ({ ...s, 'smtp.report_emails': v }))}
            placeholder="owner@email.com,manager@email.com"
            hint="Comma-separated email addresses for inventory reports"
          />
          <p className="text-xs text-muted bg-neutral-background rounded p-2">
            SMTP password is set via the <code>SMTP_PASSWORD</code> environment variable on the server.
          </p>
        </div>
        <SaveButton onClick={() => save(smtp, 'Email / SMTP')} isPending={updateMutation.isPending} />
      </Section>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "SettingsPage\|settings"
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/SettingsPage.tsx
git commit -m "feat: add owner-only Settings page with 4 configurable sections"
```

---

## Task 10: Register route + sidebar nav

**Files:**
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`

- [ ] **Step 1: Add the route in main.tsx**

In `frontend/src/main.tsx`, add the import and route:

```tsx
// Add import alongside other admin page imports:
import SettingsPage from './pages/SettingsPage.tsx'

// Add route inside the AdminLayout route group, after AnalyticsPage:
<Route
  path="/admin/settings"
  element={
    <ProtectedRoute requiredRole="owner">
      <SettingsPage />
    </ProtectedRoute>
  }
/>
```

- [ ] **Step 2: Add Settings nav item to Sidebar.tsx**

In `frontend/src/components/Sidebar.tsx`, add the import and nav item:

```tsx
// Add to existing phosphor icon import:
import { Package, CurrencyInr, ChartLine, CaretLeft, CaretRight, Gear } from "@phosphor-icons/react";

// Add after the Analytics NavItem (inside the {role === 'owner' && ...} block,
// or as its own owner-only block right after):
{role === 'owner' && (
  <NavItem
    to="/admin/settings"
    icon={<Gear size={24} weight="duotone" />}
    label="Settings"
    onClick={handleCloseMobile}
    isCollapsed={isCollapsed}
  />
)}
```

- [ ] **Step 3: Verify the frontend builds without errors**

```bash
cd frontend && npx tsc --noEmit && echo "TypeScript OK"
```

Expected: `TypeScript OK`

- [ ] **Step 4: Start both servers and manually verify the settings page**

```bash
# Terminal 1 — backend
cd backend && uv run python -m app.main

# Terminal 2 — frontend
cd frontend && npm run dev
```

1. Navigate to `http://localhost:5173/login`
2. Log in as **owner** (not admin)
3. Verify "Settings" appears in the sidebar
4. Click Settings → verify page loads with 4 sections
5. Change restaurant name → click Save → verify toast "Restaurant Info saved"
6. Refresh page → verify new name persists
7. Log out and log in as **admin** → verify Settings does NOT appear in sidebar
8. Try navigating to `/admin/settings` directly as admin → verify redirect to login

- [ ] **Step 5: Commit**

```bash
git add frontend/src/main.tsx frontend/src/components/Sidebar.tsx
git commit -m "feat: add /admin/settings route and owner-only sidebar nav item"
```

---

## Task 11: Deployment

- [ ] **Step 1: Run the migration on Fly.io**

```bash
fly ssh console --app lily-cafe-pos -C "cd /app && uv run python backend/scripts/migrate_add_app_settings.py"
```

Expected output ends with:
```
Done. Inserted: 21, Skipped (already existed): 0
```

- [ ] **Step 2: Deploy the new backend**

```bash
fly deploy --app lily-cafe-pos
```

- [ ] **Step 3: Verify settings endpoint is live**

```bash
# Get an owner token first, then:
curl -s https://lily-cafe-pos.fly.dev/api/v1/settings \
  -H "Authorization: Bearer <owner-token>" | python3 -m json.tool | head -20
```

Expected: JSON with `{ "settings": { "restaurant.name": "...", ... } }`

- [ ] **Step 4: Update settings via the deployed UI**

1. Open the deployed frontend
2. Log in as owner
3. Go to Settings → update restaurant details to correct values
4. Save each section
5. Verify receipts/PDFs now show the correct restaurant name

- [ ] **Step 5: Retire old env vars from Fly.io**

After confirming settings are correct in the DB, remove the now-redundant env vars:

```bash
fly secrets unset RESTAURANT_NAME RESTAURANT_ADDRESS_LINE1 RESTAURANT_ADDRESS_LINE2 \
  RESTAURANT_PHONE RESTAURANT_EMAIL RESTAURANT_GSTIN RESTAURANT_FSSAI \
  MAX_TABLES GST_RATE TIMEZONE TOKEN_EXPIRY_HOURS \
  RECEIPT_PAPER_SIZE GOOGLE_REVIEW_URL FEEDBACK_FORM_URL \
  SMTP_ENABLED SMTP_HOST SMTP_PORT SMTP_USERNAME SMTP_SENDER_EMAIL INVENTORY_REPORT_EMAILS \
  --app lily-cafe-pos
```

This triggers a redeploy — verify the app still works after.

---

## Self-Review Checklist

- [x] All 21 settings keys defined in DEFAULTS, KNOWN_KEYS, migration seed, and SettingsPage form state
- [x] Secrets (`SECRET_KEY`, `DATABASE_URL`, credentials, `SMTP_PASSWORD`, API keys, `CORS_ORIGINS`, `PRINTER_*`) stay in config.py
- [x] `settings_store.load()` called after `init_db()` so table exists before load
- [x] `set_many()` writes then reloads cache — immediate effect
- [x] PUT endpoint rejects unknown keys with 400
- [x] All consumer files updated (security.py, auth.py, config.py endpoint, admin.py, orders.py, inventory.py, crud.py, pdf_generator.py, printer.py, chit_generator.py, email_sender.py)
- [x] Owner-only auth via `get_current_owner` dependency (same pattern as analytics endpoint)
- [x] Frontend uses `requiredRole="owner"` on the route
- [x] Sidebar Settings item gated by `role === 'owner'` (same pattern as Analytics)
- [x] `loaded_settings_store` fixture resets cache after each test to avoid cross-test pollution
- [x] Migration script is idempotent — safe to run multiple times
