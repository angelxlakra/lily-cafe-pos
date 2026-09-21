"""The morning digest and its anomaly rules.

Every rule is checked three ways: it fires when it should, it stays quiet
when the day is ordinary, and it stays quiet when there is too little
history to judge — the third being the one that matters, since a rule that
fires off one previous Saturday is worse than no rule.
"""

from datetime import UTC, date, datetime, time, timedelta

import pytest

from app.ask import anomalies
from app.ask import digest as digest_service
from app.ask.periods import IST
from app.ask.scheduler import parse_send_at, seconds_until
from app.core import settings_store
from app.models.cash_models import DailyCashCounter
from app.models.inventory_models import InventoryItem
from app.models.models import (
    Category,
    MenuItem,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentMethod,
)

# A Saturday, so the same-weekday baseline has a name worth printing.
TARGET = date(2026, 9, 19)
assert TARGET.strftime("%A") == "Saturday"


@pytest.fixture(autouse=True)
def _default_settings():
    """Start every test from DEFAULTS, not whatever another test cached."""
    settings_store._cache = {}
    yield
    settings_store._cache = {}


def override(**values: str) -> None:
    settings_store._cache = dict(settings_store.DEFAULTS) | values


def _ist(day: date, hour: int = 11) -> datetime:
    return datetime(day.year, day.month, day.day, hour, tzinfo=IST).astimezone(UTC).replace(tzinfo=None)


@pytest.fixture
def menu(db_session):
    category = Category(name="Beverages")
    db_session.add(category)
    db_session.flush()
    items = {
        name: MenuItem(name=name, price=price, category_id=category.id, is_beverage=True)
        for name, price in (("Masala Chai", 3000), ("Filter Coffee", 4000), ("Rava Dosa", 6000))
    }
    db_session.add_all(items.values())
    db_session.flush()
    db_session.commit()
    return items


def sell(db_session, menu, day, *, revenue=5000.0, orders=4, dish="Masala Chai", qty=2):
    """Record `orders` paid orders on `day` summing to `revenue` rupees."""
    per_order = int(round(revenue * 100 / orders))
    item = menu[dish]
    for n in range(orders):
        order = Order(
            order_number=f"{day:%Y%m%d}-{dish[:2]}-{n}",
            table_number=(n % 10) + 1,
            subtotal=per_order,
            gst_amount=0,
            total_amount=per_order,
            status=OrderStatus.PAID,
            created_at=_ist(day),
        )
        db_session.add(order)
        db_session.flush()
        db_session.add(OrderItem(
            order_id=order.id, menu_item_id=item.id, menu_item_name=item.name,
            quantity=qty, unit_price=item.price, subtotal=per_order, is_beverage=True,
        ))
        db_session.add(Payment(order_id=order.id, payment_method=PaymentMethod.UPI, amount=per_order))
    db_session.commit()


def steady(db_session, menu, *, days=35, revenue=5000.0, orders=4, through=None, **kwargs):
    """A calm month of identical trading days ending the day before `through`."""
    end = through or TARGET
    for offset in range(1, days + 1):
        sell(db_session, menu, end - timedelta(days=offset), revenue=revenue, orders=orders, **kwargs)


def flags_for(db_session, day=TARGET) -> dict[str, anomalies.Flag]:
    return {f.rule: f for f in anomalies.evaluate(db_session, day)}


# ----------------------------------------------------------------------
# revenue_low / revenue_high
# ----------------------------------------------------------------------


def test_revenue_low_fires_on_a_weak_saturday(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET, revenue=2000.0)

    flag = flags_for(db_session)["revenue_low"]

    assert "below your usual Saturday" in flag.sentence
    assert flag.numbers["revenue_rupees"] == 2000.0
    assert flag.numbers["usual_rupees"] == 5000.0
    assert flag.severity == "info"


def test_revenue_low_silent_on_an_ordinary_saturday(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET, revenue=4800.0)

    assert "revenue_low" not in flags_for(db_session)


def test_revenue_low_silent_with_one_previous_saturday(db_session, menu):
    """One comparable day is not a baseline — 60% down off it is noise."""
    sell(db_session, menu, TARGET - timedelta(days=7), revenue=5000.0)
    sell(db_session, menu, TARGET, revenue=2000.0)

    assert "revenue_low" not in flags_for(db_session)


def test_revenue_high_fires_on_a_strong_saturday(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET, revenue=9000.0)

    flag = flags_for(db_session)["revenue_high"]

    assert "above usual" in flag.sentence
    assert flag.numbers["usual_rupees"] == 5000.0


def test_revenue_thresholds_come_from_settings(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET, revenue=4000.0)  # 20% down

    assert "revenue_low" not in flags_for(db_session)  # default threshold is 25%

    override(**{"digest.revenue_low_pct": "10"})
    assert "revenue_low" in flags_for(db_session)


# ----------------------------------------------------------------------
# cancellations_spike
# ----------------------------------------------------------------------


def cancel(db_session, day, count):
    for n in range(count):
        db_session.add(Order(
            order_number=f"X-{day:%Y%m%d}-{n}", table_number=1, subtotal=0, gst_amount=0,
            total_amount=0, status=OrderStatus.CANCELED, created_at=_ist(day),
        ))
    db_session.commit()


def test_cancellations_spike_fires(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET)
    for offset in range(1, 15):
        cancel(db_session, TARGET - timedelta(days=offset), 1)
    cancel(db_session, TARGET, 5)

    flag = flags_for(db_session)["cancellations_spike"]

    assert flag.numbers["cancellations"] == 5


def test_cancellations_spike_needs_at_least_three(db_session, menu):
    """Two cancellations against a usual zero is doubling, and still not news."""
    steady(db_session, menu)
    sell(db_session, menu, TARGET)
    cancel(db_session, TARGET, 2)

    assert "cancellations_spike" not in flags_for(db_session)


def test_cancellations_spike_silent_when_normal(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET)
    # Across the whole baseline window: a day left out counts as zero
    # cancellations and would drag the mean down into a false spike.
    for offset in range(0, anomalies.BASELINE_DAYS + 1):
        cancel(db_session, TARGET - timedelta(days=offset), 4)

    assert "cancellations_spike" not in flags_for(db_session)


# ----------------------------------------------------------------------
# cash
# ----------------------------------------------------------------------


def counter(db_session, day, *, variance=None, closed=True, opening=1000):
    db_session.add(DailyCashCounter(
        date=day, opening_balance=opening,
        closing_balance=2000 if closed else None,
        expected_closing=2000 if closed else None,
        variance=variance, opened_by="owner",
        closed_by="owner" if closed else None,
        closed_at=_ist(day, 22) if closed else None,
    ))
    db_session.commit()


def test_cash_short_streak_fires_on_three_short_days(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET)
    for offset, amount in ((2, -50), (1, -100), (0, -70)):
        counter(db_session, TARGET - timedelta(days=offset), variance=amount)

    flag = flags_for(db_session)["cash_short_streak"]

    assert flag.severity == "warn"
    assert "three days running" in flag.sentence or "3 days running" in flag.sentence
    assert flag.numbers["shortfalls_rupees"] == [70.0, 100.0, 50.0]


def test_cash_short_streak_broken_by_a_balanced_day(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET)
    for offset, amount in ((2, -50), (1, 0), (0, -70)):
        counter(db_session, TARGET - timedelta(days=offset), variance=amount)

    assert "cash_short_streak" not in flags_for(db_session)


def test_cash_not_closed_fires(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET)
    counter(db_session, TARGET, closed=False)

    flag = flags_for(db_session)["cash_not_closed"]

    assert flag.severity == "warn"
    assert "never closed" in flag.sentence


def test_no_cash_counter_is_silence_not_a_warning(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET)

    found = flags_for(db_session)

    assert "cash_not_closed" not in found
    assert "cash_short_streak" not in found


# ----------------------------------------------------------------------
# dish_stalled
# ----------------------------------------------------------------------


def test_dish_stalled_fires_for_a_dish_that_stopped(db_session, menu):
    # Rava Dosa sells every day up to five days ago, then stops.
    for offset in range(5, 30):
        sell(db_session, menu, TARGET - timedelta(days=offset), dish="Rava Dosa", qty=3, orders=1)
    for offset in range(0, 5):
        sell(db_session, menu, TARGET - timedelta(days=offset), dish="Masala Chai", orders=1)

    flag = flags_for(db_session)["dish_stalled"]

    assert flag.numbers["dish"] == "Rava Dosa"
    assert "hasn't sold" in flag.sentence


def test_dish_stalled_silent_when_the_dish_still_sells(db_session, menu):
    for offset in range(0, 30):
        sell(db_session, menu, TARGET - timedelta(days=offset), dish="Rava Dosa", qty=3, orders=1)

    assert "dish_stalled" not in flags_for(db_session)


def test_dish_stalled_ignores_a_dish_that_never_sold_daily(db_session, menu):
    """A dish selling once a fortnight has not 'stalled' after five quiet days."""
    sell(db_session, menu, TARGET - timedelta(days=20), dish="Rava Dosa", qty=1, orders=1)
    for offset in range(0, 6):
        sell(db_session, menu, TARGET - timedelta(days=offset), dish="Masala Chai", orders=1)

    assert "dish_stalled" not in flags_for(db_session)


# ----------------------------------------------------------------------
# low_stock
# ----------------------------------------------------------------------


def test_low_stock_fires_and_warns(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET)
    db_session.add_all([
        InventoryItem(name="Milk", unit="L", current_quantity=4, min_threshold=15),
        InventoryItem(name="Paneer", unit="kg", current_quantity=1, min_threshold=5),
    ])
    db_session.commit()

    flag = flags_for(db_session)["low_stock"]

    assert flag.severity == "warn"
    assert "Milk" in flag.sentence and "Paneer" in flag.sentence


def test_low_stock_silent_when_everything_is_stocked(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET)
    db_session.add(InventoryItem(name="Milk", unit="L", current_quantity=40, min_threshold=15))
    db_session.commit()

    assert "low_stock" not in flags_for(db_session)


# ----------------------------------------------------------------------
# aov_shift
# ----------------------------------------------------------------------


def test_aov_shift_fires_when_the_basket_shrinks(db_session, menu):
    steady(db_session, menu, revenue=5000.0, orders=4)   # ₹1,250 an order
    sell(db_session, menu, TARGET, revenue=4000.0, orders=8)  # ₹500 an order

    flag = flags_for(db_session)["aov_shift"]

    assert flag.numbers["average_order_value_rupees"] == 500.0
    assert "down from" in flag.sentence


def test_aov_shift_silent_when_steady(db_session, menu):
    steady(db_session, menu, revenue=5000.0, orders=4)
    sell(db_session, menu, TARGET, revenue=5000.0, orders=4)

    assert "aov_shift" not in flags_for(db_session)


# ----------------------------------------------------------------------
# A broken rule must not cost the digest
# ----------------------------------------------------------------------


def test_one_failing_rule_does_not_lose_the_others(db_session, menu, monkeypatch):
    steady(db_session, menu)
    sell(db_session, menu, TARGET, revenue=2000.0)

    def explode(db, h):
        raise RuntimeError("bad rule")

    monkeypatch.setattr(anomalies, "_RULES", (explode, anomalies.revenue_low))

    assert [f.rule for f in anomalies.evaluate(db_session, TARGET)] == ["revenue_low"]


# ----------------------------------------------------------------------
# Digest composition
# ----------------------------------------------------------------------


def test_digest_composes_the_expected_lines(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET, revenue=6000.0, orders=5)
    counter(db_session, TARGET, variance=0)

    digest = digest_service.build_digest(db_session, TARGET)

    kinds = [line.kind for line in digest.lines]
    assert kinds == ["revenue", "top_item", "cash", "month"]
    assert "Yesterday ₹6,000 from 5 orders" in digest.lines[0].text
    assert "your usual Saturday" in digest.lines[0].text
    assert digest.lines[2].text == "Cash balanced exactly."


def test_digest_omits_lines_with_nothing_to_say(db_session, menu):
    """No cash counter means no cash line — not a line saying there isn't one."""
    steady(db_session, menu)
    sell(db_session, menu, TARGET)

    digest = digest_service.build_digest(db_session, TARGET)

    assert "cash" not in [line.kind for line in digest.lines]
    assert "stock" not in [line.kind for line in digest.lines]


def test_digest_drops_the_comparison_without_a_baseline(db_session, menu):
    sell(db_session, menu, TARGET, revenue=6000.0, orders=5)

    digest = digest_service.build_digest(db_session, TARGET)

    assert digest.lines[0].text == "Yesterday ₹6,000 from 5 orders."
    assert "usual" not in digest.lines[0].text


def test_a_closed_day_produces_no_digest(db_session, menu):
    steady(db_session, menu)

    assert digest_service.build_digest(db_session, TARGET) is None


def test_digest_numbers_match_the_sentences(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET, revenue=6000.0, orders=5)

    digest = digest_service.build_digest(db_session, TARGET)
    revenue = next(line for line in digest.lines if line.kind == "revenue")

    assert revenue.numbers["revenue_rupees"] == 6000.0
    assert revenue.numbers["orders"] == 5


# ----------------------------------------------------------------------
# Storage and the run
# ----------------------------------------------------------------------


def test_run_is_idempotent(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET)

    first = digest_service.run_for(db_session, TARGET)
    second = digest_service.run_for(db_session, TARGET)

    assert first.id == second.id
    assert db_session.query(digest_service.DailyDigest).count() == 1


def test_run_skips_a_day_with_no_trading(db_session, menu):
    steady(db_session, menu)

    assert digest_service.run_for(db_session, TARGET) is None
    assert db_session.query(digest_service.DailyDigest).count() == 0


def test_stored_payload_round_trips(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET, revenue=2000.0)

    counter(db_session, TARGET, closed=False)

    row = digest_service.run_for(db_session, TARGET)
    payload = digest_service.as_payload(row)

    assert payload["date"] == TARGET.isoformat()
    assert payload["email_sent_at"] is None
    assert any(f["rule"] == "cash_not_closed" for f in payload["flags"])


# ----------------------------------------------------------------------
# Email
# ----------------------------------------------------------------------


def test_email_body_is_the_same_sentences_as_the_card(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET, revenue=2000.0)

    digest = digest_service.build_digest(db_session, TARGET)
    html = digest_service.build_email_html(digest)

    for sentence in digest.sentences:
        assert sentence in html
    assert digest.sentences, "a digest with no sentences would pass vacuously"


def test_email_is_not_sent_unless_both_switches_are_on(db_session, menu, monkeypatch):
    steady(db_session, menu)
    sell(db_session, menu, TARGET)
    sent = []
    monkeypatch.setattr(
        "app.utils.email_sender.send_email",
        lambda *a, **k: sent.append(a) or True,
    )

    override(**{"smtp.enabled": "true", "digest.email_enabled": "false"})
    digest_service.run_for(db_session, TARGET, force=True)

    assert sent == []


def test_email_sent_when_enabled_and_recorded_once(db_session, menu, monkeypatch):
    steady(db_session, menu)
    sell(db_session, menu, TARGET)
    sent = []
    monkeypatch.setattr(
        "app.utils.email_sender.send_email",
        lambda *a, **k: sent.append(a) or True,
    )
    override(**{
        "smtp.enabled": "true",
        "digest.email_enabled": "true",
        "digest.email_to": "owner@lilycafe.com",
    })

    row = digest_service.run_for(db_session, TARGET)
    assert len(sent) == 1
    assert row.email_sent_at is not None

    # A second run must not re-send.
    digest_service.run_for(db_session, TARGET)
    assert len(sent) == 1


def test_email_recipient_falls_back_to_the_restaurant_address(db_session):
    override(**{"digest.email_to": "", "restaurant.email": "hello@lilycafe.com"})

    assert digest_service.email_recipients() == ["hello@lilycafe.com"]


# ----------------------------------------------------------------------
# Scheduler time maths
# ----------------------------------------------------------------------


def test_send_at_parses_and_falls_back():
    assert parse_send_at("07:30") == time(7, 30)
    assert parse_send_at("garbage") == time(8, 0)


def test_seconds_until_next_send_time():
    now = datetime(2026, 9, 20, 6, 0, tzinfo=IST)

    assert seconds_until(time(8, 0), now) == 2 * 3600


def test_seconds_until_rolls_over_when_the_time_has_passed():
    now = datetime(2026, 9, 20, 9, 0, tzinfo=IST)

    assert seconds_until(time(8, 0), now) == 23 * 3600


def test_yesterday_is_an_ist_calendar_day():
    # 03:00 IST on the 20th is still the 19th in UTC; yesterday must be the 19th.
    assert digest_service.yesterday_ist(date(2026, 9, 20)) == date(2026, 9, 19)


# ----------------------------------------------------------------------
# GET /api/v1/ask/digest
# ----------------------------------------------------------------------


def test_digest_endpoint_requires_auth(client):
    assert client.get("/api/v1/ask/digest").status_code == 401


def test_digest_endpoint_forbidden_for_admin(client, auth_headers):
    assert client.get("/api/v1/ask/digest", headers=auth_headers).status_code == 403


def test_digest_endpoint_returns_null_before_any_run(client, owner_headers):
    response = client.get("/api/v1/ask/digest", headers=owner_headers)

    assert response.status_code == 200
    assert response.json()["digest"] is None


def test_digest_endpoint_returns_the_latest(client, owner_headers, test_db):
    category = Category(name="Beverages")
    test_db.add(category)
    test_db.flush()
    chai = MenuItem(name="Masala Chai", price=3000, category_id=category.id, is_beverage=True)
    test_db.add(chai)
    test_db.flush()
    test_db.commit()
    sell(test_db, {"Masala Chai": chai}, TARGET, revenue=6000.0, orders=5)
    digest_service.run_for(test_db, TARGET)

    body = client.get("/api/v1/ask/digest", headers=owner_headers).json()["digest"]

    assert body["date"] == TARGET.isoformat()
    assert any(line["kind"] == "revenue" for line in body["lines"])


def test_digest_endpoint_works_without_a_model_configured(client, owner_headers, monkeypatch):
    """The digest is pure code — a server with no OPENAI_API_KEY still serves it."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

    assert client.get("/api/v1/ask/digest", headers=owner_headers).status_code == 200


# ----------------------------------------------------------------------
# Lines and flags must not repeat each other
# ----------------------------------------------------------------------


def test_revenue_flag_is_dropped_when_the_line_already_compares(db_session, menu):
    """The revenue line carries the same comparison plus the order count."""
    steady(db_session, menu)
    sell(db_session, menu, TARGET, revenue=2000.0)

    digest = digest_service.build_digest(db_session, TARGET)

    assert "revenue_low" in flags_for(db_session)  # the rule still fires
    assert "revenue_low" not in {f.rule for f in digest.flags}  # the digest shows it once
    assert "below your usual Saturday" in digest.lines[0].text


def test_revenue_flag_is_kept_when_the_line_has_no_baseline(db_session, menu):
    """Without a baseline the line states the figure alone, so it supersedes nothing."""
    steady(db_session, menu)
    sell(db_session, menu, TARGET, revenue=2000.0)
    digest = digest_service.build_digest(db_session, TARGET)
    assert "usual" in digest.lines[0].text

    # Same weak day, but with only one comparable Saturday behind it.
    for order in db_session.query(Order).all():
        db_session.delete(order)
    db_session.commit()
    sell(db_session, menu, TARGET - timedelta(days=7), revenue=5000.0)
    sell(db_session, menu, TARGET, revenue=2000.0)

    digest = digest_service.build_digest(db_session, TARGET)

    assert "usual" not in digest.lines[0].text
    assert "revenue_low" not in {f.rule for f in digest.flags}  # rule is silent too


def test_stock_line_gives_way_to_the_richer_low_stock_flag(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET)
    db_session.add(InventoryItem(name="Milk", unit="L", current_quantity=4, min_threshold=15))
    db_session.commit()

    digest = digest_service.build_digest(db_session, TARGET)

    assert "stock" not in [line.kind for line in digest.lines]
    flag = next(f for f in digest.flags if f.rule == "low_stock")
    assert "4 L" in flag.sentence and "reorder at 15" in flag.sentence


def test_no_sentence_is_repeated_in_a_full_digest(db_session, menu):
    steady(db_session, menu)
    sell(db_session, menu, TARGET, revenue=2000.0)
    db_session.add(InventoryItem(name="Milk", unit="L", current_quantity=4, min_threshold=15))
    counter(db_session, TARGET, variance=-100)
    db_session.commit()

    sentences = digest_service.build_digest(db_session, TARGET).sentences

    assert len(sentences) == len(set(sentences))
    assert sum("below your usual" in s for s in sentences) == 1
    assert sum("reorder" in s for s in sentences) == 1
