"""
Configuration endpoints for exposing application settings to the frontend.
"""
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.schemas import AppConfig
router = APIRouter()
@router.get("", response_model=AppConfig)
def get_app_config() -> AppConfig:
    """Return public application configuration."""
    return AppConfig(
        restaurant_name=settings.RESTAURANT_NAME,
        max_tables=settings.MAX_TABLES,
        gst_rate=settings.GST_RATE,
    )