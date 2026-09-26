"""SQLAlchemy model for the stored daily digest."""

from datetime import UTC, datetime

from sqlalchemy import Column, Date, DateTime, Integer, Text

from app.db.session import Base


class DailyDigest(Base):
    """One computed digest per trading day.

    `date` is the IST calendar day the digest is *about* (yesterday, when the
    scheduler runs it), and is unique — that uniqueness is what makes the
    digest run idempotent, so a restart or a second caller cannot produce two
    digests for the same day.
    """

    __tablename__ = "daily_digests"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    # The rendered lines and the numbers behind them, as JSON.
    body_json = Column(Text, nullable=False)
    email_sent_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False
    )
