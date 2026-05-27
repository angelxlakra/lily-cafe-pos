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
