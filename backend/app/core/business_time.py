"""
Business-day time helpers for Lily Cafe POS System.

The cafe runs on Indian Standard Time, but every timestamp column
(``Order.created_at`` etc.) is stored as naive UTC. Any "today" / date-range
filter therefore has to be computed on the IST calendar and then converted to
UTC bounds before it is compared against the stored value. Comparing the UTC
date of a row against the IST date of "now" is wrong between 18:30 and 24:00
UTC (00:00–05:30 IST), when the two calendars disagree.

All wall-clock reads go through ``utc_now`` so tests can freeze the clock.
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

# IST is UTC+5:30 and has no DST.
IST = timezone(timedelta(hours=5, minutes=30))


def utc_now() -> datetime:
    """Current time as an aware UTC datetime. The single seam for freezing time."""
    return datetime.now(timezone.utc)


def business_today() -> date:
    """The current IST calendar date."""
    return utc_now().astimezone(IST).date()


def ist_day_to_utc_bounds(
    start: Optional[str], end: Optional[str]
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Interpret start/end as IST calendar days (YYYY-MM-DD) and return
    naive-UTC datetime bounds suitable for comparing against ``created_at``.
    Either bound may be None (open-ended). Raises ValueError on bad input."""
    start_dt = None
    end_dt = None
    if start:
        d = date.fromisoformat(start)
        start_dt = (
            datetime.combine(d, time.min, IST).astimezone(timezone.utc).replace(tzinfo=None)
        )
    if end:
        d = date.fromisoformat(end)
        end_dt = (
            datetime.combine(d, time.max, IST).astimezone(timezone.utc).replace(tzinfo=None)
        )
    return start_dt, end_dt


def today_utc_bounds() -> tuple[datetime, datetime]:
    """Naive-UTC bounds of the current IST calendar day."""
    today = business_today().isoformat()
    start_dt, end_dt = ist_day_to_utc_bounds(today, today)
    return start_dt, end_dt
