"""Dish price history: a row only when numbers change, one per trigger, append-only, owner-only."""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.pool import StaticPool

from app.db.session import ensure_price_history_guard
from app.models.costing_models import DishPriceHistory
from app.models.inventory_models import InventoryItem
from app.utils import price_history

API = "/api/v1"
ZERO = {"mode": "amount", "value": "0"}


@pytest.fixture
def butter(test_db):
    # No purchases: its typed price is the price, so typed-price triggers show.
    item = InventoryItem(name="Butter", unit="kg", cost_per_unit=Decimal("580"))
    test_db.add(item)
    test_db.commit()
    return item


@pytest.fixture
def dish(client, owner_headers, butter, sample_menu_items):
    """Costed dish: 100 g butter + ₹10 packaging for 1 portion = ₹68."""
    menu = sample_menu_items[0]
    r = client.post(f"{API}/costing", headers=owner_headers, json={
        "menu_item_id": menu.id, "yield_units": "1",
        "ingredients": [{"inventory_item_id": butter.id, "quantity": "100", "unit": "g"}],
        "packaging": {"mode": "amount", "value": "10"}, "labour": ZERO, "fixed": ZERO, "wastage": ZERO,
    })
    assert r.status_code == 201, r.text
    return menu, r.json()


def _history(client, headers, menu):
    r = client.get(f"{API}/costing/menu/{menu.id}/history", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["entries"]


def _body(menu, butter, qty="100", note=None, packaging="10"):
    body = {
        "menu_item_id": menu.id, "yield_units": "1",
        "ingredients": [{"inventory_item_id": butter.id, "quantity": qty, "unit": "g"}],
        "packaging": {"mode": "amount", "value": packaging}, "labour": ZERO, "fixed": ZERO, "wastage": ZERO,
    }
    if note:
        body["history_note"] = note
    return body


def test_recipe_create_then_save(client, owner_headers, dish, butter):
    menu, costing = dish
    first = _history(client, owner_headers, menu)
    assert [e["cause"] for e in first] == ["recipe"]
    assert Decimal(first[0]["cost_per_unit"]) == Decimal("68")
    assert first[0]["recipe"][0]["name"] == "Butter"

    r = client.patch(f"{API}/costing/{costing['id']}", headers=owner_headers, json=_body(menu, butter, "120", "more butter"))
    assert r.status_code == 200, r.text
    top = _history(client, owner_headers, menu)[0]
    assert (top["cause"], top["note"], top["actor"]) == ("recipe", "more butter", top["actor"])
    assert top["actor"]
    assert top["moves"] == ["Butter 100 g → 120 g"]
    assert Decimal(top["prev_cost_per_unit"]) == Decimal("68")


def test_unchanged_save_writes_nothing_but_a_note_forces_a_row(client, owner_headers, dish, butter):
    menu, costing = dish
    client.patch(f"{API}/costing/{costing['id']}", headers=owner_headers, json=_body(menu, butter))
    assert len(_history(client, owner_headers, menu)) == 1
    client.patch(f"{API}/costing/{costing['id']}", headers=owner_headers, json=_body(menu, butter, note="checked"))
    rows = _history(client, owner_headers, menu)
    assert len(rows) == 2 and rows[0]["note"] == "checked" and rows[0]["moves"] == []


def test_menu_price_edit(client, owner_headers, dish):
    menu, _ = dish
    r = client.patch(f"{API}/menu/{menu.id}", headers=owner_headers, json={"price": 30000})
    assert r.status_code == 200, r.text
    top = _history(client, owner_headers, menu)[0]
    assert top["cause"] == "menu_price" and top["moves"][0].startswith("Menu price")
    assert Decimal(top["menu_price"]) == Decimal("300")


def test_menu_edit_without_price_writes_nothing(client, owner_headers, dish):
    menu, _ = dish
    client.patch(f"{API}/menu/{menu.id}", headers=owner_headers, json={"description": "tasty"})
    assert len(_history(client, owner_headers, menu)) == 1


def test_apply_suggested_price(client, owner_headers, dish):
    menu, costing = dish
    suggested = client.get(f"{API}/costing/{costing['id']}", headers=owner_headers).json()["breakdown"]["suggested_price"]
    r = client.post(f"{API}/costing/{costing['id']}/apply-price", headers=owner_headers,
                    json={"price": suggested, "history_note": "raised after the dairy hike"})
    assert r.status_code == 200, r.text
    top = _history(client, owner_headers, menu)[0]
    assert top["cause"] == "menu_price" and top["note"] == "raised after the dairy hike"


def test_typed_price_changes(client, owner_headers, dish, butter):
    menu, _ = dish
    r = client.post(f"{API}/costing/reprice", headers=owner_headers,
                    json={"prices": [{"inventory_item_id": butter.id, "new_cost_per_unit": "620"}]})
    assert r.status_code == 200, r.text
    top = _history(client, owner_headers, menu)[0]
    assert top["cause"] == "typed_price"
    assert any(m.startswith("Butter ₹580.00 → ₹620.00/kg") for m in top["moves"])
    assert (Decimal(top["prev_cost_per_unit"]), Decimal(top["cost_per_unit"])) == (Decimal("68"), Decimal("72"))

    client.post(f"{API}/inventory/items/{butter.id}/pack-price", headers=owner_headers,
                json={"price": "70", "pack_quantity": "100", "pack_unit": "g"})
    assert _history(client, owner_headers, menu)[0]["cause"] == "typed_price"
    assert len(_history(client, owner_headers, menu)) == 3

    client.patch(f"{API}/inventory/items/{butter.id}", headers=owner_headers, json={"cost_per_unit": "800"})
    assert len(_history(client, owner_headers, menu)) == 4

    client.patch(f"{API}/inventory/items", headers=owner_headers, json={"items": [{"id": butter.id, "cost_per_unit": "900"}]})
    assert len(_history(client, owner_headers, menu)) == 5


def test_owner_purchase_and_approval(client, owner_headers, auth_headers, dish, butter):
    menu, _ = dish
    buy = lambda headers, total: client.post(f"{API}/inventory/transactions/purchase", headers=headers, json={
        "items": [{"item_id": butter.id, "quantity": "2", "total_amount": total}]})

    # Staff at a new price: waits for approval, nothing moves.
    r = buy(auth_headers, "1400")  # ₹700/kg
    assert r.status_code == 201
    assert len(_history(client, owner_headers, menu)) == 1
    pid = r.json()["transactions"][0]["id"]

    assert client.post(f"{API}/inventory/purchases/{pid}/price-review", headers=owner_headers, json={"action": "approve"}).status_code == 200
    top = _history(client, owner_headers, menu)[0]
    assert top["cause"] == "purchase" and "Butter" in top["detail"] and "approved" in top["detail"]
    assert Decimal(top["cost_per_unit"]) == Decimal("80")

    # An owner's own purchase is approved at once.
    buy(owner_headers, "1000")  # ₹500/kg
    top = _history(client, owner_headers, menu)[0]
    assert top["cause"] == "purchase" and Decimal(top["cost_per_unit"]) == Decimal("60")


def test_approve_all(client, owner_headers, auth_headers, dish, butter):
    menu, _ = dish
    r = client.post(f"{API}/inventory/transactions/purchase", headers=auth_headers, json={
        "items": [{"item_id": butter.id, "quantity": "2", "total_amount": "1400"}]})
    pid = r.json()["transactions"][0]["id"]
    client.post(f"{API}/inventory/purchases/price-review/approve-all", headers=owner_headers, json={"purchase_ids": [pid]})
    assert _history(client, owner_headers, menu)[0]["cause"] == "purchase"


def test_default_charges_change(client, owner_headers, dish):
    menu, _ = dish
    # The recipe overrides packaging only if sent; send labour unset to inherit.
    r = client.put(f"{API}/settings", headers=owner_headers, json={"settings": {"costing.labour.value": "20"}})
    assert r.status_code == 200, r.text
    # The dish sets all four charges itself, so nothing moved: no row.
    assert len(_history(client, owner_headers, menu)) == 1


def test_default_charges_reach_a_dish_that_inherits(client, owner_headers, butter, sample_menu_items):
    menu = sample_menu_items[1]
    client.post(f"{API}/costing", headers=owner_headers, json={
        "menu_item_id": menu.id, "yield_units": "1",
        "ingredients": [{"inventory_item_id": butter.id, "quantity": "100", "unit": "g"}]})
    client.put(f"{API}/settings", headers=owner_headers, json={"settings": {"costing.labour.value": "20"}})
    top = _history(client, owner_headers, menu)[0]
    assert top["cause"] == "default_charges" and top["moves"] == ["Labour 15% → 20%"]


def test_made_item_change_reaches_the_dish(client, owner_headers, test_db, sample_menu_items):
    spice = InventoryItem(name="Paprika", unit="g", cost_per_unit=Decimal("1"))
    masala = InventoryItem(name="Masala", unit="g")
    test_db.add_all([spice, masala])
    test_db.commit()
    client.post(f"{API}/costing", headers=owner_headers, json={
        "inventory_item_id": masala.id, "ingredients": [{"inventory_item_id": spice.id, "quantity": "100", "unit": "g"}]})
    menu = sample_menu_items[0]
    client.post(f"{API}/costing", headers=owner_headers, json={
        "menu_item_id": menu.id, "yield_units": "1", "packaging": ZERO, "labour": ZERO, "fixed": ZERO, "wastage": ZERO,
        "ingredients": [{"inventory_item_id": masala.id, "quantity": "10", "unit": "g"}]})

    client.post(f"{API}/costing/reprice", headers=owner_headers,
                json={"prices": [{"inventory_item_id": spice.id, "new_cost_per_unit": "2"}]})
    dish_top = _history(client, owner_headers, menu)[0]
    assert dish_top["cause"] == "typed_price" and any(m.startswith("Masala") for m in dish_top["moves"])
    made = client.get(f"{API}/costing/item/{masala.id}/history", headers=owner_headers).json()["entries"]
    assert len(made) == 2 and made[0]["moves"] == ["Paprika ₹1.00 → ₹2.00/g"]


def test_history_survives_deleting_the_recipe(client, owner_headers, dish):
    menu, costing = dish
    client.delete(f"{API}/costing/{costing['id']}", headers=owner_headers)
    assert len(_history(client, owner_headers, menu)) == 1


def test_staff_cannot_read(client, auth_headers, dish):
    menu, _ = dish
    assert client.get(f"{API}/costing/menu/{menu.id}/history", headers=auth_headers).status_code == 403


def test_baseline_gives_old_recipes_a_first_row_once(client, owner_headers, test_db, dish):
    menu, _ = dish
    test_db.query(DishPriceHistory).delete()
    test_db.commit()
    assert price_history.record(test_db, "baseline", None) == 1
    assert price_history.record(test_db, "baseline", None) == 0
    assert _history(client, owner_headers, menu)[0]["cause"] == "baseline"


def test_table_refuses_update_and_delete():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    DishPriceHistory.__table__.create(engine)
    assert ensure_price_history_guard(engine) and ensure_price_history_guard(engine)
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO dish_price_history (name, cause, cost_per_unit, raw_cost, yield_units, is_complete, data, fingerprint) "
            "VALUES ('x', 'baseline', 1, 1, 1, 1, '{}', '{}')"))
    for sql in ("UPDATE dish_price_history SET name = 'y'", "DELETE FROM dish_price_history"):
        with pytest.raises(DatabaseError, match="append-only"):
            with engine.begin() as conn:
                conn.execute(text(sql))
