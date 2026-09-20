"""Deterministic resolution of a period into IST calendar days and UTC bounds.

The model never computes dates for relative phrases. "Last week" comes back
as the named period LAST_WEEK and is resolved here, in code, against today's
IST date — so the meaning of "last week" is fixed (Monday to Sunday) and
tested, not re-derived by a language model on every question.

Explicit dates the owner actually said ("August", "since 1 May") arrive as
month/range/since specs and are validated and capped here.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field

IST = timezone(timedelta(hours=5, minutes=30))


def today_ist() -> date:
    return datetime.now(IST).date()


class NamedPeriod(StrEnum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"  # Monday to today
    LAST_WEEK = "last_week"  # previous Monday to Sunday
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
    LAST_7_DAYS = "last_7_days"  # including today
    LAST_30_DAYS = "last_30_days"
    ALL_TIME = "all_time"


class NamedSpec(BaseModel):
    kind: Literal["named"] = "named"
    name: NamedPeriod


class MonthSpec(BaseModel):
    kind: Literal["month"] = "month"
    year: int
    month: int = Field(ge=1, le=12)


class RangeSpec(BaseModel):
    kind: Literal["range"] = "range"
    start: date
    end: date


class SinceSpec(BaseModel):
    kind: Literal["since"] = "since"
    start: date


class DaySpec(BaseModel):
    kind: Literal["day"] = "day"
    date: date


Period = Annotated[
    NamedSpec | MonthSpec | RangeSpec | SinceSpec | DaySpec,
    Field(discriminator="kind"),
]


class PeriodError(ValueError):
    """The spec cannot describe a real, past-or-present stretch of days."""


@dataclass(frozen=True)
class ResolvedPeriod:
    """Inclusive IST calendar days, plus the naive-UTC bounds the ORM needs."""

    start_day: date | None
    end_day: date | None
    label: str

    @property
    def start_utc(self) -> datetime | None:
        return _day_start_utc(self.start_day) if self.start_day else None

    @property
    def end_utc(self) -> datetime | None:
        return _day_end_utc(self.end_day) if self.end_day else None

    @property
    def start_iso(self) -> str | None:
        return self.start_utc.isoformat() if self.start_utc else None

    @property
    def end_iso(self) -> str | None:
        return self.end_utc.isoformat() if self.end_utc else None

    @property
    def is_single_day(self) -> bool:
        return self.start_day is not None and self.start_day == self.end_day


def resolve(spec: NamedSpec | MonthSpec | RangeSpec | SinceSpec | DaySpec, today: date) -> ResolvedPeriod:
    if isinstance(spec, NamedSpec):
        start, end = _named_bounds(spec.name, today)
        if start is None:
            return ResolvedPeriod(None, None, "All time")
        return ResolvedPeriod(start, end, _label(start, end, today, spec.name))

    if isinstance(spec, MonthSpec):
        start = date(spec.year, spec.month, 1)
        if start > today:
            raise PeriodError(f"{start:%B %Y} has not started yet")
        end = min(_month_end(start), today)
        return ResolvedPeriod(start, end, _label(start, end, today))

    if isinstance(spec, RangeSpec):
        if spec.start > spec.end:
            raise PeriodError("The range ends before it starts")
        if spec.start > today:
            raise PeriodError(f"{spec.start:%-d %b %Y} is in the future")
        end = min(spec.end, today)
        return ResolvedPeriod(spec.start, end, _label(spec.start, end, today))

    if isinstance(spec, SinceSpec):
        if spec.start > today:
            raise PeriodError(f"{spec.start:%-d %b %Y} is in the future")
        return ResolvedPeriod(spec.start, today, _label(spec.start, today, today))

    if isinstance(spec, DaySpec):
        if spec.date > today:
            raise PeriodError(f"{spec.date:%-d %b %Y} is in the future")
        return ResolvedPeriod(spec.date, spec.date, _label(spec.date, spec.date, today))

    raise PeriodError(f"Unknown period kind: {spec!r}")  # pragma: no cover


# ----------------------------------------------------------------------
# Bounds
# ----------------------------------------------------------------------


def _named_bounds(name: NamedPeriod, today: date) -> tuple[date | None, date | None]:
    monday = today - timedelta(days=today.weekday())
    first_of_month = today.replace(day=1)

    if name is NamedPeriod.TODAY:
        return today, today
    if name is NamedPeriod.YESTERDAY:
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    if name is NamedPeriod.THIS_WEEK:
        return monday, today
    if name is NamedPeriod.LAST_WEEK:
        return monday - timedelta(days=7), monday - timedelta(days=1)
    if name is NamedPeriod.THIS_MONTH:
        return first_of_month, today
    if name is NamedPeriod.LAST_MONTH:
        last_month_end = first_of_month - timedelta(days=1)
        return last_month_end.replace(day=1), last_month_end
    if name is NamedPeriod.THIS_YEAR:
        return today.replace(month=1, day=1), today
    if name is NamedPeriod.LAST_7_DAYS:
        return today - timedelta(days=6), today
    if name is NamedPeriod.LAST_30_DAYS:
        return today - timedelta(days=29), today
    if name is NamedPeriod.ALL_TIME:
        return None, None
    raise PeriodError(f"Unknown named period: {name}")  # pragma: no cover


def _month_end(any_day_in_month: date) -> date:
    next_month = (any_day_in_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(days=1)


def _day_start_utc(day: date) -> datetime:
    return datetime.combine(day, time.min, IST).astimezone(UTC).replace(tzinfo=None)


def _day_end_utc(day: date) -> datetime:
    return datetime.combine(day, time.max, IST).astimezone(UTC).replace(tzinfo=None)


# ----------------------------------------------------------------------
# Labels — always shown to the owner, so a misread question is visible
# ----------------------------------------------------------------------


def _label(start: date, end: date, today: date, name: NamedPeriod | None = None) -> str:
    if start == end:
        if start == today:
            return f"Today, {start:%a %-d %b}"
        if start == today - timedelta(days=1):
            return f"Yesterday, {start:%a %-d %b}"
        return f"{start:%a %-d %b %Y}"

    if start.day == 1 and end == _month_end(start):
        return f"{start:%B %Y}"
    # A month cut short by today — named or explicit — is a partial month.
    if start.day == 1 and end == today and end < _month_end(start):
        return f"{start:%B} so far, {_span(start, end)}"

    if name is NamedPeriod.LAST_WEEK:
        return f"Last week, {_span(start, end)}"
    if name is NamedPeriod.THIS_WEEK:
        return f"This week so far, {_span(start, end)}"
    if name is NamedPeriod.THIS_YEAR:
        return f"{start.year} so far, {_span(start, end)}"
    if name in (NamedPeriod.LAST_7_DAYS, NamedPeriod.LAST_30_DAYS):
        days = (end - start).days + 1
        return f"Last {days} days, {_span(start, end)}"
    return _span(start, end)


def _span(start: date, end: date) -> str:
    if start.year != end.year:
        return f"{start:%-d %b %Y} – {end:%-d %b %Y}"
    if start.month != end.month:
        return f"{start:%-d %b} – {end:%-d %b %Y}"
    return f"{start:%-d}–{end:%-d %b %Y}"
