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


def test_day_sheet_lists_the_days_purchases_with_a_total(client, owner_headers, test_db, chicken):
    # The sheet's day is the count night: 04:00 IST on the 20th (22:30 UTC on
    # the 19th) to 04:00 IST on the 21st, so 01:30 IST on the 21st still counts.
    _purchase(test_db, chicken, "4", "1280", datetime(2026, 9, 20, 5))
    _purchase(test_db, chicken, "1", None, datetime(2026, 9, 20, 20))
    _purchase(test_db, chicken, "1", "999", datetime(2026, 9, 19, 20))  # 01:30 IST on the 20th: the night before

    body = client.get("/api/v1/inventory/purchases", headers=owner_headers,
                      params={"business_date": "2026-09-20"}).json()

    assert len(body["purchases"]) == 2
    assert Decimal(str(body["total_amount"])) == Decimal("1280")
    assert body["unpriced"] == 1


# --- correcting today's sheet ------------------------------------------------------

def _log(client, auth_headers, item, quantity, total):
    body = client.post(PURCHASE, headers=auth_headers, json={
        "items": [{"item_id": item.id, "quantity": quantity, "total_amount": total}],
    }).json()
    return body["transactions"][0]["id"]


def test_a_line_can_be_corrected_the_same_day(client, auth_headers, test_db, chicken):
    purchase_id = _log(client, auth_headers, chicken, 4, 1280)  # stock 2 -> 6

    fixed = client.patch(f"/api/v1/inventory/purchases/{purchase_id}", headers=auth_headers,
                         json={"quantity": 3, "total_amount": 960})

    assert fixed.status_code == 200, fixed.json()
    test_db.expire_all()
    assert test_db.get(InventoryItem, chicken.id).current_quantity == Decimal("5")
    t = test_db.get(InventoryTransaction, purchase_id)
    assert (t.quantity, t.new_quantity, t.total_amount) == (Decimal("3"), Decimal("5"), Decimal("960"))

    gone = client.delete(f"/api/v1/inventory/purchases/{purchase_id}", headers=auth_headers)
    assert gone.status_code == 204
    test_db.expire_all()
    assert test_db.get(InventoryItem, chicken.id).current_quantity == Decimal("2")
    assert test_db.query(InventoryTransaction).count() == 0


def test_once_counted_a_line_is_an_adjustment_not_an_edit(client, auth_headers, test_db, chicken):
    purchase_id = _log(client, auth_headers, chicken, 4, 1280)
    counted = client.post("/api/v1/inventory/counts", headers=auth_headers,
                          json={"lines": [{"item_id": chicken.id, "counted_quantity": 6}]})
    assert counted.status_code == 201, counted.json()

    response = client.patch(f"/api/v1/inventory/purchases/{purchase_id}", headers=auth_headers,
                            json={"quantity": 3})

    assert response.status_code == 409


def test_an_old_line_cannot_be_edited(client, auth_headers, test_db, chicken):
    old = _purchase(test_db, chicken, "4", "1280", datetime(2026, 8, 12, 5))

    assert client.delete(f"/api/v1/inventory/purchases/{old.id}", headers=auth_headers).status_code == 409


# --- the picker ----------------------------------------------------------------------

def test_staff_can_add_an_item_inline_flagged_for_setup(client, auth_headers, owner_headers, test_db):
    made = client.post(f"{ITEMS}/quick", headers=auth_headers, json={"name": "Kaffir lime leaves", "unit": "pack"})
    again = client.post(f"{ITEMS}/quick", headers=auth_headers, json={"name": "kaffir LIME leaves ", "unit": "g"})

    assert made.status_code == 201, made.json()
    assert made.json()["needs_setup"] is True
    assert again.json()["id"] == made.json()["id"]  # no duplicate

    client.patch(ITEMS, headers=owner_headers, json={"items": [{"id": made.json()["id"], "min_threshold": 1}]})
    assert client.get(f"{ITEMS}/{made.json()['id']}", headers=auth_headers).json()["needs_setup"] is False


def test_frequent_items_rank_purchases_above_count_corrections(client, auth_headers, test_db, chicken):
    onion = InventoryItem(name="Onion", unit="kg", current_quantity=Decimal("0"))
    test_db.add(onion)
    test_db.commit()
    for _ in range(2):  # two upward count corrections
        test_db.add(InventoryTransaction(item_id=onion.id, transaction_type="ADJUSTMENT", quantity=Decimal(1),
                                         recorded_by="t", previous_quantity=Decimal(0), new_quantity=Decimal(1)))
    test_db.commit()
    _log(client, auth_headers, chicken, 1, 320)  # one purchase outweighs them

    ranked = client.get("/api/v1/inventory/purchases/frequent", headers=auth_headers).json()

    assert ranked == [chicken.id, onion.id]


# --- the owners' table: used, remaining, day-end, wastage ------------------------

@pytest.fixture
def sugar_sold_today(test_db):
    """Sugar in kg; a coffee uses 50 g; 10 coffees sold today, 5 more on a canceled order."""
    from app.models import models
    from app.models.costing_models import DishCosting, DishCostingIngredient
    from app.core import business_day

    sugar = InventoryItem(name="Sugar", unit="kg", current_quantity=Decimal("0"))
    category = models.Category(name="Beverages")
    test_db.add_all([sugar, category])
    test_db.commit()
    coffee = models.MenuItem(name="Coffee", price=4000, category_id=category.id, is_available=True)
    test_db.add(coffee)
    test_db.commit()
    costing = DishCosting(menu_item_id=coffee.id, yield_units=1)
    costing.ingredients.append(DishCostingIngredient(inventory_item_id=sugar.id, quantity=Decimal("50"), unit="g"))
    test_db.add(costing)
    for n, (status, cups) in enumerate([(models.OrderStatus.PAID, 10), (models.OrderStatus.CANCELED, 5)]):
        order = models.Order(order_number=f"ORD-T-{n}", table_number=1, subtotal=0, gst_amount=0,
                             total_amount=0, status=status, created_at=business_day.utcnow())
        test_db.add(order)
        test_db.commit()
        test_db.add(models.OrderItem(order_id=order.id, menu_item_id=coffee.id, menu_item_name="Coffee",
                                     quantity=cups, unit_price=4000, subtotal=4000 * cups))
    test_db.commit()
    return sugar


def test_the_sketch_bought_used_counted_wastage(client, auth_headers, test_db, sugar_sold_today):
    sugar = sugar_sold_today
    # Staff: 2 × 1 kg at ₹65.
    saved = client.post(PURCHASE, headers=auth_headers, json={
        "items": [{"item_id": sugar.id, "quantity": 2, "total_amount": 130, "pack_count": 2}],
    })
    assert saved.status_code == 201, saved.json()
    # Staff, at close: 1.4 kg actually left. This is tonight's count.
    counted = client.put(f"/api/v1/inventory/counts/tonight/items/{sugar.id}", headers=auth_headers,
                         json={"counted_quantity": 1.4})
    assert counted.status_code == 204, counted.json()

    sheet = client.get("/api/v1/inventory/purchases", headers=auth_headers).json()

    line = sheet["purchases"][0]
    assert Decimal(str(line["pack_count"])) == 2
    row = sheet["items"][str(sugar.id)]
    as_dec = {k: None if v is None else Decimal(str(v)) for k, v in row.items()}
    assert as_dec["opening"] == 0
    assert as_dec["bought"] == 2
    assert as_dec["used"] == Decimal("0.5")        # 10 coffees × 50 g; the canceled order doesn't count
    assert as_dec["remaining"] == Decimal("1.5")
    assert as_dec["day_end"] == Decimal("1.4")
    assert as_dec["wastage"] == Decimal("0.1")
    assert sheet["editable"] is True

    test_db.expire_all()
    assert test_db.get(InventoryItem, sugar.id).current_quantity == Decimal("1.4")
    count = client.get("/api/v1/inventory/counts/today", headers=auth_headers).json()
    assert (count["items_total"], count["items_changed"]) == (1, 1)


def test_day_end_retyped_updates_the_same_count_line(client, auth_headers, test_db, chicken):
    for value in (5, 4):
        client.put(f"/api/v1/inventory/counts/tonight/items/{chicken.id}", headers=auth_headers,
                   json={"counted_quantity": value})
    count = client.get("/api/v1/inventory/counts/today", headers=auth_headers).json()
    assert count["items_total"] == 1
    test_db.expire_all()
    assert test_db.get(InventoryItem, chicken.id).current_quantity == Decimal("4")


def test_an_item_no_recipe_uses_is_unknown_not_zero(client, auth_headers, chicken):
    client.post(PURCHASE, headers=auth_headers, json={
        "items": [{"item_id": chicken.id, "quantity": 1, "total_amount": 320}],
    })
    row = client.get("/api/v1/inventory/purchases", headers=auth_headers).json()["items"][str(chicken.id)]
    assert row["used"] is None and row["remaining"] is None and row["wastage"] is None
    assert Decimal(str(row["opening"])) == 2


def test_only_the_owner_opens_other_days(client, auth_headers, owner_headers):
    params = {"business_date": "2026-01-05"}
    assert client.get("/api/v1/inventory/purchases", headers=auth_headers, params=params).status_code == 403
    past = client.get("/api/v1/inventory/purchases", headers=owner_headers, params=params)
    assert past.status_code == 200
    assert past.json()["editable"] is False


def test_used_counts_the_count_night_not_the_calendar_day(test_db, sugar_sold_today):
    """A coffee sold at 01:30 after close belongs to the night before, like the count does."""
    from datetime import date

    from app.models import models
    from app.utils.usage import used_on

    coffee = test_db.query(models.MenuItem).filter_by(name="Coffee").one()
    test_db.query(models.OrderItem).delete()
    test_db.query(models.Order).delete()
    # Night of 20 Sep (IST) runs 04:00 on the 20th to 04:00 on the 21st: 22:30 to 22:30 UTC.
    for n, (utc, cups) in enumerate([
        (datetime(2026, 9, 19, 22, 0), 1),   # 03:30 IST on the 20th: the night before
        (datetime(2026, 9, 20, 6, 0), 4),    # 11:30 IST on the 20th
        (datetime(2026, 9, 20, 20, 0), 6),   # 01:30 IST on the 21st, after close
        (datetime(2026, 9, 20, 23, 0), 2),   # 04:30 IST on the 21st: the next night
    ]):
        order = models.Order(order_number=f"ORD-N-{n}", table_number=1, subtotal=0, gst_amount=0,
                             total_amount=0, status=models.OrderStatus.PAID, created_at=utc)
        test_db.add(order)
        test_db.commit()
        test_db.add(models.OrderItem(order_id=order.id, menu_item_id=coffee.id, menu_item_name="Coffee",
                                     quantity=cups, unit_price=4000, subtotal=4000 * cups))
    test_db.commit()

    assert used_on(test_db, date(2026, 9, 20), [sugar_sold_today])[sugar_sold_today.id] == Decimal("0.5")


def test_recipe_in_ml_bridges_to_bottles_by_pack_size():
    from app.models.costing_models import DishCostingIngredient
    from app.utils.usage import per_portion_in_item_unit

    oil = InventoryItem(name="Chilli oil", unit="bottle", pack_size=Decimal("700"), pack_unit="ml")
    assert per_portion_in_item_unit(DishCostingIngredient(quantity=Decimal("35"), unit="ml"), oil, 1) == Decimal("0.05")
    assert per_portion_in_item_unit(DishCostingIngredient(quantity=Decimal("35"), unit="g"), oil, 1) is None


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
