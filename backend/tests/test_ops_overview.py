"""The price ripple through kitchen-made items, and the recipes overview."""

from datetime import timedelta
from decimal import Decimal

from app.core.business_day import utcnow
from app.models import models
from app.models.inventory_models import InventoryItem, InventoryTransaction

API = "/api/v1"
NO_OVERHEADS = {k: {"mode": "amount", "value": "0"} for k in ("packaging", "labour", "fixed", "wastage")}


def _d(value):
    return Decimal(str(value))


def _item(test_db, name, unit="kg", price=None):
    item = InventoryItem(name=name, unit=unit, cost_per_unit=price)
    test_db.add(item)
    test_db.commit()
    return item


def _menu(test_db, categories, name, price=10000, available=True):
    m = models.MenuItem(name=name, price=price, category_id=categories[0].id, is_available=available)
    test_db.add(m)
    test_db.commit()
    return m


def _lines(*triples):
    return [{"inventory_item_id": i.id, "quantity": str(q), "unit": u} for i, q, u in triples]


def _recipe(client, headers, subject, lines, **extra):
    key = "menu_item_id" if isinstance(subject, models.MenuItem) else "inventory_item_id"
    body = {key: subject.id, "yield_units": "1", "ingredients": _lines(*lines), **extra}
    r = client.post(f"{API}/costing", headers=headers, json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _overview(client, headers):
    r = client.get(f"{API}/costing/overview", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_ripple_passes_through_made_item(client, test_db, owner_headers, auth_headers, sample_categories):
    onion = _item(test_db, "Onion", "kg", Decimal("32"))
    bao = _item(test_db, "Bao buns", "pcs")
    _recipe(client, owner_headers, bao, [(onion, 1, "kg")], yield_units="10")
    for n in "ABC":
        _recipe(client, owner_headers, _menu(test_db, sample_categories, f"Bao {n}"), [(bao, 2, "pcs")])
    _recipe(client, owner_headers, _menu(test_db, sample_categories, "Onion rings"), [(onion, 200, "g")])
    _recipe(client, owner_headers, _menu(test_db, sample_categories, "Plain tea"), [(_item(test_db, "Tea", "g", Decimal("1")), 5, "g")])

    # Staff log 4 kg for 160: Rs 40/kg against Rs 32, so it waits for the owner.
    r = client.post(f"{API}/inventory/transactions/purchase", headers=auth_headers, json={
        "items": [{"item_id": onion.id, "quantity": "4", "total_amount": "160"}]})
    assert r.status_code == 201, r.text
    (pending,) = client.get(f"{API}/inventory/purchases/pending-prices", headers=owner_headers).json()

    ripple = pending["ripple"]
    assert len(ripple["affected_dishes"]) == 4
    assert ripple["unaffected_count"] == 1
    vias = {d["menu_item_name"]: d["via"] for d in ripple["affected_dishes"]}
    assert vias == {"Bao A": ["Bao buns"], "Bao B": ["Bao buns"], "Bao C": ["Bao buns"], "Onion rings": []}
    (made,) = ripple["made_items"]
    assert made["name"] == "Bao buns" and made["unit"] == "pcs"
    assert _d(made["cost_after"]) > _d(made["cost_before"])
    assert _d(made["cost_after"]) == _d("4.00") and _d(made["cost_before"]) == _d("3.20")


def test_overview_statuses_and_order(client, test_db, owner_headers, sample_categories):
    flour = _item(test_db, "Flour", "kg", Decimal("100"))
    unpriced = _item(test_db, "Saffron", "g")
    bao = _item(test_db, "Bao buns", "pcs")
    _recipe(client, owner_headers, bao, [(flour, 1, "kg")], yield_units="10")
    cheap = _menu(test_db, sample_categories, "Cheap bowl", price=12000)   # cost 100 against 120: below target
    _recipe(client, owner_headers, cheap, [(flour, 1, "kg")], **NO_OVERHEADS)
    fine = _menu(test_db, sample_categories, "Fine bowl", price=100000)    # cost 100 against 1000: on target
    _recipe(client, owner_headers, fine, [(flour, 1, "kg")], **NO_OVERHEADS)
    gap = _menu(test_db, sample_categories, "Gap bowl")
    _recipe(client, owner_headers, gap, [(unpriced, 1, "g")])
    _menu(test_db, sample_categories, "Bare bowl")
    _menu(test_db, sample_categories, "Off menu", available=False)

    body = _overview(client, owner_headers)
    assert [(r["name"], r["status"]) for r in body["rows"]] == [
        ("Cheap bowl", "below_target"), ("Gap bowl", "missing_prices"), ("Bare bowl", "no_recipe"),
        ("Bao buns", "costed"), ("Fine bowl", "on_target"),
    ]
    rows = {r["name"]: r for r in body["rows"]}
    assert rows["Bao buns"]["kind"] == "made" and rows["Bao buns"]["unit"] == "pcs"
    assert _d(rows["Bao buns"]["cost_per_unit"]) == _d("10.00")
    assert rows["Bao buns"]["category"] is None and rows["Fine bowl"]["category"] == "South Indian"
    assert rows["Gap bowl"]["missing_count"] == 1 and rows["Gap bowl"]["margin_percent"] is None
    assert rows["Bare bowl"]["costing_id"] is None and rows["Bare bowl"]["menu_item_id"] is not None
    totals = body["totals"]
    assert (totals["below_target"], totals["missing_prices"], totals["no_recipe"]) == (1, 1, 1)
    assert _d(totals["average_margin"]) == _d("53.34")  # (16.67 + 90.00) / 2


def test_overview_average_margin_null_without_dishes(client, owner_headers):
    assert _overview(client, owner_headers)["totals"]["average_margin"] is None


def test_overview_last_week(client, test_db, owner_headers, sample_categories):
    onion = _item(test_db, "Onion", "kg")
    dish = _menu(test_db, sample_categories, "Onion bowl")
    _recipe(client, owner_headers, dish, [(onion, 1, "kg")], **NO_OVERHEADS)
    for total in ("32", "40"):
        r = client.post(f"{API}/inventory/transactions/purchase", headers=owner_headers, json={
            "items": [{"item_id": onion.id, "quantity": "1", "total_amount": total}]})
        assert r.status_code == 201, r.text
    old = test_db.query(InventoryTransaction).filter_by(item_id=onion.id).order_by(InventoryTransaction.id).first()
    old.price_reviewed_at = utcnow() - timedelta(days=8)
    test_db.commit()

    (row,) = _overview(client, owner_headers)["rows"]
    assert _d(row["cost_per_unit"]) == 40 and _d(row["cost_last_week"]) == 32


def test_overview_survives_retired_made_item_and_deleted_menu_item(client, test_db, owner_headers, sample_categories):
    flour = _item(test_db, "Flour", "kg", Decimal("100"))
    bao = _item(test_db, "Bao buns", "pcs")
    _recipe(client, owner_headers, bao, [(flour, 1, "kg")], yield_units="10")
    dish = _menu(test_db, sample_categories, "Bao plate")
    _recipe(client, owner_headers, dish, [(bao, 2, "pcs")])
    gone = _menu(test_db, sample_categories, "Gone plate")
    _recipe(client, owner_headers, gone, [(flour, 1, "kg")])

    bao.is_active = False
    test_db.delete(gone)
    test_db.commit()

    body = _overview(client, owner_headers)
    assert [r["name"] for r in body["rows"]] == ["Bao plate"]


def test_last_week_prices_made_item_after_purchase_priced_line(client, test_db, owner_headers, sample_categories):
    onion = _item(test_db, "Onion", "kg")
    flour = _item(test_db, "Flour", "kg")
    bao = _item(test_db, "Bao buns", "pcs")
    _recipe(client, owner_headers, bao, [(flour, 1, "kg")], yield_units="1")
    dish = _menu(test_db, sample_categories, "Onion bao")
    _recipe(client, owner_headers, dish, [(onion, 1, "kg"), (bao, 1, "pcs")], **NO_OVERHEADS)
    for item, totals in ((onion, ("10", "10")), (flour, ("20", "50"))):
        for total in totals:
            r = client.post(f"{API}/inventory/transactions/purchase", headers=owner_headers, json={
                "items": [{"item_id": item.id, "quantity": "1", "total_amount": total}]})
            assert r.status_code == 201, r.text
    for item in (onion, flour):
        first = test_db.query(InventoryTransaction).filter_by(item_id=item.id).order_by(InventoryTransaction.id).first()
        first.price_reviewed_at = utcnow() - timedelta(days=8)
    test_db.commit()

    row = next(r for r in _overview(client, owner_headers)["rows"] if r["name"] == "Onion bao")
    assert _d(row["cost_per_unit"]) == 60 and _d(row["cost_last_week"]) == 30


def test_incomplete_row_shows_partial_cost_and_margin_ceiling(client, test_db, owner_headers, sample_categories):
    flour = _item(test_db, "Flour", "kg", Decimal("100"))
    saffron = _item(test_db, "Saffron", "g")
    dish = _menu(test_db, sample_categories, "Saffron bowl", price=20000)
    _recipe(client, owner_headers, dish, [(flour, 1, "kg"), (saffron, 1, "g")], **NO_OVERHEADS)

    (row,) = _overview(client, owner_headers)["rows"]
    assert row["status"] == "missing_prices" and row["margin_percent"] is None
    assert _d(row["cost_per_unit"]) == 100 and _d(row["margin_ceiling"]) == 50
