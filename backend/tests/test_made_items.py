"""Kitchen-made items: their own recipes, costed recursively, and pack-price entry."""

from decimal import Decimal

import pytest
from sqlalchemy import Index, create_engine, text
from sqlalchemy.pool import StaticPool

from app.db.session import ensure_costing_made_items
from app.models.inventory_models import InventoryItem
from app.utils.costing import money

API = "/api/v1"


def _item(test_db, name, unit="pkt"):
    item = InventoryItem(name=name, unit=unit)
    test_db.add(item)
    test_db.commit()
    return item


def _pack_price(client, headers, item, price, qty, unit):
    r = client.post(
        f"{API}/inventory/items/{item.id}/pack-price", headers=headers,
        json={"price": str(price), "pack_quantity": str(qty), "pack_unit": unit},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _priced(client, test_db, headers, rows):
    """Create a pkt item per (name, price, qty, unit) and price it by its pack."""
    items = {}
    for name, price, qty, unit in rows:
        items[name] = _item(test_db, name)
        if price is not None:
            _pack_price(client, headers, items[name], price, qty, unit)
    return items


def _lines(*triples):
    return [{"inventory_item_id": i.id, "quantity": str(q), "unit": u} for i, q, u in triples]


def _cajun(client, test_db, headers):
    spices = _priced(client, test_db, headers, [
        ("Salt", None, 0, ""), ("Oregano", 99, 10, "g"), ("Thyme", 99, 18, "g"),
        ("Kashmiri", 140, 100, "g"), ("Paprika", 99, 52, "g"), ("Garlic", 99, 100, "g"),
        ("Onion powder", 99, 80, "g"), ("Pepper", 195, 100, "g"),
    ])
    made = _item(test_db, "Cajun masala", "g")
    qty = [200, 20, 40, 80, 266, 206, 100, 100]
    r = client.post(f"{API}/costing", headers=headers, json={
        "inventory_item_id": made.id,
        "ingredients": _lines(*[(s, q, "g") for s, q in zip(spices.values(), qty)]),
    })
    return spices, made, r


def test_cookie_costs_from_whatsapp_sample(client, test_db, owner_headers, sample_menu_items):
    it = _priced(client, test_db, owner_headers, [
        ("Butter", 58, 100, "g"), ("Powder sugar", 75, 1000, "g"), ("Brown sugar", 180, 1000, "g"),
        ("Fresh cream", 60, 250, "g"), ("Vanilla", 439, 500, "ml"), ("Maida", 35, 500, "g"),
        ("Baking powder", 38, 100, "g"), ("Choco chunks", 220, 400, "g"),
    ])
    menu = sample_menu_items[0]
    menu.price = 13000
    test_db.commit()
    qty = [(100, "g"), (25, "g"), (25, "g"), (50, "g"), (5, "ml"), (190, "g"), (3, "g"), (100, "g")]
    r = client.post(f"{API}/costing", headers=owner_headers, json={
        "menu_item_id": menu.id, "yield_units": "4",
        "ingredients": _lines(*[(i, q, u) for i, (q, u) in zip(it.values(), qty)]),
    })
    assert r.status_code == 201, r.text
    b = r.json()["breakdown"]
    assert Decimal(b["raw_material_cost"]) == Decimal("150.21")
    assert Decimal(b["raw_cost_per_unit"]) == Decimal("37.55")
    assert Decimal(b["cost_per_unit"]) == Decimal("48.82")
    assert 62 <= Decimal(b["margin_percent"]) < 63


def test_cajun_masala_made_item(client, test_db, owner_headers):
    _, made, r = _cajun(client, test_db, owner_headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["kind"] == "made" and body["name"] == "Cajun masala" and body["unit"] == "g"
    assert Decimal(body["yield_units"]) == 1012
    assert Decimal(body["breakdown"]["raw_material_cost"]) == Decimal("1559.11")
    assert body["breakdown"]["is_complete"] is False
    got = client.get(f"{API}/costing/item/{made.id}", headers=owner_headers)
    assert got.status_code == 200 and got.json()["id"] == body["id"]
    assert client.get(f"{API}/costing/item/999999", headers=owner_headers).status_code == 404
    # The item list says which items are made here (admin can't call costing).
    flags = {i["name"]: i["has_recipe"] for i in client.get(f"{API}/inventory/items", headers=owner_headers).json()["items"]}
    assert flags["Cajun masala"] is True and flags["Pepper"] is False


def test_dish_uses_made_item(client, test_db, owner_headers, sample_menu_items):
    spices, made, r = _cajun(client, test_db, owner_headers)
    assert r.status_code == 201, r.text
    dish = lambda: client.post(f"{API}/costing/preview", headers=owner_headers, json={
        "menu_item_id": sample_menu_items[0].id, "yield_units": "1",
        "ingredients": _lines((made, 10, "g")),
    })
    (line,) = dish().json()["ingredients"]
    assert line["price_source"] == "recipe" and line["price_missing"] is True

    _pack_price(client, owner_headers, spices["Salt"], 28, 1000, "g")
    (line,) = dish().json()["ingredients"]
    assert line["price_missing"] is False
    assert Decimal(line["line_cost"]) == money(Decimal("1564.71") / 1012 * 10)

    # The made item's page names the recipes that use it.
    saved = client.post(f"{API}/costing", headers=owner_headers, json={
        "menu_item_id": sample_menu_items[0].id, "yield_units": "1",
        "ingredients": _lines((made, 10, "g")),
    })
    assert saved.status_code == 201, saved.text
    used = client.get(f"{API}/costing/item/{made.id}", headers=owner_headers).json()["used_in"]
    assert used == [{"costing_id": saved.json()["id"], "name": "Masala Dosa", "kind": "dish"}]


def test_cycle_refused(client, test_db, owner_headers):
    a, b = _item(test_db, "Cajun masala", "g"), _item(test_db, "Spice mix", "g")
    pepper = _priced(client, test_db, owner_headers, [("Pepper", 195, 100, "g")])["Pepper"]
    r = client.post(f"{API}/costing", headers=owner_headers, json={
        "inventory_item_id": a.id, "yield_units": "100",
        "ingredients": _lines((b, 50, "g"), (pepper, 50, "g")),
    })
    assert r.status_code == 201, r.text
    r = client.post(f"{API}/costing", headers=owner_headers, json={
        "inventory_item_id": b.id, "yield_units": "100", "ingredients": _lines((a, 10, "g")),
    })
    assert r.status_code == 400
    assert r.json()["detail"] == "A recipe can't use itself: Spice mix → Cajun masala → Spice mix"

    # The same loop made by editing a saved recipe.
    r = client.post(f"{API}/costing", headers=owner_headers, json={
        "inventory_item_id": b.id, "yield_units": "100", "ingredients": _lines((pepper, 10, "g")),
    })
    assert r.status_code == 201, r.text
    r = client.patch(f"{API}/costing/{r.json()['id']}", headers=owner_headers, json={
        "inventory_item_id": b.id, "yield_units": "100", "ingredients": _lines((a, 10, "g")),
    })
    assert r.status_code == 400
    assert r.json()["detail"] == "A recipe can't use itself: Spice mix → Cajun masala → Spice mix"


def test_made_recipe_needs_yield_when_units_differ(client, test_db, owner_headers):
    flour = _item(test_db, "Maida")
    made = _item(test_db, "Dough ball", "pcs")
    r = client.post(f"{API}/costing", headers=owner_headers, json={
        "inventory_item_id": made.id, "ingredients": _lines((flour, 100, "g")),
    })
    assert r.status_code == 400
    assert r.json()["detail"].startswith("Type how much one batch makes (Maida is in g")


def test_one_id_required(client, test_db, owner_headers, sample_menu_items):
    made = _item(test_db, "Dough ball", "pcs")
    for body in ({}, {"menu_item_id": sample_menu_items[0].id, "inventory_item_id": made.id, "yield_units": "1"}):
        assert client.post(f"{API}/costing", headers=owner_headers, json=body).status_code == 422


def test_menu_chip_list_skips_made_items(client, test_db, owner_headers, sample_menu_items):
    _, _, r = _cajun(client, test_db, owner_headers)
    assert r.status_code == 201
    pepper = test_db.query(InventoryItem).filter_by(name="Pepper").one()
    r = client.post(f"{API}/costing", headers=owner_headers, json={
        "menu_item_id": sample_menu_items[0].id, "yield_units": "1", "ingredients": _lines((pepper, 10, "g")),
    })
    assert r.status_code == 201, r.text
    rows = client.get(f"{API}/costing", headers=owner_headers).json()
    assert [row["menu_item_name"] for row in rows] == ["Masala Dosa"]


def test_pack_price_same_family_and_presence(client, test_db, owner_headers):
    flour = _item(test_db, "Flour", "kg")
    out = _pack_price(client, owner_headers, flour, 35, 500, "g")
    assert Decimal(out["current_price"]) == 70 and out["pack_size"] is None
    chilli = InventoryItem(name="Chilli oil", unit="yes/no", count_mode="presence")
    test_db.add(chilli)
    test_db.commit()
    r = client.post(f"{API}/inventory/items/{chilli.id}/pack-price", headers=owner_headers,
                    json={"price": "10", "pack_quantity": "1", "pack_unit": "g"})
    assert r.status_code == 400


def _old_schema_engine():
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool, connect_args={"check_same_thread": False})
    with engine.begin() as c:
        for ddl in (
            "CREATE TABLE menu_items (id INTEGER PRIMARY KEY)",
            "CREATE TABLE inventory_items (id INTEGER PRIMARY KEY)",
            "CREATE TABLE dish_costings (id INTEGER PRIMARY KEY, "
            "menu_item_id INTEGER NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE, "
            "yield_units NUMERIC(12, 3) NOT NULL, target_margin_percent NUMERIC(5, 2), notes VARCHAR(500), "
            "packaging_mode VARCHAR(10), packaging_value NUMERIC(12, 2), labour_mode VARCHAR(10), "
            "labour_value NUMERIC(12, 2), fixed_mode VARCHAR(10), fixed_value NUMERIC(12, 2), "
            "wastage_mode VARCHAR(10), wastage_value NUMERIC(12, 2), created_at DATETIME, updated_at DATETIME)",
            "CREATE UNIQUE INDEX ix_dish_costings_menu_item_id ON dish_costings (menu_item_id)",
            "CREATE TABLE dish_costing_ingredients (id INTEGER PRIMARY KEY, "
            "costing_id INTEGER NOT NULL REFERENCES dish_costings(id) ON DELETE CASCADE, "
            "inventory_item_id INTEGER NOT NULL REFERENCES inventory_items(id), "
            "quantity NUMERIC(12, 4) NOT NULL, unit VARCHAR(20) NOT NULL, sort_order INTEGER NOT NULL)",
            "INSERT INTO menu_items VALUES (7)",
            "INSERT INTO inventory_items VALUES (3)",
            "INSERT INTO dish_costings (id, menu_item_id, yield_units, notes) VALUES (1, 7, 4, 'keep')",
            "INSERT INTO dish_costing_ingredients VALUES (1, 1, 3, 100, 'g', 0)",
        ):
            c.execute(text(ddl))
    return engine


def test_migration_rebuilds_old_table():
    engine = _old_schema_engine()
    ensure_costing_made_items(engine)
    ensure_costing_made_items(engine)  # idempotent

    with engine.begin() as c:
        cols = {r[1]: r[3] for r in c.exec_driver_sql("PRAGMA table_info(dish_costings)")}
        assert cols["menu_item_id"] == 0 and "inventory_item_id" in cols
        assert c.execute(text("SELECT menu_item_id, yield_units, notes FROM dish_costings")).one() == (7, 4, "keep")
        assert c.execute(text("SELECT costing_id, inventory_item_id FROM dish_costing_ingredients")).one() == (1, 3)
        assert c.exec_driver_sql("PRAGMA foreign_key_check").fetchall() == []
        assert c.exec_driver_sql("PRAGMA foreign_keys").scalar() == 0  # as before the rebuild
        # Two made items (NULL menu item) can now coexist.
        c.execute(text("INSERT INTO inventory_items VALUES (4)"))
        c.execute(text("INSERT INTO inventory_items VALUES (5)"))
        c.execute(text("INSERT INTO dish_costings (menu_item_id, inventory_item_id, yield_units) VALUES (NULL, 4, 1)"))
        c.execute(text("INSERT INTO dish_costings (menu_item_id, inventory_item_id, yield_units) VALUES (NULL, 5, 1)"))



def test_migration_failure_leaves_old_table(monkeypatch):
    engine = _old_schema_engine()

    def boom(*args, **kwargs):
        raise RuntimeError("died mid-rebuild")

    monkeypatch.setattr(Index, "create", boom)  # fails after the drop and rename
    with pytest.raises(RuntimeError):
        ensure_costing_made_items(engine)

    with engine.begin() as c:
        cols = {r[1]: r[3] for r in c.exec_driver_sql("PRAGMA table_info(dish_costings)")}
        assert cols["menu_item_id"] == 1 and "inventory_item_id" not in cols
        assert c.execute(text("SELECT menu_item_id, notes FROM dish_costings")).one() == (7, "keep")
        assert "dish_costings_new" not in {r[0] for r in c.exec_driver_sql("SELECT name FROM sqlite_master")}

def test_small_unit_pack_price_is_exact(client, test_db, owner_headers, sample_menu_items):
    paprika = _item(test_db, "Paprika", "g")
    salt = _item(test_db, "Salt", "g")
    _pack_price(client, owner_headers, paprika, 99, 52, "g")
    _pack_price(client, owner_headers, salt, 28, 1000, "g")
    for item, grams, cost in ((paprika, 52, "99.00"), (salt, 1000, "28.00")):
        r = client.post(f"{API}/costing/preview", headers=owner_headers, json={
            "menu_item_id": sample_menu_items[0].id, "yield_units": "1", "ingredients": _lines((item, grams, "g")),
        })
        assert Decimal(r.json()["ingredients"][0]["line_cost"]) == Decimal(cost)


def test_pack_price_rejects_unknown_unit_and_clears_stale_pack(client, test_db, owner_headers):
    flour = _item(test_db, "Flour", "kg")
    flour.pack_size, flour.pack_unit = Decimal(5), "pcs"
    test_db.commit()
    r = client.post(f"{API}/inventory/items/{flour.id}/pack-price", headers=owner_headers,
                    json={"price": "35", "pack_quantity": "500", "pack_unit": "bogus"})
    assert r.status_code == 400
    out = _pack_price(client, owner_headers, flour, 35, 500, "g")
    assert out["pack_size"] is None and out["pack_unit"] is None


def test_cost_flows_through_two_levels_and_patch_with_yield(client, test_db, owner_headers, sample_menu_items):
    pepper = _priced(client, test_db, owner_headers, [("Pepper", 100, 100, "g")])["Pepper"]  # 1 rupee/g
    mix = _item(test_db, "Spice mix", "g")
    rub = _item(test_db, "Rub", "g")
    r = client.post(f"{API}/costing", headers=owner_headers, json={
        "inventory_item_id": mix.id, "ingredients": _lines((pepper, 100, "g")),
    })
    assert r.status_code == 201, r.text  # 100 g costing 100
    r = client.post(f"{API}/costing", headers=owner_headers, json={
        "inventory_item_id": rub.id, "ingredients": _lines((mix, 50, "g")),
    })
    assert r.status_code == 201, r.text  # 50 g of mix = 50, yield 50
    rub_costing = r.json()["id"]
    dish = lambda: client.post(f"{API}/costing/preview", headers=owner_headers, json={
        "menu_item_id": sample_menu_items[0].id, "yield_units": "1", "ingredients": _lines((rub, 10, "g")),
    }).json()["ingredients"][0]["line_cost"]
    assert Decimal(dish()) == Decimal("10.00")

    # Explicit yield on PATCH: the same 50 g now make 100 g, so a gram costs half.
    r = client.patch(f"{API}/costing/{rub_costing}", headers=owner_headers, json={
        "inventory_item_id": rub.id, "yield_units": "100", "ingredients": _lines((mix, 50, "g")),
    })
    assert r.status_code == 200, r.text
    assert Decimal(r.json()["yield_units"]) == 100
    assert Decimal(dish()) == Decimal("5.00")


def test_cross_family_pack_price_is_refused_but_packets_still_work(client, test_db, owner_headers):
    vanilla = _item(test_db, "Vanilla", "g")
    r = client.post(f"{API}/inventory/items/{vanilla.id}/pack-price", headers=owner_headers,
                    json={"price": "439", "pack_quantity": "500", "pack_unit": "ml"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Vanilla is counted in g; give the pack in g or kg, or change its unit first"
    test_db.refresh(vanilla)
    assert vanilla.cost_per_unit is None
    # A count item priced by weight is a packet: unchanged.
    out = _pack_price(client, owner_headers, _item(test_db, "Paprika packet", "pcs"), 99, 52, "g")
    assert (out["pack_size"], out["pack_unit"]) == ("52.000", "g") or Decimal(str(out["pack_size"])) == 52


def test_made_item_returns_auto_yield_in_its_unit(client, test_db, owner_headers):
    pepper = _priced(client, test_db, owner_headers, [("Pepper", 100, 100, "g")])["Pepper"]
    mix = _item(test_db, "Big mix", "kg")
    r = client.post(f"{API}/costing", headers=owner_headers, json={
        "inventory_item_id": mix.id, "yield_units": "2", "ingredients": _lines((pepper, 300, "g"), (pepper, 200, "g")),
    })
    assert r.status_code == 201, r.text
    assert Decimal(r.json()["auto_yield"]) == Decimal("0.5")
    assert Decimal(r.json()["yield_units"]) == 2


def test_preview_works_for_a_saved_recipe(client, test_db, owner_headers, sample_menu_items):
    pepper = _priced(client, test_db, owner_headers, [("Pepper", 100, 100, "g")])["Pepper"]
    body = {"menu_item_id": sample_menu_items[0].id, "yield_units": "1", "ingredients": _lines((pepper, 10, "g"))}
    assert client.post(f"{API}/costing", headers=owner_headers, json=body).status_code == 201
    body["ingredients"] = _lines((pepper, 20, "g"))
    r = client.post(f"{API}/costing/preview", headers=owner_headers, json=body)
    assert r.status_code == 200, r.text
    assert Decimal(r.json()["raw_material_cost"]) == 20
    # A second recipe for the same dish is still refused.
    assert client.post(f"{API}/costing", headers=owner_headers, json=body).status_code == 409
