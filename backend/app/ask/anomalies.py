"""Deterministic rules that flag an odd trading day.

Each rule asks one question — "is yesterday odd against the last month?" —
and answers it in code, from the same orders, cash counters and stock rows
the reports read. No rule forecasts, none compares against last year, and
none asks a model anything: the sentence a rule returns is a template with
computed numbers already in it.

Every rule stays silent rather than firing on thin evidence. A comparison
needs at least MIN_BASELINE_DAYS of history behind it; below that the rule
returns nothing, because "34% below usual" computed from one previous
Saturday is noise presented as a finding.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.ask.captions import count, pct, rupees
from app.core import settings_store
from app.crud.crud_analytics import get_time_filter, to_ist_timestamp
from app.models.cash_models import DailyCashCounter
from app.models.inventory_models import InventoryItem
from app.models.models import Order, OrderItem, OrderStatus

logger = logging.getLogger(__name__)

# A rule that compares against "usual" needs at least this many past
# observations of that same thing, or it stays silent.
MIN_BASELINE_DAYS = 2
# How far back the baselines look. Four weeks, not eight: a festival week or
# a closure distorts a longer window, and the owner is being asked "is
# yesterday odd", not "what is the annual trend".
BASELINE_WEEKS = 4
BASELINE_DAYS = BASELINE_WEEKS * 7

Severity = str  # "info" | "warn"


@dataclass(frozen=True)
class Flag:
    """One finding, with the numbers that produced it kept alongside."""

    rule: str
    severity: Severity
    sentence: str
    numbers: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "sentence": self.sentence,
            "numbers": self.numbers,
        }


@dataclass(frozen=True)
class DayStats:
    day: date
    revenue: float
    orders: int


@dataclass(frozen=True)
class History:
    """The target day and the trading days before it, most recent first."""

    day: date
    target: DayStats | None
    prior: list[DayStats]

    def same_weekday(self, weeks: int = BASELINE_WEEKS) -> list[DayStats]:
        return [s for s in self.prior if s.day.weekday() == self.day.weekday()][:weeks]


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------


def _revenue_by_day(db: Session, start: date, end: date) -> dict[date, DayStats]:
    """Paid revenue and order count per IST calendar day, as `best_days` counts them."""
    from app.ask.periods import ResolvedPeriod

    period = ResolvedPeriod(start, end, "")
    rows = (
        db.query(
            func.date(to_ist_timestamp(Order.created_at)).label("day"),
            func.sum(Order.total_amount).label("revenue_paise"),
            func.count(Order.id).label("orders"),
        )
        .filter(
            and_(
                Order.status == OrderStatus.PAID,
                *get_time_filter(period.start_utc, period.end_utc),
            )
        )
        .group_by("day")
        .all()
    )
    stats: dict[date, DayStats] = {}
    for row in rows:
        day = date.fromisoformat(str(row.day))
        stats[day] = DayStats(
            day=day,
            revenue=round((row.revenue_paise or 0) / 100, 2),
            orders=int(row.orders or 0),
        )
    return stats


def load_history(db: Session, day: date) -> History:
    """The target day plus the BASELINE_DAYS trading days before it."""
    start = day - timedelta(days=BASELINE_DAYS)
    stats = _revenue_by_day(db, start, day)
    prior = sorted(
        (s for d, s in stats.items() if d < day), key=lambda s: s.day, reverse=True
    )
    return History(day=day, target=stats.get(day), prior=prior)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _weekday(day: date) -> str:
    return f"{day:%A}"


# ----------------------------------------------------------------------
# Rules
#
# Each takes (db, history) and returns a Flag or None. Adding a rule means
# adding a function here and listing it in _RULES.
# ----------------------------------------------------------------------


def revenue_low(db: Session, h: History) -> Flag | None:
    baseline = h.same_weekday()
    if h.target is None or len(baseline) < MIN_BASELINE_DAYS:
        return None
    usual = _mean([s.revenue for s in baseline])
    if usual <= 0:
        return None
    threshold = settings_store.get_int("digest.revenue_low_pct", 25) / 100
    if h.target.revenue >= (1 - threshold) * usual:
        return None
    short_by = usual - h.target.revenue
    return Flag(
        rule="revenue_low",
        severity="info",
        sentence=(
            f"{_weekday(h.day)} came in {rupees(short_by)} "
            f"({pct(short_by / usual * 100)}) below your usual {_weekday(h.day)}."
        ),
        numbers={
            "revenue_rupees": h.target.revenue,
            "usual_rupees": round(usual, 2),
            "baseline_days": len(baseline),
        },
    )


def revenue_high(db: Session, h: History) -> Flag | None:
    baseline = h.same_weekday()
    if h.target is None or len(baseline) < MIN_BASELINE_DAYS:
        return None
    usual = _mean([s.revenue for s in baseline])
    if usual <= 0:
        return None
    threshold = settings_store.get_int("digest.revenue_high_pct", 40) / 100
    if h.target.revenue <= (1 + threshold) * usual:
        return None
    return Flag(
        rule="revenue_high",
        severity="info",
        sentence=(
            f"Best {_weekday(h.day)} in {BASELINE_WEEKS} weeks: {rupees(h.target.revenue)}, "
            f"{pct((h.target.revenue - usual) / usual * 100)} above usual."
        ),
        numbers={
            "revenue_rupees": h.target.revenue,
            "usual_rupees": round(usual, 2),
            "baseline_days": len(baseline),
        },
    )


def cancellations_spike(db: Session, h: History) -> Flag | None:
    from app.ask.periods import ResolvedPeriod

    start = h.day - timedelta(days=BASELINE_DAYS)
    period = ResolvedPeriod(start, h.day, "")
    rows = (
        db.query(
            func.date(to_ist_timestamp(Order.created_at)).label("day"),
            func.count(Order.id).label("cancels"),
        )
        .filter(
            and_(
                Order.status == OrderStatus.CANCELED,
                *get_time_filter(period.start_utc, period.end_utc),
            )
        )
        .group_by("day")
        .all()
    )
    by_day = {date.fromisoformat(str(r.day)): int(r.cancels) for r in rows}
    yesterday = by_day.get(h.day, 0)
    if yesterday < 3:
        return None
    # Mean over every prior trading day, counting zero-cancellation days.
    trading = [s.day for s in h.prior]
    if len(trading) < MIN_BASELINE_DAYS:
        return None
    usual = _mean([float(by_day.get(d, 0)) for d in trading])
    if yesterday < 2 * usual:
        return None
    return Flag(
        rule="cancellations_spike",
        severity="info",
        sentence=(
            f"{count(yesterday, 'order')} cancelled yesterday, "
            f"against a usual {usual:.1f} a day."
        ),
        numbers={"cancellations": yesterday, "usual_per_day": round(usual, 2)},
    )


def cash_short_streak(db: Session, h: History) -> Flag | None:
    need = settings_store.get_int("digest.cash_short_days", 3)
    if need < 1:
        return None
    # "Closed" is whatever the cash counter screen calls closed — see
    # DailyCashCounter.status, which keys off closing_balance, not closed_at.
    rows = (
        db.query(DailyCashCounter)
        .filter(
            DailyCashCounter.date <= h.day,
            DailyCashCounter.closing_balance.isnot(None),
        )
        .order_by(DailyCashCounter.date.desc())
        .limit(need)
        .all()
    )
    if len(rows) < need or rows[0].date != h.day:
        return None
    shortfalls = [float(r.variance) for r in rows if r.variance is not None]
    if len(shortfalls) < need or not all(v < 0 for v in shortfalls):
        return None
    amounts = ", ".join(rupees(abs(v)) for v in shortfalls)
    return Flag(
        rule="cash_short_streak",
        severity="warn",
        sentence=f"Cash has closed short {count(need, 'day')} running: {amounts}.",
        numbers={"days": need, "shortfalls_rupees": [abs(v) for v in shortfalls]},
    )


def cash_not_closed(db: Session, h: History) -> Flag | None:
    counter = db.query(DailyCashCounter).filter(DailyCashCounter.date == h.day).first()
    # Same definition as DailyCashCounter.status, so this rule can never
    # contradict the digest's own cash line.
    if counter is None or counter.status != "open":
        return None
    return Flag(
        rule="cash_not_closed",
        severity="warn",
        sentence="Yesterday's cash counter was opened but never closed.",
        numbers={"opening_balance_rupees": float(counter.opening_balance or 0)},
    )


def dish_stalled(db: Session, h: History) -> Flag | None:
    from app.ask.periods import ResolvedPeriod

    quiet_days = settings_store.get_int("digest.dish_stalled_days", 5)
    if quiet_days < 1:
        return None

    window_start = h.day - timedelta(days=BASELINE_DAYS)
    period = ResolvedPeriod(window_start, h.day, "")
    rows = (
        db.query(
            OrderItem.menu_item_name.label("name"),
            func.date(to_ist_timestamp(Order.created_at)).label("day"),
            func.sum(OrderItem.quantity).label("qty"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            and_(
                Order.status == OrderStatus.PAID,
                *get_time_filter(period.start_utc, period.end_utc),
            )
        )
        .group_by("name", "day")
        .all()
    )

    quiet_from = h.day - timedelta(days=quiet_days - 1)
    sold_before: dict[str, list[float]] = {}
    sold_recently: set[str] = set()
    for row in rows:
        day = date.fromisoformat(str(row.day))
        qty = float(row.qty or 0)
        if day >= quiet_from:
            if qty > 0:
                sold_recently.add(row.name)
        else:
            sold_before.setdefault(row.name, []).append(qty)

    # Days the cafe actually traded before the quiet window — the divisor for
    # "usually sells N a day". Closed days must not count as zero-sale days.
    trading_before = [s.day for s in h.prior if s.day < quiet_from]
    if len(trading_before) < MIN_BASELINE_DAYS:
        return None

    stalled: list[tuple[str, float]] = []
    for name, quantities in sold_before.items():
        if name in sold_recently:
            continue
        per_day = sum(quantities) / len(trading_before)
        if per_day >= 1.0:
            stalled.append((name, per_day))
    if not stalled:
        return None

    name, per_day = max(stalled, key=lambda pair: pair[1])
    return Flag(
        rule="dish_stalled",
        severity="info",
        sentence=(
            f"{name} hasn't sold in {count(quiet_days, 'day')}; "
            f"it usually sells {per_day:.1f} a day."
        ),
        numbers={"dish": name, "quiet_days": quiet_days, "usual_per_day": round(per_day, 2)},
    )


def low_stock(db: Session, h: History) -> Flag | None:
    items = (
        db.query(InventoryItem)
        .filter(
            InventoryItem.is_active.is_(True),
            InventoryItem.current_quantity < InventoryItem.min_threshold,
        )
        .order_by(InventoryItem.name)
        .all()
    )
    if not items:
        return None
    if len(items) == 1:
        item = items[0]
        sentence = (
            f"{item.name} is at {float(item.current_quantity):g} {item.unit} "
            f"(reorder at {float(item.min_threshold):g})."
        )
    else:
        names = ", ".join(i.name for i in items[:3])
        more = f" and {len(items) - 3} more" if len(items) > 3 else ""
        sentence = f"{names}{more} are below reorder level."
    return Flag(
        rule="low_stock",
        severity="warn",
        sentence=sentence,
        numbers={
            "items": [
                {
                    "name": i.name,
                    "quantity": float(i.current_quantity or 0),
                    "min_threshold": float(i.min_threshold or 0),
                    "unit": i.unit,
                }
                for i in items
            ]
        },
    )


def aov_shift(db: Session, h: History) -> Flag | None:
    if h.target is None or not h.target.orders:
        return None
    if len(h.prior) < MIN_BASELINE_DAYS:
        return None
    prior_orders = sum(s.orders for s in h.prior)
    if not prior_orders:
        return None
    usual = sum(s.revenue for s in h.prior) / prior_orders
    if usual <= 0:
        return None
    yesterday = h.target.revenue / h.target.orders
    threshold = settings_store.get_int("digest.aov_shift_pct", 20) / 100
    change = (yesterday - usual) / usual
    if abs(change) <= threshold:
        return None
    direction = "up" if change > 0 else "down"
    return Flag(
        rule="aov_shift",
        severity="info",
        sentence=(
            f"Average order was {rupees(yesterday)} yesterday, "
            f"{direction} from a usual {rupees(usual)}."
        ),
        numbers={
            "average_order_value_rupees": round(yesterday, 2),
            "usual_rupees": round(usual, 2),
        },
    )


_RULES = (
    revenue_low,
    revenue_high,
    cancellations_spike,
    cash_short_streak,
    cash_not_closed,
    dish_stalled,
    low_stock,
    aov_shift,
)


def evaluate(db: Session, day: date, history: History | None = None) -> list[Flag]:
    """Run every rule against `day`. A rule that raises is skipped, not fatal.

    A broken rule must not cost the owner the rest of the digest, so each is
    isolated: the failure is logged and the other seven still report.
    """
    h = history or load_history(db, day)
    flags: list[Flag] = []
    for rule in _RULES:
        try:
            flag = rule(db, h)
        except Exception:
            logger.exception("Anomaly rule %s failed for %s", rule.__name__, day)
            continue
        if flag is not None:
            flags.append(flag)
    # warn before info, otherwise in rule order.
    return sorted(flags, key=lambda f: 0 if f.severity == "warn" else 1)
