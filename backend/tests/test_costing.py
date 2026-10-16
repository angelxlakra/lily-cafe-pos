"""
Tests for dish costing math (app/utils/costing.py) and the costing endpoints.
"""

from datetime import datetime
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

    def test_a_recipe_in_the_items_own_unit_always_costs(self):
        """1 packet of noodles counted in packets is 1 packet, though "packet" isn't a unit the converter knows."""
        breakdown = compute(
            ingredients=[_ingredient(1, "Glass noodles", "1", "Packet", "packet", "60")],
            overheads=_no_overheads(), yield_units=Decimal("1"),
        )

        line = breakdown.ingredients[0]
        assert (line.unit_error, line.reason, line.line_cost) == (False, None, Decimal("60.00"))

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

        oil, sauce, coriander = breakdown.ingredients
        assert [line.needs_pack_size for line in breakdown.ingredients] == [True, True, False]
        assert oil.unit_error and sauce.unit_error and oil.line_cost == sauce.line_cost == 0
        assert (oil.reason, sauce.reason) == ("needs_pack_size", "needs_pack_size")
        assert breakdown.is_complete is False
        assert any("1 bottle = how many ml" in w for w in breakdown.warnings)


    def test_yes_no_item_is_shown_but_never_a_gap(self):
        """Coriander on a recipe is covered by overheads: no cost, no reason, dish still complete."""
        coriander = IngredientInput(
            item_id=2, name="Coriander", quantity=Decimal("5"), unit="g", stock_unit="yes/no",
            cost_per_unit=None, is_presence=True,
        )
        breakdown = compute(
            ingredients=[_ingredient(1, "Paneer", "250", "g", "kg", "400"), coriander],
            overheads=_no_overheads(), yield_units=Decimal("1"),
        )

        line = breakdown.ingredients[1]
        assert (line.is_presence, line.reason, line.line_cost) == (True, None, Decimal("0.00"))
        assert breakdown.is_complete is True
        assert not any("Coriander" in w for w in breakdown.warnings)

    def test_a_retired_yes_no_item_is_still_a_gap(self):
        """Covered by overheads while it's stocked; once retired it needs swapping, like any retired item."""
        coriander = IngredientInput(
            item_id=1, name="Coriander", quantity=Decimal("5"), unit="g", stock_unit="yes/no",
            cost_per_unit=None, is_presence=True, is_active=False,
        )
        breakdown = compute(ingredients=[coriander], overheads=_no_overheads(), yield_units=Decimal("1"))

        assert breakdown.ingredients[0].reason == "retired"
        assert breakdown.is_complete is False

    def test_a_dish_that_costs_nothing_gets_no_suggested_price(self):
        """Only yes/no items: complete, ₹0, and no ₹0 price to apply to the menu."""
        coriander = IngredientInput(
            item_id=1, name="Coriander", quantity=Decimal("5"), unit="g", stock_unit="yes/no",
            cost_per_unit=None, is_presence=True,
        )
        breakdown = compute(
            ingredients=[coriander], overheads=_no_overheads(), yield_units=Decimal("1"),
            target_margin_percent=Decimal("65"),
        )

        assert breakdown.is_complete is True
        assert breakdown.suggested_price is None

    def test_every_gap_has_one_named_reason(self):
        retired = _ingredient(4, "Old ghee", "10", "g", "kg", "600")
        retired.is_active = False
        breakdown = compute(
            ingredients=[
                _ingredient(1, "Paneer", "250", "g", "kg", "400"),
                _ingredient(2, "Maida", "30", "g", "kg", "0.00"),
                _ingredient(3, "Ghee", "1", "tbsp", "kg", "600"),
                retired,
            ],
            overheads=_no_overheads(), yield_units=Decimal("1"),
        )

        assert [line.reason for line in breakdown.ingredients] == [None, "no_price", "unknown_unit", "retired"]

    def test_suggested_price_rounds_up_to_ten_and_waits_for_a_complete_dish(self):
        """₹100 of paneer at a 65% target is ₹285.71, offered as ₹290; with a gap, nothing is offered."""
        complete = compute(
            ingredients=[_ingredient(1, "Paneer", "250", "g", "kg", "400")],
            overheads=_no_overheads(), yield_units=Decimal("1"), target_margin_percent=Decimal("65"),
        )
        with_gap = compute(
            ingredients=[_ingredient(1, "Paneer", "250", "g", "kg", "400"), _ingredient(2, "Maida", "30", "g", "kg", None)],
            overheads=_no_overheads(), yield_units=Decimal("1"), target_margin_percent=Decimal("65"),
        )

        assert complete.suggested_price == Decimal("290")
        assert with_gap.suggested_price is None

    def test_price_source_and_date_ride_along_only_with_a_real_price(self):
        bought = datetime(2026, 10, 12, 5)
        paneer = _ingredient(1, "Paneer", "250", "g", "kg", "400")
        paneer.price_source, paneer.price_as_of = "purchase", bought
        maida = _ingredient(2, "Maida", "30", "g", "kg", "0.00")
        maida.price_source = "typed"

        lines = compute(ingredients=[paneer, maida], overheads=_no_overheads(), yield_units=Decimal("1")).ingredients

        assert (lines[0].price_source, lines[0].price_as_of) == ("purchase", bought)
        assert (lines[1].price_source, lines[1].price_as_of) == (None, None)


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

    def test_preview_line_says_where_its_price_came_from(
        self, client, test_db, owner_headers, sample_menu_items
    ):
        paneer = InventoryItem(name="Paneer", unit="kg", cost_per_unit=Decimal("300"))
        salt = InventoryItem(name="Salt", unit="kg", cost_per_unit=Decimal("20"))
        test_db.add_all([paneer, salt])
        test_db.flush()
        test_db.add(InventoryTransaction(
            item_id=paneer.id, transaction_type="PURCHASE", quantity=Decimal("4"),
            total_amount=Decimal("1600"), recorded_by="test",
            previous_quantity=Decimal("0"), new_quantity=Decimal("4"), created_at=datetime(2026, 10, 12, 5),
        ))
        test_db.commit()

        r = client.post("/api/v1/costing/preview", headers=owner_headers, json={
            "menu_item_id": sample_menu_items[0].id, "yield_units": "1",
            "ingredients": [
                {"inventory_item_id": paneer.id, "quantity": "250", "unit": "g"},
                {"inventory_item_id": salt.id, "quantity": "5", "unit": "g"},
            ],
        })

        assert r.status_code == 200, r.text
        bought, typed = r.json()["ingredients"]
        assert bought["price_source"] == "purchase" and bought["price_as_of"].startswith("2026-10-12")
        assert (typed["price_source"], typed["price_as_of"]) == ("typed", None)

    def _costing(self, client, owner_headers, menu_item_id, item_ids):
        r = client.post("/api/v1/costing", headers=owner_headers, json={
            "menu_item_id": menu_item_id, "yield_units": "1",
            "ingredients": [{"inventory_item_id": i, "quantity": "250", "unit": "g"} for i in item_ids],
        })
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def test_apply_price_writes_whole_rupees(self, client, test_db, owner_headers, sample_menu_items):
        """₹100 of paneer plus the default 30% overheads is ₹130; at 65% that's ₹371.43, so ₹380."""
        paneer = InventoryItem(name="Paneer", unit="kg", cost_per_unit=Decimal("400"))
        test_db.add(paneer)
        test_db.commit()
        costing_id = self._costing(client, owner_headers, sample_menu_items[0].id, [paneer.id])

        r = client.post(f"/api/v1/costing/{costing_id}/apply-price", headers=owner_headers, json={"price": "380"})

        assert r.status_code == 200, r.text
        test_db.refresh(sample_menu_items[0])
        assert sample_menu_items[0].price == 38000

    def test_apply_price_refuses_a_dish_with_gaps(self, client, test_db, owner_headers, sample_menu_items):
        maida = InventoryItem(name="Maida", unit="kg", cost_per_unit=None)
        test_db.add(maida)
        test_db.commit()
        costing_id = self._costing(client, owner_headers, sample_menu_items[0].id, [maida.id])

        r = client.post(f"/api/v1/costing/{costing_id}/apply-price", headers=owner_headers, json={"price": "100"})

        assert r.status_code == 409
        test_db.refresh(sample_menu_items[0])
        assert sample_menu_items[0].price == 8000

    def test_apply_price_refuses_a_price_the_owner_didnt_see(self, client, test_db, owner_headers, sample_menu_items):
        """Confirmed ₹380, then a purchase moved the cost: the menu keeps its price and the answer says the new one."""
        paneer = InventoryItem(name="Paneer", unit="kg", cost_per_unit=Decimal("400"))
        test_db.add(paneer)
        test_db.commit()
        costing_id = self._costing(client, owner_headers, sample_menu_items[0].id, [paneer.id])
        test_db.add(InventoryTransaction(
            item_id=paneer.id, transaction_type="PURCHASE", quantity=Decimal("1"),
            total_amount=Decimal("500"), recorded_by="test",
            previous_quantity=Decimal("0"), new_quantity=Decimal("1"),
        ))
        test_db.commit()

        r = client.post(f"/api/v1/costing/{costing_id}/apply-price", headers=owner_headers, json={"price": "380"})

        assert r.status_code == 409
        assert "₹470" in r.json()["detail"]
        test_db.refresh(sample_menu_items[0])
        assert sample_menu_items[0].price == 8000

    def test_preview_saves_nothing(self, client, test_db, owner_headers, sample_menu_items):
        from app.models.costing_models import DishCosting, DishCostingIngredient
        paneer = InventoryItem(name="Paneer", unit="kg", cost_per_unit=Decimal("400"))
        test_db.add(paneer)
        test_db.commit()

        r = client.post("/api/v1/costing/preview", headers=owner_headers, json={
            "menu_item_id": sample_menu_items[0].id, "yield_units": "1",
            "ingredients": [{"inventory_item_id": paneer.id, "quantity": "250", "unit": "g"}],
        })

        assert r.status_code == 200, r.text
        assert test_db.query(DishCosting).count() == test_db.query(DishCostingIngredient).count() == 0

    def test_defaults_are_the_cafe_wide_overheads(self, client, owner_headers):
        r = client.get("/api/v1/costing/defaults", headers=owner_headers)

        assert r.status_code == 200, r.text
        data = r.json()
        assert data["labour"] == {"mode": "percent", "value": "15"}
        assert Decimal(data["target_margin_percent"]) == Decimal("65")

    def test_costs_are_the_owners_alone(self, client, auth_headers, owner_headers):
        """A staff login can't read costs or margins, not even the defaults."""
        assert client.get("/api/v1/costing", headers=auth_headers).status_code == 403
        assert client.get("/api/v1/costing/defaults", headers=auth_headers).status_code == 403
        assert client.get("/api/v1/costing", headers=owner_headers).status_code == 200

    def test_list_counts_each_dishs_gaps(self, client, test_db, owner_headers, sample_menu_items):
        paneer = InventoryItem(name="Paneer", unit="kg", cost_per_unit=Decimal("400"))
        maida = InventoryItem(name="Maida", unit="kg", cost_per_unit=None)
        test_db.add_all([paneer, maida])
        test_db.commit()
        self._costing(client, owner_headers, sample_menu_items[0].id, [paneer.id, maida.id])

        (row,) = client.get("/api/v1/costing", headers=owner_headers).json()

        assert (row["gap_count"], row["is_complete"]) == (1, False)
