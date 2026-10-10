"""
Tests for dish costing math (app/utils/costing.py) and the costing endpoints.
"""

from decimal import Decimal

from app.models.inventory_models import InventoryItem, InventoryTransaction
from app.utils.costing import IngredientInput, OverheadInput, compute


def _no_overheads():
    return {
        kind: OverheadInput(mode="percent", value=Decimal("0"), inherited=True)
        for kind in ("packaging", "labour", "fixed", "wastage")
    }


def _ingredient(item_id, name, quantity, unit, stock_unit, cost_per_unit):
    return IngredientInput(
        item_id=item_id,
        name=name,
        quantity=Decimal(quantity),
        unit=unit,
        stock_unit=stock_unit,
        cost_per_unit=None if cost_per_unit is None else Decimal(cost_per_unit),
    )


class TestCompute:
    def test_normal_cost_calculation(self):
        """Units convert to the stock unit, overheads add on, margin is computed."""
        overheads = _no_overheads()
        overheads["packaging"] = OverheadInput(mode="amount", value=Decimal("5"), inherited=False)

        breakdown = compute(
            ingredients=[
                # 250 g of paneer at ₹400/kg = ₹100
                _ingredient(1, "Paneer", "250", "g", "kg", "400"),
                # 100 ml of cream at ₹200/L = ₹20
                _ingredient(2, "Cream", "100", "ml", "l", "200"),
            ],
            overheads=overheads,
            yield_units=Decimal("2"),
            selling_price=Decimal("150"),
        )

        assert [line.line_cost for line in breakdown.ingredients] == [
            Decimal("100.00"),
            Decimal("20.00"),
        ]
        assert breakdown.raw_material_cost == Decimal("120.00")
        assert breakdown.overhead_cost == Decimal("5.00")
        assert breakdown.total_cost == Decimal("125.00")
        assert breakdown.cost_per_unit == Decimal("62.50")
        assert breakdown.margin_amount == Decimal("87.50")
        assert breakdown.is_complete is True
        assert breakdown.warnings == []

    def test_missing_price_is_flagged_not_free(self):
        """None and a 0.00 placeholder both count as missing and make the dish incomplete."""
        breakdown = compute(
            ingredients=[
                _ingredient(1, "Paneer", "250", "g", "kg", "400"),
                _ingredient(2, "Salt", "5", "g", "kg", None),
                _ingredient(3, "Onion", "100", "g", "kg", "0.00"),
            ],
            overheads=_no_overheads(),
            yield_units=Decimal("1"),
        )

        paneer, salt, onion = breakdown.ingredients
        assert paneer.price_missing is False
        assert salt.price_missing is True
        assert onion.price_missing is True
        assert salt.line_cost == onion.line_cost == Decimal("0.00")
        assert breakdown.raw_material_cost == Decimal("100.00")
        assert breakdown.is_complete is False
        assert any("Salt" in w for w in breakdown.warnings)
        assert any("Onion" in w for w in breakdown.warnings)

    def test_unconvertible_unit_costs_one_line_at_zero(self):
        """A bad unit on one ingredient must not raise and sink the whole dish."""
        breakdown = compute(
            ingredients=[
                _ingredient(1, "Paneer", "250", "g", "kg", "400"),
                # grams against a stock unit of pieces: different families
                _ingredient(2, "Eggs", "50", "g", "pcs", "6"),
                # a unit the converter has never heard of
                _ingredient(3, "Ghee", "1", "tbsp", "kg", "600"),
            ],
            overheads=_no_overheads(),
            yield_units=Decimal("1"),
        )

        paneer, eggs, ghee = breakdown.ingredients
        assert paneer.unit_error is False
        assert paneer.line_cost == Decimal("100.00")
        assert eggs.unit_error is True
        assert eggs.line_cost == Decimal("0.00")
        assert ghee.unit_error is True
        assert ghee.line_cost == Decimal("0.00")
        assert breakdown.raw_material_cost == Decimal("100.00")
        assert breakdown.is_complete is False
        assert any("Eggs" in w for w in breakdown.warnings)
        assert any("Ghee" in w for w in breakdown.warnings)
        # Grams of eggs counted in pieces would cost with a pack size
        # (1 pcs = 50 g); tbsp is a unit no pack size can fix.
        assert eggs.needs_pack_size is True
        assert ghee.needs_pack_size is False

    def test_pack_size_bridges_a_recipe_unit_to_the_stock_unit(self):
        """30 ml of chilli oil, counted in ₹350 bottles of 700 ml, is 30/700 of a bottle: ₹15."""
        oil = IngredientInput(
            item_id=1, name="Chilli oil", quantity=Decimal("30"), unit="ml", stock_unit="bottle",
            cost_per_unit=Decimal("350"), pack_size=Decimal("700"), pack_unit="ml",
        )
        # 1 portion = 6 pcs of wings; the recipe uses 12 pcs.
        wings = IngredientInput(
            item_id=2, name="Wings", quantity=Decimal("12"), unit="pcs", stock_unit="portion",
            cost_per_unit=Decimal("90"), pack_size=Decimal("6"), pack_unit="pcs",
        )
        # A litre pack bridges millilitres too: same family as the pack unit.
        syrup = IngredientInput(
            item_id=3, name="Syrup", quantity=Decimal("50"), unit="ml", stock_unit="bottle",
            cost_per_unit=Decimal("200"), pack_size=Decimal("1"), pack_unit="l",
        )

        breakdown = compute(ingredients=[oil, wings, syrup], overheads=_no_overheads(), yield_units=Decimal("1"))

        assert [line.line_cost for line in breakdown.ingredients] == [
            Decimal("15.00"), Decimal("180.00"), Decimal("10.00"),
        ]
        assert not any(line.unit_error or line.needs_pack_size for line in breakdown.ingredients)
        assert breakdown.is_complete is True

    def test_missing_or_wrong_pack_size_asks_for_one(self):
        """No pack size, or one in the wrong family, flags the line instead of guessing."""
        no_pack = _ingredient(1, "Chilli oil", "30", "ml", "bottle", "350")
        wrong_family = IngredientInput(
            item_id=2, name="Sauce", quantity=Decimal("30"), unit="ml", stock_unit="bottle",
            cost_per_unit=Decimal("350"), pack_size=Decimal("500"), pack_unit="g",
        )
        presence = IngredientInput(
            item_id=3, name="Coriander", quantity=Decimal("5"), unit="g", stock_unit="yes/no",
            cost_per_unit=None, is_presence=True,
        )

        breakdown = compute(ingredients=[no_pack, wrong_family, presence], overheads=_no_overheads(), yield_units=Decimal("1"))

        assert [line.needs_pack_size for line in breakdown.ingredients] == [True, True, False]
        assert all(line.unit_error and line.line_cost == 0 for line in breakdown.ingredients)
        assert breakdown.is_complete is False
        assert any("1 bottle = how many ml" in w for w in breakdown.warnings)


class TestCostingEndpoints:
    def test_update_to_already_costed_menu_item_is_409(
        self, client, test_db, owner_headers, sample_menu_items
    ):
        """This path used sataus_code=, which raised TypeError and returned a 500."""
        item = InventoryItem(name="Paneer", unit="kg", cost_per_unit=Decimal("400"))
        test_db.add(item)
        test_db.commit()

        def body(menu_item_id):
            return {
                "menu_item_id": menu_item_id,
                "yield_units": "1",
                "ingredients": [{"inventory_item_id": item.id, "quantity": "250", "unit": "g"}],
            }

        first, second = sample_menu_items[0].id, sample_menu_items[1].id
        r1 = client.post("/api/v1/costing", json=body(first), headers=owner_headers)
        assert r1.status_code == 201, r1.text
        r2 = client.post("/api/v1/costing", json=body(second), headers=owner_headers)
        assert r2.status_code == 201, r2.text

        r = client.patch(
            f"/api/v1/costing/{r2.json()['id']}", json=body(first), headers=owner_headers
        )
        assert r.status_code == 409
        assert "already exists" in r.json()["detail"]

    def test_preview_with_bad_unit_returns_breakdown(
        self, client, test_db, owner_headers, sample_menu_items
    ):
        """One uncostable ingredient comes back as a flagged line, not an error."""
        good = InventoryItem(name="Paneer", unit="kg", cost_per_unit=Decimal("400"))
        bad = InventoryItem(name="Eggs", unit="pcs", cost_per_unit=Decimal("6"))
        test_db.add_all([good, bad])
        test_db.commit()

        r = client.post(
            "/api/v1/costing/preview",
            json={
                "menu_item_id": sample_menu_items[0].id,
                "yield_units": "1",
                "ingredients": [
                    {"inventory_item_id": good.id, "quantity": "250", "unit": "g"},
                    {"inventory_item_id": bad.id, "quantity": "50", "unit": "g"},
                ],
            },
            headers=owner_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["is_complete"] is False
        assert [line["unit_error"] for line in data["ingredients"]] == [False, True]
        assert Decimal(data["raw_material_cost"]) == Decimal("100.00")

    def test_preview_costs_ml_against_an_item_counted_in_bottles(
        self, client, test_db, owner_headers, sample_menu_items
    ):
        """The item's pack size reaches the API: 30 ml of a ₹350, 700 ml bottle is ₹15."""
        oil = InventoryItem(name="Chilli oil", unit="bottle", cost_per_unit=Decimal("350"),
                            pack_size=Decimal("700"), pack_unit="ml")
        test_db.add(oil)
        test_db.commit()

        r = client.post(
            "/api/v1/costing/preview",
            json={
                "menu_item_id": sample_menu_items[0].id,
                "yield_units": "1",
                "ingredients": [{"inventory_item_id": oil.id, "quantity": "30", "unit": "ml"}],
            },
            headers=owner_headers,
        )
        assert r.status_code == 200, r.text
        line = r.json()["ingredients"][0]
        assert (line["unit_error"], line["needs_pack_size"]) == (False, False)
        assert Decimal(line["line_cost"]) == Decimal("15.00")

    def test_preview_prices_from_the_latest_purchase(
        self, client, test_db, owner_headers, sample_menu_items
    ):
        """A paid purchase outranks the typed price: 4 kg for ₹1,600 is ₹400/kg, not 300."""
        paneer = InventoryItem(name="Paneer", unit="kg", cost_per_unit=Decimal("300"))
        test_db.add(paneer)
        test_db.flush()
        test_db.add(InventoryTransaction(
            item_id=paneer.id, transaction_type="PURCHASE", quantity=Decimal("4"),
            total_amount=Decimal("1600"), recorded_by="test",
            previous_quantity=Decimal("0"), new_quantity=Decimal("4"),
        ))
        test_db.commit()

        r = client.post(
            "/api/v1/costing/preview",
            json={
                "menu_item_id": sample_menu_items[0].id,
                "yield_units": "1",
                "ingredients": [{"inventory_item_id": paneer.id, "quantity": "250", "unit": "g"}],
            },
            headers=owner_headers,
        )
        assert r.status_code == 200, r.text
        assert Decimal(r.json()["raw_material_cost"]) == Decimal("100.00")
