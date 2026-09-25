"""
Setup grid's one Save: PATCH /inventory/items applies every changed row in one
commit, retires by deactivating, and records stock changes as adjustments.
"""

from decimal import Decimal

import pytest

from app.models.inventory_models import InventoryCategory, InventoryItem, InventoryTransaction

URL = "/api/v1/inventory/items"


@pytest.fixture
def items(test_db):
    sauces = InventoryCategory(name="Sauces")
    test_db.add(sauces)
    test_db.flush()
    rows = {
        "oil": InventoryItem(name="Chilli oil", unit="bottle", current_quantity=Decimal("3"),
                             cost_per_unit=Decimal("0"), category_id=sauces.id),
        "syrup": InventoryItem(name="Choc syrup", unit="pcs", current_quantity=Decimal("2")),
        "dupe": InventoryItem(name="CHOC SYRUP", unit="pcs", current_quantity=Decimal("0")),
    }
    test_db.add_all(rows.values())
    test_db.commit()
    return {**rows, "sauces": sauces}


def test_save_applies_fields_retires_and_logs_stock(client, owner_headers, items, test_db):
    response = client.patch(URL, headers=owner_headers, json={"items": [
        {"id": items["syrup"].id, "unit": "bottle", "pack_size": 700, "pack_unit": "ml",
         "min_threshold": 1, "cost_per_unit": 250, "current_quantity": 1.5},
        {"id": items["dupe"].id, "is_active": False},
    ]})

    assert response.status_code == 200, response.json()
    assert response.json() == {"updated": 2, "adjusted": 1}
    test_db.expire_all()
    syrup = test_db.get(InventoryItem, items["syrup"].id)
    assert (syrup.unit, syrup.pack_size, syrup.pack_unit, syrup.cost_per_unit, syrup.current_quantity) == (
        "bottle", Decimal("700"), "ml", Decimal("250"), Decimal("1.5"))
    # Retire is a soft delete: the row stays so its transactions stay valid.
    assert test_db.get(InventoryItem, items["dupe"].id).is_active is False
    log = test_db.query(InventoryTransaction).one()
    assert (log.item_id, log.transaction_type, log.quantity, log.previous_quantity, log.new_quantity) == (
        syrup.id, "ADJUSTMENT", Decimal("-0.5"), Decimal("2"), Decimal("1.5"))


def test_presence_item_drops_price_and_clamps_stock(client, owner_headers, items, test_db):
    response = client.patch(URL, headers=owner_headers, json={"items": [
        {"id": items["oil"].id, "count_mode": "presence"},
    ]})

    assert response.status_code == 200, response.json()
    test_db.expire_all()
    oil = test_db.get(InventoryItem, items["oil"].id)
    assert (oil.count_mode, oil.unit, oil.min_threshold, oil.cost_per_unit, oil.current_quantity) == (
        "presence", "yes/no", Decimal("1"), None, Decimal("1"))
    assert test_db.query(InventoryTransaction).one().quantity == Decimal("-2")


@pytest.mark.parametrize("bad_row", [
    {"id": 9999, "unit": "kg"},       # unknown item
    {"unit": None},                   # required column blanked
    {"category_id": 9999},            # unknown category
])
def test_one_bad_row_saves_nothing(client, owner_headers, items, test_db, bad_row):
    bad_row = {"id": items["dupe"].id, **bad_row}
    response = client.patch(URL, headers=owner_headers, json={"items": [
        {"id": items["syrup"].id, "unit": "kg"},
        bad_row,
    ]})

    assert response.status_code in (400, 404, 422)
    test_db.expire_all()
    assert test_db.get(InventoryItem, items["syrup"].id).unit == "pcs"


def test_staff_cannot_bulk_edit(client, auth_headers, items):
    response = client.patch(URL, headers=auth_headers, json={"items": [{"id": items["oil"].id, "unit": "kg"}]})
    assert response.status_code == 403
