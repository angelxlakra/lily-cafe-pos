"""
Regression tests for the "business day" convention.

Timestamps are stored in UTC but "today" is the local date in the configured
timezone (Asia/Kolkata by default). Between 00:00 and 05:30 IST the UTC date
is still the previous day, so anything that derives "today" from the UTC
timestamp (or from the server's local clock) disagrees with the order number.
These tests freeze the clock inside that window so the bug cannot regress
regardless of when the suite runs.
"""

from datetime import date, datetime

import pytest

from app import crud
from app.core import access, business_day
from app.models.models import OrderStatus, PaymentMethod
from app.schemas.schemas import OrderCreate, PaymentCreate


# 20:00 UTC on 9 March == 01:30 IST on 10 March.
FROZEN_UTC = datetime(2026, 3, 9, 20, 0, 0)
FROZEN_BUSINESS_DAY = date(2026, 3, 10)


@pytest.fixture
def frozen_after_midnight_ist(monkeypatch):
    """Freeze the shared clock to just after local midnight, before UTC midnight."""
    monkeypatch.setattr(business_day, "utcnow", lambda: FROZEN_UTC)
    return FROZEN_UTC


def _place_order(db, menu_item, table_number):
    order, _ = crud.create_order(
        db,
        OrderCreate(
            table_number=table_number,
            customer_name="Night owl",
            items=[{"menu_item_id": menu_item.id, "quantity": 1}],
        ),
    )
    return order


def test_business_today_is_local_date_not_utc_date(frozen_after_midnight_ist):
    assert FROZEN_UTC.date() == date(2026, 3, 9)  # sanity: UTC still says yesterday
    assert business_day.business_today() == FROZEN_BUSINESS_DAY
    assert access.business_today() == FROZEN_BUSINESS_DAY


def test_business_day_bounds_cover_local_midnight_to_midnight():
    start, end = business_day.business_day_utc_bounds(FROZEN_BUSINESS_DAY)
    assert start == datetime(2026, 3, 9, 18, 30)  # 00:00 IST
    assert end == datetime(2026, 3, 10, 18, 30)   # 24:00 IST
    assert start <= FROZEN_UTC < end


def test_order_created_after_local_midnight_belongs_to_today(
    test_db, sample_menu_item, frozen_after_midnight_ist
):
    order = _place_order(test_db, sample_menu_item, table_number=3)

    # Stamped in UTC, numbered with the local business date.
    assert order.created_at == FROZEN_UTC
    assert order.order_number.startswith("ORD-20260310-")
    assert access.order_business_date(order) == FROZEN_BUSINESS_DAY

    # And every "today" view agrees.
    assert [o.id for o in crud.get_orders(test_db, today_only=True)] == [order.id]
    assert [o.id for o in crud.get_orders(test_db, status=OrderStatus.ACTIVE, today_only=True)] == [order.id]
    assert [o.id for o in crud.get_orders(test_db, table_number=3, today_only=True)] == [order.id]
    assert crud.get_orders(test_db, date_str="2026-03-10") != []
    assert crud.get_orders(test_db, date_str="2026-03-09") == []


def test_order_created_before_local_midnight_is_not_today(
    test_db, sample_menu_item, monkeypatch
):
    # 18:00 UTC == 23:30 IST on 9 March: still yesterday's business day.
    monkeypatch.setattr(business_day, "utcnow", lambda: datetime(2026, 3, 9, 18, 0, 0))
    yesterday_order = _place_order(test_db, sample_menu_item, table_number=1)
    assert yesterday_order.order_number.startswith("ORD-20260309-")

    monkeypatch.setattr(business_day, "utcnow", lambda: FROZEN_UTC)
    today_order = _place_order(test_db, sample_menu_item, table_number=2)
    assert today_order.order_number.startswith("ORD-20260310-0001")

    assert [o.id for o in crud.get_orders(test_db, today_only=True)] == [today_order.id]
    assert [o.id for o in crud.get_orders(test_db, start_date="2026-03-09", end_date="2026-03-09")] == [
        yesterday_order.id
    ]


def test_payment_breakdown_uses_business_day(test_db, sample_menu_item, frozen_after_midnight_ist):
    order = _place_order(test_db, sample_menu_item, table_number=4)
    crud.create_payment(test_db, order.id, PaymentCreate(payment_method="cash", amount=order.total_amount))

    orders, total, _, breakdown = crud.get_orders_paginated(test_db, today_only=True, exclude_active=True)
    assert [o.id for o in orders] == [order.id]
    assert total == 1
    assert breakdown.get(PaymentMethod.CASH.value, breakdown.get("cash")) == order.total_amount


def test_admin_can_reach_post_midnight_order(test_db, sample_menu_item, frozen_after_midnight_ist, client, auth_headers):
    order = _place_order(test_db, sample_menu_item, table_number=6)
    response = client.get(f"/api/v1/orders/{order.id}", headers=auth_headers)
    assert response.status_code == 200, response.text
