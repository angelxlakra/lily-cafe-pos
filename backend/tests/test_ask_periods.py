"""Period resolution is the part of the Ask feature most likely to be quietly
wrong — "last week" meaning different things on different days — so it is
pinned down day by day here."""

from datetime import date, datetime

import pytest

from app.ask.periods import (
    DaySpec,
    MonthSpec,
    NamedPeriod,
    NamedSpec,
    PeriodError,
    RangeSpec,
    SinceSpec,
    resolve,
)

# Sunday 20 September 2026 — the last day of the week Mon 14 to Sun 20.
TODAY = date(2026, 9, 20)
MON = date(2026, 9, 14)
PREV_SUN = date(2026, 9, 13)


def named(name, today=TODAY):
    return resolve(NamedSpec(name=name), today)


# ============================================================================
# Named periods
# ============================================================================


def test_today_and_yesterday():
    assert (named(NamedPeriod.TODAY).start_day, named(NamedPeriod.TODAY).end_day) == (TODAY, TODAY)
    y = named(NamedPeriod.YESTERDAY)
    assert (y.start_day, y.end_day) == (date(2026, 9, 19), date(2026, 9, 19))


def test_this_week_runs_monday_to_today():
    p = named(NamedPeriod.THIS_WEEK)
    assert (p.start_day, p.end_day) == (MON, TODAY)


def test_this_week_on_a_monday_is_just_monday():
    p = named(NamedPeriod.THIS_WEEK, today=MON)
    assert (p.start_day, p.end_day) == (MON, MON)


def test_last_week_is_the_previous_monday_to_sunday():
    p = named(NamedPeriod.LAST_WEEK)
    assert (p.start_day, p.end_day) == (date(2026, 9, 7), PREV_SUN)



def test_last_week_on_a_monday():
    p = named(NamedPeriod.LAST_WEEK, today=MON)
    assert (p.start_day, p.end_day) == (date(2026, 9, 7), PREV_SUN)


def test_this_month_and_last_month():
    tm = named(NamedPeriod.THIS_MONTH)
    assert (tm.start_day, tm.end_day) == (date(2026, 9, 1), TODAY)
    lm = named(NamedPeriod.LAST_MONTH)
    assert (lm.start_day, lm.end_day) == (date(2026, 8, 1), date(2026, 8, 31))


def test_last_month_in_january_is_december_of_previous_year():
    p = named(NamedPeriod.LAST_MONTH, today=date(2026, 1, 15))
    assert (p.start_day, p.end_day) == (date(2025, 12, 1), date(2025, 12, 31))


def test_last_month_handles_february_lengths():
    p = named(NamedPeriod.LAST_MONTH, today=date(2028, 3, 10))  # 2028 is a leap year
    assert (p.start_day, p.end_day) == (date(2028, 2, 1), date(2028, 2, 29))


def test_this_year():
    p = named(NamedPeriod.THIS_YEAR)
    assert (p.start_day, p.end_day) == (date(2026, 1, 1), TODAY)


def test_last_7_and_30_days_include_today():
    p7 = named(NamedPeriod.LAST_7_DAYS)
    assert (p7.start_day, p7.end_day) == (date(2026, 9, 14), TODAY)
    assert (p7.end_day - p7.start_day).days + 1 == 7
    p30 = named(NamedPeriod.LAST_30_DAYS)
    assert (p30.end_day - p30.start_day).days + 1 == 30


def test_all_time_is_open_ended():
    p = named(NamedPeriod.ALL_TIME)
    assert (p.start_day, p.end_day, p.start_iso, p.end_iso) == (None, None, None, None)
    assert p.label == "All time"


# ============================================================================
# Explicit periods
# ============================================================================


def test_past_month_is_the_full_month():
    p = resolve(MonthSpec(year=2026, month=8), TODAY)
    assert (p.start_day, p.end_day) == (date(2026, 8, 1), date(2026, 8, 31))


def test_current_month_is_capped_at_today():
    p = resolve(MonthSpec(year=2026, month=9), TODAY)
    assert (p.start_day, p.end_day) == (date(2026, 9, 1), TODAY)


def test_future_month_is_rejected():
    with pytest.raises(PeriodError, match="October 2026"):
        resolve(MonthSpec(year=2026, month=10), TODAY)


def test_since_runs_to_today():
    p = resolve(SinceSpec(start=date(2026, 5, 1)), TODAY)
    assert (p.start_day, p.end_day) == (date(2026, 5, 1), TODAY)


def test_range_end_is_capped_at_today():
    p = resolve(RangeSpec(start=date(2026, 9, 1), end=date(2026, 12, 31)), TODAY)
    assert p.end_day == TODAY


def test_inverted_range_is_rejected():
    with pytest.raises(PeriodError, match="ends before it starts"):
        resolve(RangeSpec(start=date(2026, 9, 10), end=date(2026, 9, 1)), TODAY)


def test_future_start_is_rejected():
    with pytest.raises(PeriodError, match="in the future"):
        resolve(SinceSpec(start=date(2026, 9, 21)), TODAY)
    with pytest.raises(PeriodError, match="in the future"):
        resolve(DaySpec(date=date(2026, 9, 21)), TODAY)


def test_single_day():
    p = resolve(DaySpec(date=date(2026, 9, 18)), TODAY)
    assert p.is_single_day
    assert (p.start_day, p.end_day) == (date(2026, 9, 18), date(2026, 9, 18))


# ============================================================================
# UTC bounds — orders are stored as naive UTC; days are IST
# ============================================================================


def test_ist_day_maps_to_utc_bounds_offset_by_five_thirty():
    p = resolve(DaySpec(date=date(2026, 9, 18)), TODAY)

    assert p.start_utc == datetime(2026, 9, 17, 18, 30, 0)
    assert p.end_utc == datetime(2026, 9, 18, 18, 29, 59, 999999)
    assert p.start_utc.tzinfo is None and p.end_utc.tzinfo is None


def test_iso_strings_carry_no_timezone_suffix():
    """The analytics tools parse these; a trailing Z would make them tz-aware."""
    p = resolve(DaySpec(date=date(2026, 9, 18)), TODAY)
    assert p.start_iso == "2026-09-17T18:30:00"
    assert not p.end_iso.endswith("Z")


# ============================================================================
# Labels — what the owner sees, so a misread question is visible
# ============================================================================


@pytest.mark.parametrize(
    "spec, label",
    [
        (NamedSpec(name=NamedPeriod.TODAY), "Today, Sun 20 Sep"),
        (NamedSpec(name=NamedPeriod.YESTERDAY), "Yesterday, Sat 19 Sep"),
        (NamedSpec(name=NamedPeriod.THIS_WEEK), "This week so far, 14–20 Sep 2026"),
        (NamedSpec(name=NamedPeriod.LAST_WEEK), "Last week, 7–13 Sep 2026"),
        (NamedSpec(name=NamedPeriod.THIS_MONTH), "September so far, 1–20 Sep 2026"),
        (NamedSpec(name=NamedPeriod.LAST_MONTH), "August 2026"),
        (NamedSpec(name=NamedPeriod.THIS_YEAR), "2026 so far, 1 Jan – 20 Sep 2026"),
        (NamedSpec(name=NamedPeriod.LAST_7_DAYS), "Last 7 days, 14–20 Sep 2026"),
        (MonthSpec(year=2026, month=8), "August 2026"),
        (SinceSpec(start=date(2026, 5, 1)), "1 May – 20 Sep 2026"),
        (RangeSpec(start=date(2025, 12, 15), end=date(2026, 1, 10)), "15 Dec 2025 – 10 Jan 2026"),
        (DaySpec(date=date(2026, 9, 18)), "Fri 18 Sep 2026"),
    ],
)
def test_labels(spec, label):
    assert resolve(spec, TODAY).label == label
