"""
The daily purchase sheet: POST /inventory/transactions/purchase records what was
paid per line, and an item's price comes from its latest paid purchase, falling
back to the typed cost_per_unit.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect, text

from app.db.session import ensure_inventory_columns
from app.models.inventory_models import InventoryItem, InventoryTransaction, Vendor
from app.utils import pricing

PURCHASE = "/api/v1/inventory/transactions/purchase"
ITEMS = "/api/v1/inventory/items"


@pytest.fixture
def chicken(test_db):
    item = InventoryItem(name="Chicken boneless", unit="kg", current_quantity=Decimal("2"),
                         cost_per_unit=Decimal("300"))
    test_db.add(item)
    test_db.commit()
    return item


def _purchase(test_db, item, quantity, total, when, notes=None):
    t = InventoryTransaction(
        item_id=item.id, transaction_type="PURCHASE", quantity=Decimal(quantity),
        total_amount=None if total is None else Decimal(total), notes=notes, recorded_by="test",
        previous_quantity=Decimal(0), new_quantity=Decimal(quantity), created_at=when,
    )
    test_db.add(t)
    test_db.commit()
    return t


# --- unit price derivation ---------------------------------------------------

def test_unit_price_is_total_over_quantity():
    assert pricing.unit_price(Decimal("480"), Decimal("4")) == Decimal("120")
    assert pricing.unit_price(Decimal("100"), Decimal("3")) == Decimal("33.3333")


def test_unit_price_of_a_gift_is_zero_and_of_no_total_is_unknown():
    assert pricing.unit_price(Decimal("0"), Decimal("1")) == Decimal("0")
    assert pricing.unit_price(None, Decimal("1")) is None
    # A yes/no item bought while in stock records a 0 movement: nothing to divide.
    assert pricing.unit_price(Decimal("50"), Decimal("0")) is None


def test_a_gift_never_becomes_the_price(test_db, chicken):
    _purchase(test_db, chicken, "4", "1280", datetime(2026, 8, 12, 5))
    _purchase(test_db, chicken, "1", "0", datetime(2026, 8, 13, 5), notes="free from vendor")

    price = pricing.resolve_one(test_db, chicken)

    assert (price.price, price.source, price.as_of) == (Decimal("320"), "purchase", datetime(2026, 8, 12, 5))


# --- resolution ----------------------------------------------------------------

def test_latest_purchase_wins_over_earlier_ones_and_the_typed_price(test_db, chicken):
    _purchase(test_db, chicken, "4", "1280", datetime(2026, 8, 12, 5))   # 320/kg
    _purchase(test_db, chicken, "5", "1750", datetime(2026, 9, 1, 5))    # 350/kg
    _purchase(test_db, chicken, "2", None, datetime(2026, 9, 2, 5))      # no amount: skipped

    price = pricing.resolve_one(test_db, chicken)

    assert (price.price, price.source, price.as_of) == (Decimal("350"), "purchase", datetime(2026, 9, 1, 5))


def test_same_item_twice_on_one_sheet_the_later_line_wins(test_db, chicken):
    same_second = datetime(2026, 9, 1, 5)
    _purchase(test_db, chicken, "4", "1280", same_second)
    _purchase(test_db, chicken, "1", "340", same_second)

    assert pricing.resolve_one(test_db, chicken).price == Decimal("340")


def test_falls_back_to_the_typed_price_with_no_purchase_history(test_db, chicken):
    price = pricing.resolve_one(test_db, chicken)

    assert (price.price, price.source, price.as_of) == (Decimal("300"), "typed", None)


@pytest.mark.parametrize("typed", [Decimal("0"), Decimal("0.00"), None])
def test_a_stored_zero_is_missing_not_free(test_db, typed):
    item = InventoryItem(name="Salt", unit="kg", cost_per_unit=typed)
    test_db.add(item)
    test_db.commit()

    assert pricing.resolve_one(test_db, item) == pricing.NO_PRICE


def test_yes_no_items_have_no_price(test_db):
    item = InventoryItem(name="Chilli oil", unit="yes/no", count_mode="presence", current_quantity=Decimal("0"))
    test_db.add(item)
    test_db.commit()
    _purchase(test_db, item, "1", "90", datetime(2026, 9, 1, 5))

    assert pricing.resolve_one(test_db, item) == pricing.NO_PRICE


def test_price_jump_threshold():
    assert pricing.is_price_jump(Decimal("320"), Decimal("520"))
    assert pricing.is_price_jump(Decimal("320"), Decimal("200"))
    assert not pricing.is_price_jump(Decimal("320"), Decimal("400"))
    assert not pricing.is_price_jump(None, Decimal("400"))


# --- the endpoint ----------------------------------------------------------------

def test_purchase_records_total_vendor_and_raises_stock(client, auth_headers, test_db, chicken):
    vendor = Vendor(name="Raju Chicken Centre")
    test_db.add(vendor)
    test_db.commit()

    response = client.post(PURCHASE, headers=auth_headers, json={
        "vendor_id": vendor.id,
        "items": [{"item_id": chicken.id, "quantity": 4, "total_amount": 1280}],
    })

    assert response.status_code == 201, response.json()
    body = response.json()
    line = body["transactions"][0]
    assert Decimal(str(body["total_amount"])) == Decimal("1280")
    assert Decimal(str(line["unit_price"])) == Decimal("320")
    assert line["vendor_name"] == "Raju Chicken Centre"
    test_db.expire_all()
    assert test_db.get(InventoryItem, chicken.id).current_quantity == Decimal("6")
    t = test_db.query(InventoryTransaction).one()
    assert (t.total_amount, t.vendor_id) == (Decimal("1280"), vendor.id)

    item = client.get(f"{ITEMS}/{chicken.id}", headers=auth_headers).json()
    assert Decimal(str(item["current_price"])) == Decimal("320")
    assert item["price_source"] == "purchase"
    assert item["price_as_of"] is not None


def test_purchase_without_amount_or_vendor_still_works(client, auth_headers, test_db, chicken):
    response = client.post(PURCHASE, headers=auth_headers, json={
        "items": [{"item_id": chicken.id, "quantity": 1}],
    })

    assert response.status_code == 201, response.json()
    item = client.get(f"{ITEMS}/{chicken.id}", headers=auth_headers).json()
    assert item["price_source"] == "typed"


def test_a_zero_total_needs_a_note(client, auth_headers, chicken):
    bare = client.post(PURCHASE, headers=auth_headers, json={
        "items": [{"item_id": chicken.id, "quantity": 1, "total_amount": 0}],
    })
    noted = client.post(PURCHASE, headers=auth_headers, json={
        "items": [{"item_id": chicken.id, "quantity": 1, "total_amount": 0, "notes": "thrown in"}],
    })

    assert bare.status_code == 422
    assert noted.status_code == 201, noted.json()
    assert noted.json()["transactions"][0]["price_check"]["is_jump"] is False


def test_unknown_vendor_is_rejected(client, auth_headers, chicken):
    response = client.post(PURCHASE, headers=auth_headers, json={
        "items": [{"item_id": chicken.id, "quantity": 1, "total_amount": 300, "vendor_id": 999}],
    })

    assert response.status_code == 400


def test_check_flags_a_jump_before_saving(client, auth_headers, test_db, chicken):
    _purchase(test_db, chicken, "4", "1280", datetime(2026, 8, 12, 5))

    response = client.post(f"{PURCHASE}/check", headers=auth_headers, json={
        "items": [{"item_id": chicken.id, "quantity": 2, "total_amount": 1040}],
    })

    assert response.status_code == 200, response.json()
    check = response.json()[0]
    assert Decimal(str(check["unit_price"])) == Decimal("520")
    assert Decimal(str(check["previous_price"])) == Decimal("320")
    assert check["previous_source"] == "purchase"
    assert check["is_jump"] is True
    assert test_db.query(InventoryTransaction).count() == 1  # a dry run writes nothing


def test_day_sheet_lists_the_days_purchases_with_a_total(client, auth_headers, test_db, chicken):
    # 2026-09-20 in IST (UTC+5:30) runs from 18:30 UTC on the 19th.
    _purchase(test_db, chicken, "4", "1280", datetime(2026, 9, 19, 20))
    _purchase(test_db, chicken, "1", None, datetime(2026, 9, 20, 5))
    _purchase(test_db, chicken, "1", "999", datetime(2026, 9, 19, 5))  # the day before

    body = client.get("/api/v1/inventory/purchases", headers=auth_headers,
                      params={"business_date": "2026-09-20"}).json()

    assert len(body["purchases"]) == 2
    assert Decimal(str(body["total_amount"])) == Decimal("1280")
    assert body["unpriced"] == 1


# --- migration -------------------------------------------------------------------

def test_startup_adds_the_money_columns_to_an_old_database():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE vendors (id INTEGER PRIMARY KEY, name VARCHAR(100))"))
        conn.execute(text(
            "CREATE TABLE inventory_transactions (id INTEGER PRIMARY KEY, item_id INTEGER, quantity NUMERIC)"))

    added = ensure_inventory_columns(engine)
    again = ensure_inventory_columns(engine)

    assert {"total_amount", "vendor_id"} <= set(added)
    assert again == []
    columns = {c["name"] for c in inspect(engine).get_columns("inventory_transactions")}
    assert {"total_amount", "vendor_id"} <= columns
