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
