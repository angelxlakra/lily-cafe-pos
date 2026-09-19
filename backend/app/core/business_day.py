"""
One consistent notion of "now" and "today" for Lily Cafe POS.

Timestamps (``created_at``, ``updated_at``, ``canceled_at``, ...) are stored as
naive UTC. The business day, however, is the *local* calendar date in the
configured timezone (``app.timezone``, default Asia/Kolkata). An order placed
at 01:00 IST belongs to that IST date even though its UTC timestamp still
reads the previous day.

Every module that needs "today" or a "today" filter must go through here so
the two conventions cannot drift apart. Tests can freeze the clock by
monkeypatching :func:`utcnow`.
"""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def utcnow() -> datetime:
    """Current time as a naive UTC datetime — the storage convention for all timestamps."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def business_timezone() -> ZoneInfo:
    """The configured local timezone."""
    from app.core import settings_store  # local import: settings_store imports the models

    return ZoneInfo(settings_store.get("app.timezone", "Asia/Kolkata"))


def to_business_date(utc_dt: datetime) -> date:
    """Local calendar date of a stored (naive UTC) timestamp."""
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(business_timezone()).date()


def business_today() -> date:
    """The current business day (local date in the configured timezone)."""
    return to_business_date(utcnow())


def business_day_utc_bounds(day: date) -> tuple[datetime, datetime]:
    """
    Half-open UTC range ``[start, end)`` covering the given local business day.

    Returned datetimes are naive UTC so they compare directly with stored
    timestamps on both SQLite and PostgreSQL.
    """
    tz = business_timezone()
    start_local = datetime.combine(day, datetime.min.time(), tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return (
        start_local.astimezone(timezone.utc).replace(tzinfo=None),
        end_local.astimezone(timezone.utc).replace(tzinfo=None),
    )


def on_business_day(column, day: date):
    """SQLAlchemy criterion: ``column`` falls on the given local business day."""
    start, end = business_day_utc_bounds(day)
    return (column >= start) & (column < end)


def on_or_after_business_day(column, day: date):
    """SQLAlchemy criterion: ``column`` is on or after the start of the given business day."""
    start, _ = business_day_utc_bounds(day)
    return column >= start


def on_or_before_business_day(column, day: date):
    """SQLAlchemy criterion: ``column`` is on or before the end of the given business day."""
    _, end = business_day_utc_bounds(day)
    return column < end
