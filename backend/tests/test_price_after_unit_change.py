"""
A purchase is read in its item's unit as it is now. Before this, a line
recorded as "4000 g for ₹480" became a price of ₹0.12/kg the moment the
owner switched the item to kg, and stayed wrong until the next purchase.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine, inspect, text

from app.db.session import ensure_inventory_columns
from app.models.inventory_models import InventoryItem, InventoryTransaction
from app.utils import pricing

ITEMS = "/api/v1/inventory/items"
PURCHASE = "/api/v1/inventory/transactions/purchase"


def _onions(test_db, unit="g", price=None):
    item = InventoryItem(name="Onion", unit=unit, current_quantity=Decimal("0"), min_threshold=Decimal("0"),
                         cost_per_unit=None if price is None else Decimal(price))
    test_db.add(item)
    test_db.commit()
    return item


def _buy(client, headers, item, quantity, total):
    r = client.post(PURCHASE, headers=headers, json={"items": [{"item_id": item.id, "quantity": quantity, "total_amount": total}]})
    assert r.status_code == 201, r.text
    return r.json()["transactions"][0]["id"]


def test_every_movement_records_its_unit(client, auth_headers, test_db):
    onion = _onions(test_db)
    line = _buy(client, auth_headers, onion, 4000, 480)

    assert test_db.get(InventoryTransaction, line).unit == "g"


def test_the_price_survives_a_g_to_kg_change(client, auth_headers, owner_headers, test_db):
    onion = _onions(test_db)
    _buy(client, auth_headers, onion, 4000, 480)
    assert pricing.resolve_one(test_db, onion).price == Decimal("0.12")  # ₹0.12 a gram

    r = client.patch(ITEMS, headers=owner_headers, json={"items": [{"id": onion.id, "unit": "kg"}]})
    assert r.status_code == 200, r.text
    test_db.refresh(onion)

    price = pricing.resolve_one(test_db, onion)
    assert (price.price, price.source) == (Decimal("120.0000"), "purchase")
    listed = client.get(ITEMS, headers=owner_headers).json()["items"][0]
    assert Decimal(str(listed["current_price"])) == Decimal("120")


def test_a_purchase_in_a_unit_that_no_longer_converts_is_passed_over(client, auth_headers, owner_headers, test_db):
    """Bought by the piece, now counted in kg: the old line says nothing about a kg, so the typed price stands."""
    lemons = _onions(test_db, unit="pcs", price="80")
    _buy(client, auth_headers, lemons, 20, 100)

    client.patch(ITEMS, headers=owner_headers, json={"items": [{"id": lemons.id, "unit": "kg"}]})
    test_db.refresh(lemons)

    price = pricing.resolve_one(test_db, lemons)
    assert (price.price, price.source) == (Decimal("80"), "typed")


def test_the_days_sheet_shows_old_lines_in_the_new_unit(client, auth_headers, owner_headers, test_db):
    onion = _onions(test_db)
    _buy(client, auth_headers, onion, 4000, 480)
    client.patch(ITEMS, headers=owner_headers, json={"items": [{"id": onion.id, "unit": "kg"}]})

    (line,) = client.get("/api/v1/inventory/purchases", headers=auth_headers).json()["purchases"]

    assert (Decimal(str(line["quantity"])), line["unit"], Decimal(str(line["unit_price"]))) == (Decimal("4"), "kg", Decimal("120"))


def test_editing_an_old_line_after_the_change_moves_stock_in_the_new_unit(client, auth_headers, owner_headers, test_db):
    """Bought 4000 g, now in kg (4 kg in stock): correcting it to 5 kg leaves 5 kg, not 4 - 4000 + 5."""
    onion = _onions(test_db)
    line = _buy(client, auth_headers, onion, 4000, 480)
    client.patch(ITEMS, headers=owner_headers, json={"items": [{"id": onion.id, "unit": "kg"}]})

    r = client.patch(f"/api/v1/inventory/purchases/{line}", headers=auth_headers, json={"quantity": 5})

    assert r.status_code == 200, r.text
    test_db.refresh(onion)
    assert onion.current_quantity == Decimal("5")
    t = test_db.get(InventoryTransaction, line)
    assert (t.quantity, t.unit) == (Decimal("5"), "kg")


def test_startup_backfills_the_unit_on_old_rows():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE vendors (id INTEGER PRIMARY KEY, name VARCHAR(100))"))
        conn.execute(text("CREATE TABLE inventory_items (id INTEGER PRIMARY KEY, unit VARCHAR(20))"))
        conn.execute(text(
            "CREATE TABLE inventory_transactions (id INTEGER PRIMARY KEY, item_id INTEGER, quantity NUMERIC)"))
        conn.execute(text("INSERT INTO inventory_items (id, unit) VALUES (1, 'kg')"))
        conn.execute(text("INSERT INTO inventory_transactions (id, item_id, quantity) VALUES (1, 1, 4)"))

    ensure_inventory_columns(engine)
    ensure_inventory_columns(engine)  # idempotent

    assert "unit" in {c["name"] for c in inspect(engine).get_columns("inventory_transactions")}
    with engine.connect() as conn:
        assert conn.execute(text("SELECT unit FROM inventory_transactions")).scalar() == "kg"


def test_a_line_whose_unit_changed_kind_cant_be_edited_or_deleted(client, auth_headers, owner_headers, test_db):
    """20 pcs can't be restated in kg, so neither change can move stock correctly: both are refused."""
    lemons = _onions(test_db, unit="pcs")
    line = _buy(client, auth_headers, lemons, 20, 100)
    client.patch(ITEMS, headers=owner_headers, json={"items": [{"id": lemons.id, "unit": "kg"}]})

    edit = client.patch(f"/api/v1/inventory/purchases/{line}", headers=auth_headers, json={"quantity": 2})
    delete = client.delete(f"/api/v1/inventory/purchases/{line}", headers=auth_headers)

    assert (edit.status_code, delete.status_code) == (409, 409)
    assert "tonight's count" in edit.json()["detail"]


def test_deleting_an_old_line_after_the_change_takes_out_the_same_amount(client, auth_headers, owner_headers, test_db):
    """4000 g bought, now 4 kg in stock: deleting the line leaves 0 kg, not 4 - 4000."""
    onion = _onions(test_db)
    line = _buy(client, auth_headers, onion, 4000, 480)
    client.patch(ITEMS, headers=owner_headers, json={"items": [{"id": onion.id, "unit": "kg"}]})

    r = client.delete(f"/api/v1/inventory/purchases/{line}", headers=auth_headers)

    assert r.status_code == 204, r.text
    test_db.refresh(onion)
    assert onion.current_quantity == Decimal("0")


def test_a_stock_change_saved_with_a_unit_change_records_the_new_unit(client, owner_headers, test_db):
    """One grid save switches g to kg and sets stock: the adjustment it logs is in kg."""
    onion = _onions(test_db)

    r = client.patch(ITEMS, headers=owner_headers, json={"items": [{"id": onion.id, "unit": "kg", "current_quantity": 3}]})

    assert r.status_code == 200, r.text
    (adjustment,) = test_db.query(InventoryTransaction).filter_by(item_id=onion.id).all()
    assert (adjustment.quantity, adjustment.unit) == (Decimal("3"), "kg")
