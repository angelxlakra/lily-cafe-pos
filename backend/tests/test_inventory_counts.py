"""
Nightly stock count: each active item is recorded as checked, changed or
skipped, stock moves only for changed items, and the owner controls the order.
"""

from decimal import Decimal

import pytest

from app.models.inventory_models import (
    InventoryCategory,
    InventoryCount,
    InventoryItem,
    InventoryTransaction,
)


@pytest.fixture
def stock(test_db):
    dry = InventoryCategory(name="Dry Grocery")
    cold = InventoryCategory(name="Cold Drinks")
    test_db.add_all([dry, cold])
    test_db.flush()
    items = [
        InventoryItem(name="Ramen", unit="pcs", current_quantity=Decimal("46"), category_id=dry.id),
        InventoryItem(name="Eggs", unit="pcs", current_quantity=Decimal("20"), category_id=dry.id),
        InventoryItem(name="Milk", unit="L", current_quantity=Decimal("3"), category_id=cold.id),
        InventoryItem(name="Old", unit="pcs", current_quantity=Decimal("1"), is_active=False),
    ]
    test_db.add_all(items)
    test_db.commit()
    return {"dry": dry, "cold": cold, **{item.name: item for item in items}}


def test_count_records_checked_changed_and_skipped(client, auth_headers, stock, test_db):
    response = client.post(
        "/api/v1/inventory/counts",
        headers=auth_headers,
        json={"lines": [
            {"item_id": stock["Ramen"].id, "counted_quantity": 46},    # matches
            {"item_id": stock["Eggs"].id, "counted_quantity": 12.5},   # changed
            {"item_id": stock["Milk"].id, "counted_quantity": None},   # skipped
            {"item_id": stock["Old"].id, "counted_quantity": 5},       # inactive: ignored
            {"item_id": 9999, "counted_quantity": 5},                  # deleted: ignored
        ]},
    )

    assert response.status_code == 201, response.json()
    body = response.json()
    assert (body["items_total"], body["items_checked"], body["items_changed"], body["items_skipped"]) == (3, 1, 1, 1)
    assert body["counted_by"] == "admin"
    assert body["skipped_item_names"] == ["Milk"]
    assert body["changes"] == [{
        "item_id": stock["Eggs"].id, "item_name": "Eggs",
        "previous_quantity": 20.0, "new_quantity": 12.5, "difference": -7.5,
    }]

    test_db.expire_all()
    assert test_db.get(InventoryItem, stock["Eggs"].id).current_quantity == Decimal("12.5")
    assert test_db.get(InventoryItem, stock["Ramen"].id).current_quantity == Decimal("46")
    assert test_db.get(InventoryItem, stock["Old"].id).current_quantity == Decimal("1")
    # Only the changed item moves stock.
    assert test_db.query(InventoryTransaction).count() == 1
    count = test_db.query(InventoryCount).one()
    assert sorted(line.status for line in count.lines) == ["changed", "checked", "skipped"]


def test_todays_count_reports_latest(client, auth_headers, stock):
    assert client.get("/api/v1/inventory/counts/today", headers=auth_headers).json() is None

    for eggs in (19, 18):
        client.post(
            "/api/v1/inventory/counts",
            headers=auth_headers,
            json={"lines": [{"item_id": stock["Eggs"].id, "counted_quantity": eggs}]},
        )

    today = client.get("/api/v1/inventory/counts/today", headers=auth_headers).json()
    assert today["items_changed"] == 1 and today["items_skipped"] == 2
    assert len(client.get("/api/v1/inventory/counts", headers=auth_headers).json()) == 2


def test_count_rejects_negative_quantities(client, auth_headers, stock):
    response = client.post(
        "/api/v1/inventory/counts",
        headers=auth_headers,
        json={"lines": [{"item_id": stock["Eggs"].id, "counted_quantity": -1}]},
    )
    assert response.status_code == 422


def test_owner_sets_count_order(client, owner_headers, stock):
    cold, dry = stock["cold"].id, stock["dry"].id
    assert client.put(
        "/api/v1/inventory/categories/order", headers=owner_headers, json={"ids": [cold, dry]}
    ).status_code == 204
    assert [c["id"] for c in client.get("/api/v1/inventory/categories", headers=owner_headers).json()] == [cold, dry]

    eggs, ramen = stock["Eggs"].id, stock["Ramen"].id
    client.put("/api/v1/inventory/items/order", headers=owner_headers, json={"ids": [eggs, ramen]})
    listed = client.get("/api/v1/inventory/items", headers=owner_headers).json()["items"]
    assert [i["id"] for i in listed if i["category_id"] == dry] == [eggs, ramen]


def test_new_items_join_the_end_of_an_arranged_order(client, owner_headers, stock):
    dry = stock["dry"].id
    client.put(
        "/api/v1/inventory/items/order",
        headers=owner_headers,
        json={"ids": [stock["Eggs"].id, stock["Ramen"].id]},
    )
    created = client.post(
        "/api/v1/inventory/items",
        headers=owner_headers,
        json={"name": "Salt", "unit": "kg", "category_id": dry},
    ).json()
    listed = client.get("/api/v1/inventory/items", headers=owner_headers).json()["items"]
    assert [i["id"] for i in listed if i["category_id"] == dry][-1] == created["id"]


def test_reordering_is_owner_only(client, auth_headers, stock):
    response = client.put(
        "/api/v1/inventory/categories/order",
        headers=auth_headers,
        json={"ids": [stock["dry"].id]},
    )
    assert response.status_code == 403


def test_reordering_unknown_ids_fails(client, owner_headers, stock):
    response = client.put(
        "/api/v1/inventory/items/order", headers=owner_headers, json={"ids": [9999]}
    )
    assert response.status_code == 404


@pytest.mark.parametrize("utc_now, expected_night", [
    ((2026, 9, 21, 17, 30), "2026-09-21"),  # 23:00 IST: that night
    ((2026, 9, 21, 18, 35), "2026-09-21"),  # 00:05 IST: still last night
    ((2026, 9, 21, 22, 29), "2026-09-21"),  # 03:59 IST: still last night
    ((2026, 9, 21, 22, 31), "2026-09-22"),  # 04:01 IST: a new day
])
def test_counts_after_midnight_belong_to_the_night(client, auth_headers, stock, monkeypatch, utc_now, expected_night):
    from datetime import datetime
    from app.core import business_day

    monkeypatch.setattr(business_day, "utcnow", lambda: datetime(*utc_now))
    saved = client.post(
        "/api/v1/inventory/counts",
        headers=auth_headers,
        json={"lines": [{"item_id": stock["Eggs"].id, "counted_quantity": 20}]},
    ).json()
    assert saved["business_date"] == expected_night
    assert client.get("/api/v1/inventory/counts/today", headers=auth_headers).json()["id"] == saved["id"]
