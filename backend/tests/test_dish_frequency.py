"""Tests for the /analytics/dish-frequency endpoint (Tools page)."""

from datetime import datetime, timedelta, timezone

import pytest

from app.main import app
from app.api.deps import get_current_user
from app.models import models


@pytest.fixture
def auth_override():
    """Authenticate as an admin (non-owner) — the Tools report is open to
    both owner and admin roles."""
    app.dependency_overrides[get_current_user] = lambda: type(
        "TD", (), {"username": "admin", "role": "admin"}
    )()
    yield
    app.dependency_overrides.pop(get_current_user, None)


def _make_order(db, order_number, items, created_at, status=models.OrderStatus.PAID):
    """items: list of (menu_item, quantity)."""
    order = models.Order(
        order_number=order_number,
        table_number=1,
        subtotal=0,
        gst_amount=0,
        total_amount=0,
        status=status,
        created_at=created_at,
    )
    db.add(order)
    db.flush()
    for menu_item, qty in items:
        db.add(
            models.OrderItem(
                order_id=order.id,
                menu_item_id=menu_item.id,
                menu_item_name=menu_item.name,
                quantity=qty,
                unit_price=menu_item.price,
                subtotal=menu_item.price * qty,
            )
        )
    db.commit()
    return order


def test_dish_frequency_sorted_desc(client, test_db, sample_menu_items, auth_override):
    dosa, coffee, samosa = sample_menu_items
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Coffee: 5 units across 2 orders; Dosa: 3 units across 1 order
    _make_order(test_db, "O-1", [(dosa, 3), (coffee, 2)], now - timedelta(hours=1))
    _make_order(test_db, "O-2", [(coffee, 3)], now - timedelta(hours=2))
    # Canceled order should be excluded by default
    _make_order(test_db, "O-3", [(dosa, 10)], now - timedelta(hours=1),
                status=models.OrderStatus.CANCELED)

    resp = client.get("/api/v1/analytics/dish-frequency")
    assert resp.status_code == 200, resp.text
    rows = resp.json()["rows"]

    # Descending by quantity: coffee (5) before dosa (3); samosa absent (no orders)
    assert [r["name"] for r in rows] == ["Filter Coffee", "Masala Dosa"]
    assert rows[0]["quantity"] == 5
    assert rows[0]["times_ordered"] == 2
    assert rows[1]["quantity"] == 3
    assert rows[1]["times_ordered"] == 1


def test_dish_frequency_filter_includes_zero(client, test_db, sample_menu_items, auth_override):
    dosa, coffee, samosa = sample_menu_items
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    _make_order(test_db, "O-1", [(dosa, 2)], now - timedelta(hours=1))

    # Filter to dosa + samosa; samosa never ordered -> appears with 0
    resp = client.get(
        "/api/v1/analytics/dish-frequency",
        params={"menu_item_ids": [dosa.id, samosa.id]},
    )
    assert resp.status_code == 200, resp.text
    rows = {r["name"]: r["quantity"] for r in resp.json()["rows"]}
    assert rows == {"Masala Dosa": 2, "Samosa": 0}


def test_dish_frequency_paid_only(client, test_db, sample_menu_items, auth_override):
    dosa, coffee, samosa = sample_menu_items
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    _make_order(test_db, "O-1", [(dosa, 2)], now - timedelta(hours=1),
                status=models.OrderStatus.PAID)
    _make_order(test_db, "O-2", [(dosa, 5)], now - timedelta(hours=1),
                status=models.OrderStatus.ACTIVE)

    # Default (exclude canceled) counts both active + paid = 7
    resp = client.get("/api/v1/analytics/dish-frequency")
    assert resp.json()["rows"][0]["quantity"] == 7

    # paid_only counts only the paid order = 2
    resp = client.get("/api/v1/analytics/dish-frequency", params={"paid_only": True})
    assert resp.json()["rows"][0]["quantity"] == 2
