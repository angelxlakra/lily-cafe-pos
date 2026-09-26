"""The morning digest: what the owner is told without having to ask.

Every sentence here is composed by code from a report in the v1 registry,
using the v1 caption helpers, so the digest and the Ask cards round and
format a figure identically. The v1 invariant carries over unchanged: a
model never produces a figure, and in v2 a model is not involved at all.

A day the cafe did not trade produces no digest. A closed day is not an
anomaly, and a digest saying "no sales yesterday" every Monday trains the
owner to ignore the digest.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.ask.anomalies import Flag, evaluate, load_history
from app.ask.captions import count, pct, rupees
from app.ask.periods import ResolvedPeriod, today_ist
from app.ask.reports import REPORTS, ReportContext
from app.core import settings_store
from app.models.digest_models import DailyDigest

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DigestLine:
    kind: str
    text: str
    numbers: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Digest:
    date: date
    lines: list[DigestLine]
    flags: list[Flag]

    @property
    def sentences(self) -> list[str]:
        return [line.text for line in self.lines] + [f.sentence for f in self.flags]

    def as_dict(self) -> dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "lines": [asdict(line) for line in self.lines],
            "flags": [f.as_dict() for f in self.flags],
        }


def yesterday_ist(today: date | None = None) -> date:
    return (today or today_ist()) - timedelta(days=1)


def _single_day(day: date) -> ResolvedPeriod:
    return ResolvedPeriod(day, day, f"{day:%a %-d %b %Y}")


def _run(db: Session, report_id: str, period: ResolvedPeriod | None, limit: int = 10) -> dict:
    """Run a v1 report, returning {} if it fails rather than losing the digest."""
    try:
        return REPORTS[report_id].run(db, ReportContext(period, None, None, limit))
    except Exception:
        logger.exception("Digest could not run report %s", report_id)
        return {}


# ----------------------------------------------------------------------
# Lines
# ----------------------------------------------------------------------


def _revenue_line(db: Session, day: date, history) -> DigestLine | None:
    target = history.target
    if target is None or not target.orders:
        return None

    head = f"Yesterday {rupees(target.revenue)} from {count(target.orders, 'order')}"
    numbers: dict[str, Any] = {"revenue_rupees": target.revenue, "orders": target.orders}

    baseline = history.same_weekday()
    # Fewer than two comparable days is not a baseline; say the figure plainly
    # rather than compute "up 40%" off a single previous week.
    if len(baseline) >= 2:
        usual = sum(s.revenue for s in baseline) / len(baseline)
        if usual > 0:
            change = (target.revenue - usual) / usual * 100
            direction = "above" if change >= 0 else "below"
            head += f" — {pct(abs(change))} {direction} your usual {day:%A}"
            numbers |= {"usual_rupees": round(usual, 2), "baseline_days": len(baseline)}
    return DigestLine(kind="revenue", text=head + ".", numbers=numbers)


def _top_item_line(db: Session, day: date) -> DigestLine | None:
    data = _run(db, "top_items", _single_day(day), limit=1)
    items = data.get("top_products") or []
    if not items:
        return None
    first = items[0]
    return DigestLine(
        kind="top_item",
        text=f"{first['name']} sold best: {count(first['quantity_sold'], 'portion')}.",
        numbers={"name": first["name"], "quantity_sold": first["quantity_sold"]},
    )


def _cash_line(db: Session, day: date) -> DigestLine | None:
    data = _run(db, "cash_counter", _single_day(day))
    # No counter recorded is silence, not a warning — the cash_not_closed rule
    # covers the case where one was opened and left open.
    if not data or data.get("error") or data.get("closing_balance_rupees") is None:
        return None
    variance = data.get("variance_rupees") or 0
    if not variance:
        text = "Cash balanced exactly."
    else:
        word = "over" if variance > 0 else "short"
        text = f"Cash was {rupees(abs(variance))} {word}."
    return DigestLine(kind="cash", text=text, numbers={"variance_rupees": variance})


def _stock_line(db: Session, day: date) -> DigestLine | None:
    data = _run(db, "inventory_status", None)
    low = data.get("low_stock_items") or []
    if not low:
        return None
    names = [item["name"] for item in low]
    if len(names) == 1:
        listed = names[0]
    elif len(names) <= 3:
        listed = ", ".join(names[:-1]) + f" and {names[-1]}"
    else:
        listed = ", ".join(names[:3]) + f" and {len(names) - 3} more"
    verb = "is" if len(names) == 1 else "are"
    return DigestLine(
        kind="stock",
        text=f"{listed} {verb} below reorder level.",
        numbers={"count": len(names), "items": names},
    )


def _month_line(db: Session, day: date) -> DigestLine | None:
    start = day.replace(day=1)
    period = ResolvedPeriod(start, day, f"{start:%B} so far")
    data = _run(db, "sales_summary", period)
    if not data.get("total_orders"):
        return None
    return DigestLine(
        kind="month",
        text=(
            f"{start:%B} so far: {rupees(data['total_revenue_rupees'])} "
            f"across {count(data['total_orders'], 'order')}."
        ),
        numbers={
            "revenue_rupees": data["total_revenue_rupees"],
            "orders": data["total_orders"],
        },
    )


# ----------------------------------------------------------------------
# Composition
# ----------------------------------------------------------------------


# A line and a flag that say the same thing make the digest argue with
# itself. Where the two overlap, the one carrying more detail wins:
#
#   revenue line  >  revenue_low / revenue_high  (the line adds the order count)
#   low_stock flag > stock line                  (the flag adds the quantities)
#
# The rules themselves are untouched — `evaluate` still returns everything,
# and this only decides what the digest shows.
_FLAGS_COVERED_BY_REVENUE_LINE = frozenset({"revenue_low", "revenue_high"})
_LINE_COVERED_BY_LOW_STOCK = "stock"


def _deduplicate(lines: list[DigestLine], flags: list[Flag]) -> tuple[list[DigestLine], list[Flag]]:
    rules = {f.rule for f in flags}

    if "low_stock" in rules:
        lines = [line for line in lines if line.kind != _LINE_COVERED_BY_LOW_STOCK]

    # Only when the revenue line actually carries the comparison — without a
    # baseline it states the figure alone and supersedes nothing.
    revenue_line = next((line for line in lines if line.kind == "revenue"), None)
    if revenue_line is not None and "usual_rupees" in revenue_line.numbers:
        flags = [f for f in flags if f.rule not in _FLAGS_COVERED_BY_REVENUE_LINE]

    return lines, flags


def build_digest(db: Session, day: date) -> Digest | None:
    """Compose the digest for `day`, or None if the cafe did not trade."""
    history = load_history(db, day)
    if history.target is None or not history.target.orders:
        logger.info("No sales on %s — no digest", day)
        return None

    builders = (_revenue_line, _top_item_line, _cash_line, _stock_line, _month_line)
    lines: list[DigestLine] = []
    for build in builders:
        try:
            line = build(db, day, history) if build is _revenue_line else build(db, day)
        except Exception:
            logger.exception("Digest line %s failed for %s", build.__name__, day)
            continue
        if line is not None:
            lines.append(line)

    lines, flags = _deduplicate(lines, evaluate(db, day, history))
    return Digest(date=day, lines=lines, flags=flags)


# ----------------------------------------------------------------------
# Storage
# ----------------------------------------------------------------------


def get_stored(db: Session, day: date) -> DailyDigest | None:
    return db.query(DailyDigest).filter(DailyDigest.date == day).first()


def latest_stored(db: Session) -> DailyDigest | None:
    return db.query(DailyDigest).order_by(DailyDigest.date.desc()).first()


def store(db: Session, digest: Digest) -> DailyDigest:
    """Insert or refresh the stored digest for its day.

    The unique `date` column is what makes a digest run idempotent: a second
    run for the same day overwrites rather than adding a duplicate.
    """
    row = get_stored(db, digest.date)
    if row is None:
        row = DailyDigest(date=digest.date, body_json=json.dumps(digest.as_dict()))
        db.add(row)
    else:
        row.body_json = json.dumps(digest.as_dict())
    db.commit()
    db.refresh(row)
    return row


def as_payload(row: DailyDigest) -> dict[str, Any]:
    body = json.loads(row.body_json)
    body["email_sent_at"] = row.email_sent_at.isoformat() if row.email_sent_at else None
    return body


# ----------------------------------------------------------------------
# Email
# ----------------------------------------------------------------------


def email_recipients() -> list[str]:
    raw = settings_store.get("digest.email_to") or settings_store.get("restaurant.email")
    return [address.strip() for address in raw.split(",") if address.strip()]


def build_email_html(digest: Digest) -> str:
    """The same sentences as the in-app card. Charts are one tap away in Ask."""
    cafe = settings_store.get("restaurant.name")
    items = "".join(
        f'<li style="margin-bottom:8px;line-height:1.5;">{sentence}</li>'
        for sentence in digest.sentences
    )
    return (
        '<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;'
        'max-width:520px;margin:0 auto;padding:24px;color:#2b2320;">'
        f'<h2 style="margin:0 0 4px;font-size:18px;">{cafe}</h2>'
        f'<p style="margin:0 0 20px;color:#8a7d76;font-size:14px;">'
        f'{digest.date:%A, %-d %B %Y}</p>'
        f'<ul style="padding-left:20px;margin:0;font-size:15px;">{items}</ul>'
        '</div>'
    )


def send_digest_email(db: Session, digest: Digest, row: DailyDigest) -> bool:
    if not (settings_store.get_bool("smtp.enabled") and settings_store.get_bool("digest.email_enabled")):
        return False
    recipients = email_recipients()
    if not recipients:
        logger.warning("Digest email enabled but no recipient configured")
        return False

    from app.utils.email_sender import send_email

    subject = f"{settings_store.get('restaurant.name')} — {digest.date:%a %-d %b}"
    if not send_email(subject, build_email_html(digest), recipients):
        return False
    row.email_sent_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    return True


# ----------------------------------------------------------------------
# The run
# ----------------------------------------------------------------------


def run_for(db: Session, day: date, *, force: bool = False) -> DailyDigest | None:
    """Build, store and (if configured) email the digest for `day`.

    Idempotent: an existing digest for the day is returned untouched unless
    `force`, so a restart or a duplicate trigger cannot send two emails.
    """
    existing = get_stored(db, day)
    if existing is not None and not force:
        logger.info("Digest for %s already exists", day)
        return existing

    digest = build_digest(db, day)
    if digest is None:
        return None

    row = store(db, digest)
    if row.email_sent_at is None:
        send_digest_email(db, digest, row)
    return row
