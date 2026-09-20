"""The Ask service with the model replaced by canned decisions.

Covers what the code is responsible for: defaults, period resolution, dish
matching, the report actually running, and the state handed to the next turn.
"""

from datetime import UTC, date, datetime

import pytest

from app.ask.periods import IST
from app.ask.reports import REPORTS, Comparison
from app.ask.router import RouterDecision
from app.ask.service import ask
from app.models.models import (
    Category,
    MenuItem,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentMethod,
)

TODAY = date(2026, 9, 20)


class FakeRouter:
    def __init__(self, decision: RouterDecision):
        self.decision = decision
        self.calls = []

    def decide(self, question, previous, today, previous_question=None):
        self.calls.append((question, previous, today, previous_question))
        return self.decision


def decision(**overrides) -> RouterDecision:
    base = {
        "action": "report", "report": "sales_summary", "period": None, "dish": None,
        "comparison": None, "limit": None, "message": None,
    }
    return RouterDecision(**{**base, **overrides})


def _ist(day: date, hour: int) -> datetime:
    """A naive-UTC timestamp for the given IST calendar day and hour, as stored."""
    return _to_naive_utc(datetime(day.year, day.month, day.day, hour, tzinfo=IST))


def _to_naive_utc(aware: datetime) -> datetime:

    return aware.astimezone(UTC).replace(tzinfo=None)


@pytest.fixture
def seeded(db_session):
    beverages = Category(name="Beverages")
    db_session.add(beverages)
    db_session.flush()

    masala = MenuItem(name="Masala Chai", price=3000, category_id=beverages.id, is_beverage=True)
    ginger = MenuItem(name="Ginger Chai", price=3500, category_id=beverages.id, is_beverage=True)
    coffee = MenuItem(name="Filter Coffee", price=4000, category_id=beverages.id, is_beverage=True)
    db_session.add_all([masala, ginger, coffee])
    db_session.flush()

    # Three paid orders on three IST days: 18 Sep ₹300, 19 Sep ₹900 (best), 20 Sep ₹600.
    sales = [
        (date(2026, 9, 18), masala, 10, 30000),
        (date(2026, 9, 19), coffee, 20, 90000),
        (date(2026, 9, 20), masala, 20, 60000),
    ]
    for n, (day, item, qty, total) in enumerate(sales, start=1):
        order = Order(
            order_number=f"A-{n}", table_number=n, subtotal=total, gst_amount=0,
            total_amount=total, status=OrderStatus.PAID, created_at=_ist(day, 11),
        )
        db_session.add(order)
        db_session.flush()
        db_session.add(OrderItem(
            order_id=order.id, menu_item_id=item.id, menu_item_name=item.name,
            quantity=qty, unit_price=item.price, subtotal=total, is_beverage=True,
        ))
        db_session.add(Payment(order_id=order.id, payment_method=PaymentMethod.UPI, amount=total))
    db_session.commit()
    return db_session


# ============================================================================
# Reports run, with the period the owner will see
# ============================================================================


def test_sales_defaults_to_today_and_labels_it(seeded):
    router = FakeRouter(decision(report="sales_summary"))

    result = ask(seeded, "how are sales", router, today=TODAY)

    assert result.kind == "report"
    assert result.period_label == "Today, Sun 20 Sep"
    assert result.data["total_revenue_rupees"] == 600.0
    assert result.data["total_orders"] == 1


def test_named_period_is_resolved_in_code(seeded):
    router = FakeRouter(decision(
        report="sales_summary", period={"kind": "named", "name": "last_7_days"},
    ))

    result = ask(seeded, "sales this week", router, today=TODAY)

    assert result.period_label == "Last 7 days, 14–20 Sep 2026"
    assert result.data["total_revenue_rupees"] == 1800.0
    assert result.data["total_orders"] == 3


def test_best_days_picks_the_right_day(seeded):
    router = FakeRouter(decision(
        report="best_days", period={"kind": "since", "start": "2026-09-01"},
    ))

    result = ask(seeded, "best day since 1 sep", router, today=TODAY)

    assert result.data["best_day"] == {"date": "2026-09-19", "revenue_rupees": 900.0, "orders": 1}
    assert result.data["worst_day"]["date"] == "2026-09-18"
    assert result.data["trading_days"] == 3
    assert result.data["average_daily_revenue_rupees"] == 600.0


def test_period_summary_composes_the_other_reports(seeded):
    router = FakeRouter(decision(
        report="period_summary", period={"kind": "month", "year": 2026, "month": 9},
    ))

    result = ask(seeded, "everything about september", router, today=TODAY)

    assert result.period_label == "September so far, 1–20 Sep 2026"
    assert set(result.data) == {"sales", "orders", "top_items", "categories", "payments", "peak_hours", "best_days"}
    assert result.data["sales"]["total_revenue_rupees"] == 1800.0
    assert result.data["top_items"]["top_products"][0]["name"] == "Masala Chai"


def test_every_report_in_the_catalogue_runs(seeded):
    for report_id, report in REPORTS.items():
        extra = {}
        if report.needs_dish:
            extra["dish"] = "masala chai"
        if report.needs_comparison:
            extra["comparison"] = Comparison.THIS_WEEK_VS_LAST_WEEK
        router = FakeRouter(decision(report=report_id, **extra))

        result = ask(seeded, report_id, router, today=TODAY)

        assert result.kind == "report", f"{report_id}: {result.message}"
        assert result.data is not None


# ============================================================================
# Dishes are resolved in code, never trusted from the model
# ============================================================================


def test_dish_is_matched_to_the_exact_menu_name(seeded):
    router = FakeRouter(decision(report="dish_details", dish="filter coffee"))

    result = ask(seeded, "how did filter coffee do", router, today=TODAY)

    assert result.kind == "report"
    assert result.dish == "Filter Coffee"
    assert result.data["item_name"] == "Filter Coffee"
    assert result.decision.dish == "Filter Coffee"


def test_ambiguous_dish_asks_instead_of_guessing(seeded):
    router = FakeRouter(decision(report="dish_details", dish="chai"))

    result = ask(seeded, "how did chai do", router, today=TODAY)

    assert result.kind == "clarify"
    assert "chai" in result.message
    assert set(result.candidates) == {"Masala Chai", "Ginger Chai"}


def test_unknown_dish_is_reported_not_invented(seeded):
    router = FakeRouter(decision(report="dish_details", dish="biryani"))

    result = ask(seeded, "how did biryani do", router, today=TODAY)

    assert result.kind == "clarify"
    assert "biryani" in result.message
    assert result.candidates == []


def test_dish_report_without_a_dish_asks(seeded):
    router = FakeRouter(decision(report="dish_details", dish=None))
    assert ask(seeded, "dish", router, today=TODAY).kind == "clarify"


# ============================================================================
# Model decisions the code refuses or bounds
# ============================================================================


def test_future_month_becomes_a_clarification(seeded):
    router = FakeRouter(decision(
        report="sales_summary", period={"kind": "month", "year": 2026, "month": 12},
    ))

    result = ask(seeded, "december sales", router, today=TODAY)

    assert result.kind == "clarify"
    assert "December 2026" in result.message


def test_cash_counter_refuses_a_range(seeded):
    router = FakeRouter(decision(
        report="cash_counter", period={"kind": "named", "name": "last_week"},
    ))

    result = ask(seeded, "cash counter last week", router, today=TODAY)

    assert result.kind == "clarify"
    assert "one day at a time" in result.message


def test_compare_without_a_comparison_asks(seeded):
    router = FakeRouter(decision(report="compare_periods", comparison=None))
    result = ask(seeded, "compare", router, today=TODAY)
    assert result.kind == "clarify"
    assert "this week with last week" in result.message


def test_limit_is_clamped(seeded):
    router = FakeRouter(decision(report="top_items", limit=500))
    result = ask(seeded, "top 500", router, today=TODAY)
    assert result.kind == "report"


def test_unsupported_and_clarify_pass_the_models_message_through(seeded):
    unsupported = FakeRouter(decision(action="unsupported", report=None, message="No weather data."))
    assert ask(seeded, "rainy days", unsupported, today=TODAY).message == "No weather data."

    clarify = FakeRouter(decision(action="clarify", report=None, message="Sales or orders?"))
    assert ask(seeded, "numbers", clarify, today=TODAY).message == "Sales or orders?"


# ============================================================================
# Follow-ups
# ============================================================================


def test_previous_decision_and_question_reach_the_model(seeded):
    previous = decision(report="dish_details", dish="Masala Chai")
    router = FakeRouter(decision(
        report="dish_details", dish="Masala Chai", period={"kind": "named", "name": "last_month"},
    ))

    ask(seeded, "and last month?", router, previous=previous,
        previous_question="how did masala chai do", today=TODAY)

    question, prev, today, prev_q = router.calls[0]
    assert prev == previous
    assert prev_q == "how did masala chai do"
    assert today == TODAY


# ============================================================================
# Endpoint
# ============================================================================


def test_endpoint_is_owner_only_and_returns_a_report(client, test_db, auth_headers, owner_headers):
    from app.api.v1.endpoints.ask import get_router
    from app.main import app

    app.dependency_overrides[get_router] = lambda: FakeRouter(decision(report="inventory_status"))
    try:
        as_admin = client.post("/api/v1/ask", json={"question": "stock"}, headers=auth_headers)
        assert as_admin.status_code == 403

        as_owner = client.post("/api/v1/ask", json={"question": "stock"}, headers=owner_headers)
        assert as_owner.status_code == 200, as_owner.text
        body = as_owner.json()
        assert body["kind"] == "report"
        assert body["report_id"] == "inventory_status"
        assert body["decision"]["report"] == "inventory_status"
    finally:
        app.dependency_overrides.pop(get_router, None)


def test_endpoint_reports_missing_configuration(client, owner_headers, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    response = client.post("/api/v1/ask", json={"question": "sales"}, headers=owner_headers)
    assert response.status_code == 503


# ============================================================================
# The schema sent to OpenAI must satisfy strict mode
# ============================================================================


def test_router_schema_is_strict_mode_safe():
    """OpenAI strict mode rejects `oneOf`; a discriminated union emits it."""
    from openai.lib._parsing._completions import type_to_response_format_param

    param = type_to_response_format_param(RouterDecision)
    assert param["json_schema"]["strict"] is True

    def walk(node):
        if isinstance(node, dict):
            assert "oneOf" not in node, node
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(param["json_schema"]["schema"])


def test_period_kinds_still_parse_without_a_discriminator():
    for raw in (
        {"kind": "named", "name": "last_week"},
        {"kind": "month", "year": 2026, "month": 8},
        {"kind": "since", "start": "2026-08-01"},
        {"kind": "range", "start": "2026-09-01", "end": "2026-09-10"},
        {"kind": "day", "date": "2026-09-18"},
    ):
        parsed = decision(period=raw).period
        assert parsed.kind == raw["kind"]
