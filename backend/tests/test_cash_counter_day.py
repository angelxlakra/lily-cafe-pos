"""Tests for the /cash-counter/day/{day} endpoint (hidden day-lookup page)."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app import schemas
from app.main import app
from app.api.deps import get_current_user
from app.models import models
from app.models.cash_models import DailyCashCounter


@pytest.fixture
def auth_override():
    """
    Sign in as the owner.

    These tests look up fixed past dates to exercise the response shape and
    the prev/next day links; only the owner may read previous days (the admin
    case is covered in tests/test_cash_inventory_access.py).
    """
    app.dependency_overrides[get_current_user] = lambda: schemas.TokenData(
        username="owner", role=schemas.UserRole.OWNER
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


def _counter(db, day, opening_500s=0, closing_500s=None):
    c = DailyCashCounter(
        date=day,
        opening_balance=Decimal(opening_500s * 500),
        opening_500s=opening_500s,
        closing_500s=closing_500s,
        closing_balance=Decimal(closing_500s * 500) if closing_500s is not None else None,
        opened_by="admin",
    )
    db.add(c)
    db.commit()
    return c


def test_day_with_counter_and_neighbours(client, test_db, auth_override):
    _counter(test_db, date(2026, 9, 1), opening_500s=1)
    _counter(test_db, date(2026, 9, 5), opening_500s=2, closing_500s=4)
    _counter(test_db, date(2026, 9, 9), opening_500s=3)

    order = models.Order(order_number="O-1", table_number=1, subtotal=0,
                         gst_amount=0, total_amount=0, status=models.OrderStatus.PAID)
    test_db.add(order)
    test_db.flush()
    for amt in (50000, 25050):
        test_db.add(models.Payment(order_id=order.id, payment_method=models.PaymentMethod.CASH,
                                   amount=amt, created_at=datetime(2026, 9, 5, 10, 0)))
    test_db.add(models.Payment(order_id=order.id, payment_method=models.PaymentMethod.UPI,
                               amount=99900, created_at=datetime(2026, 9, 5, 11, 0)))
    test_db.commit()

    res = client.get("/api/v1/cash-counter/day/2026-09-05")
    assert res.status_code == 200
    body = res.json()
    assert body["counter"]["opening_500s"] == 2
    assert body["counter"]["status"] == "closed_pending_verification"
    assert Decimal(str(body["cash_payments_total"])) == Decimal("750.50")
    assert body["cash_payments_count"] == 2
    assert body["prev_date"] == "2026-09-01"
    assert body["next_date"] == "2026-09-09"


def test_day_without_counter(client, test_db, auth_override):
    _counter(test_db, date(2026, 9, 1))
    res = client.get("/api/v1/cash-counter/day/2026-09-03")
    assert res.status_code == 200
    body = res.json()
    assert body["counter"] is None
    assert body["cash_payments_count"] == 0
    assert body["prev_date"] == "2026-09-01"
    assert body["next_date"] is None


def test_day_requires_auth(client, test_db):
    res = client.get("/api/v1/cash-counter/day/2026-09-03")
    assert res.status_code in (401, 403)
