# backend/tests/test_settings.py
"""Tests for the settings store and settings API endpoints."""

import pytest
from app.core import settings_store
from app.models.settings_model import AppSetting


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Reset the settings cache after each test to prevent cross-test pollution."""
    yield
    settings_store._cache = {}


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
    from app.models.settings_model import AppSetting
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
