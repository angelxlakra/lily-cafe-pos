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
