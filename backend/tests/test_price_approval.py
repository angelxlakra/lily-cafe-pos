"""A purchase logged by staff at a new price waits for the owner before it becomes the price."""

from decimal import Decimal

import pytest

from app.models.inventory_models import InventoryItem

PURCHASE = "/api/v1/inventory/transactions/purchase"
PURCHASES = "/api/v1/inventory/purchases"
ITEMS = "/api/v1/inventory/items"


@pytest.fixture
def onion(test_db):
    item = InventoryItem(name="Onion", unit="kg", current_quantity=Decimal("2"), cost_per_unit=Decimal("32"))
    test_db.add(item)
    test_db.commit()
    return item


def _n(value):
    """The API sends decimals as strings; compare as numbers."""
    return Decimal(str(value))


def _buy(client, headers, item, quantity="4", total="160"):
    response = client.post(PURCHASE, headers=headers, json={
        "items": [{"item_id": item.id, "quantity": quantity, "total_amount": total}],
    })
    assert response.status_code == 201, response.text
    return response.json()["transactions"][0]


def _item(client, headers, item):
    return client.get(f"{ITEMS}/{item.id}", headers=headers).json()


def _review(client, headers, purchase_id, action):
    return client.post(f"{PURCHASES}/{purchase_id}/price-review", headers=headers, json={"action": action})


def test_admin_purchase_is_pending_and_not_the_price(client, auth_headers, onion):
    line = _buy(client, auth_headers, onion)  # 160 / 4 = 40, typed price is 32

    item = _item(client, auth_headers, onion)
    assert line["price_status"] == "pending"
    assert (_n(item["current_price"]), item["price_source"]) == (_n(32), "typed")


def test_owner_purchase_is_approved(client, owner_headers, onion):
    line = _buy(client, owner_headers, onion)

    assert line["price_status"] == "approved"
    assert _n(_item(client, owner_headers, onion)["current_price"]) == _n(40)


def test_same_price_purchase_auto_approved(client, auth_headers, onion):
    line = _buy(client, auth_headers, onion, total="128")  # 32/kg, the current price

    assert line["price_status"] == "approved"


def test_approve_makes_it_the_price(client, auth_headers, owner_headers, onion):
    line = _buy(client, auth_headers, onion)

    assert _review(client, owner_headers, line["id"], "approve").json()["price_status"] == "approved"

    item = _item(client, owner_headers, onion)
    assert _n(item["current_quantity"]) == _n(6)
    assert _n(item["current_price"]) == _n(40)
    assert _n(client.get(PURCHASES, headers=owner_headers).json()["total_amount"]) == _n(160)


def test_reject_keeps_stock_but_not_price(client, auth_headers, owner_headers, onion):
    line = _buy(client, auth_headers, onion)

    assert _review(client, owner_headers, line["id"], "reject").json()["price_status"] == "rejected"

    item = _item(client, owner_headers, onion)
    assert _n(item["current_quantity"]) == _n(6)
    assert _n(item["current_price"]) == _n(32)
    assert _n(client.get(PURCHASES, headers=owner_headers).json()["total_amount"]) == _n(160)


def test_out_of_order_approval_uses_highest_id(client, auth_headers, owner_headers, onion):
    first = _buy(client, auth_headers, onion, total="160")   # 40/kg
    second = _buy(client, auth_headers, onion, total="176")  # 44/kg

    _review(client, owner_headers, second["id"], "approve")
    _review(client, owner_headers, first["id"], "approve")

    assert _n(_item(client, owner_headers, onion)["current_price"]) == _n(44)


def test_pending_prices_lists_change(client, auth_headers, owner_headers, onion, test_db):
    line = _buy(client, auth_headers, onion)
    fresh = InventoryItem(name="Truffle", unit="kg", current_quantity=Decimal("0"))
    test_db.add(fresh)
    test_db.commit()
    new_line = _buy(client, auth_headers, fresh, quantity="1", total="900")

    rows = {r["purchase_id"]: r for r in client.get(f"{PURCHASES}/pending-prices", headers=owner_headers).json()}

    row = rows[line["id"]]
    assert (Decimal(str(row["old_price"])), Decimal(str(row["new_price"])), Decimal(str(row["change"]))) == (
        Decimal(32), Decimal(40), Decimal("0.25"))
    assert row["is_new_item"] is False
    assert row["item_name"] == "Onion"
    assert row["ripple"] == {"affected_dishes": [], "unaffected_count": 0, "made_items": []}
    assert rows[new_line["id"]]["is_new_item"] is True
    assert rows[new_line["id"]]["old_price"] is None


def test_review_drops_it_from_the_pending_list(client, auth_headers, owner_headers, onion):
    line = _buy(client, auth_headers, onion)
    _review(client, owner_headers, line["id"], "approve")

    assert client.get(f"{PURCHASES}/pending-prices", headers=owner_headers).json() == []
    assert _review(client, owner_headers, line["id"], "approve").status_code == 400
    assert _review(client, owner_headers, 99999, "approve").status_code == 404


def test_approve_all(client, auth_headers, owner_headers, onion):
    ids = [_buy(client, auth_headers, onion, total=t)["id"] for t in ("160", "176")]

    # Only what the owner was shown: no list, no approval.
    assert client.post(f"{PURCHASES}/price-review/approve-all", headers=owner_headers).status_code == 422
    r = client.post(f"{PURCHASES}/price-review/approve-all", headers=owner_headers, json={"purchase_ids": ids})
    assert r.json() == {"approved": 2}
    assert _n(_item(client, owner_headers, onion)["current_price"]) == _n(44)


def test_admin_cannot_review(client, auth_headers, onion):
    line = _buy(client, auth_headers, onion)

    assert _review(client, auth_headers, line["id"], "approve").status_code == 403
    assert client.get(f"{PURCHASES}/pending-prices", headers=auth_headers).status_code == 403
    assert client.post(f"{PURCHASES}/price-review/approve-all", headers=auth_headers).status_code == 403


def test_edit_total_resets_to_pending(client, auth_headers, owner_headers, onion):
    line = _buy(client, auth_headers, onion)
    _review(client, owner_headers, line["id"], "approve")

    edited = client.patch(f"{PURCHASES}/{line['id']}", headers=auth_headers, json={"total_amount": "200"})

    assert edited.json()["price_status"] == "pending"
    assert _n(_item(client, owner_headers, onion)["current_price"]) == _n(32)


def test_owner_edit_keeps_it_approved(client, auth_headers, owner_headers, onion):
    line = _buy(client, auth_headers, onion)
    _review(client, owner_headers, line["id"], "approve")

    edited = client.patch(f"{PURCHASES}/{line['id']}", headers=owner_headers, json={"total_amount": "200"})

    assert edited.json()["price_status"] == "approved"
    assert _n(_item(client, owner_headers, onion)["current_price"]) == _n(50)


def test_staff_purchase_without_a_total_or_for_nothing_is_approved(client, auth_headers, onion):
    no_total = client.post(PURCHASE, headers=auth_headers, json={"items": [{"item_id": onion.id, "quantity": "1"}]})
    gift = client.post(PURCHASE, headers=auth_headers, json={
        "items": [{"item_id": onion.id, "quantity": "1", "total_amount": "0", "notes": "free"}]})

    assert no_total.json()["transactions"][0]["price_status"] == "approved"
    assert gift.json()["transactions"][0]["price_status"] == "approved"


def test_admin_quantity_edit_goes_back_to_pending(client, auth_headers, owner_headers, onion):
    line = _buy(client, auth_headers, onion)  # 160 / 4 = 40
    _review(client, owner_headers, line["id"], "approve")

    edited = client.patch(f"{PURCHASES}/{line['id']}", headers=auth_headers, json={"quantity": "2"})  # 80/kg

    assert edited.json()["price_status"] == "pending"


def test_admin_edit_to_no_total_or_zero_is_approved_and_pending_list_still_works(client, auth_headers, owner_headers, onion):
    first = _buy(client, auth_headers, onion)
    second = _buy(client, auth_headers, onion)

    nulled = client.patch(f"{PURCHASES}/{first['id']}", headers=auth_headers, json={"total_amount": None})
    zeroed = client.patch(f"{PURCHASES}/{second['id']}", headers=auth_headers, json={"total_amount": "0", "notes": "free"})

    assert nulled.json()["price_status"] == "approved"
    assert zeroed.json()["price_status"] == "approved"
    assert client.get(f"{PURCHASES}/pending-prices", headers=owner_headers).status_code == 200
    assert _n(_item(client, owner_headers, onion)["current_price"]) == _n(32)


def test_notes_only_edit_keeps_it_approved(client, auth_headers, owner_headers, onion):
    line = _buy(client, auth_headers, onion)
    _review(client, owner_headers, line["id"], "approve")

    edited = client.patch(f"{PURCHASES}/{line['id']}", headers=auth_headers, json={"notes": "from Raju"})

    assert edited.json()["price_status"] == "approved"


def test_brand_round_trips(client, owner_headers, onion):
    assert client.patch(f"{ITEMS}/{onion.id}", headers=owner_headers, json={"brand": "Nashik"}).status_code == 200
    assert _item(client, owner_headers, onion)["brand"] == "Nashik"

    bulk = client.patch(ITEMS, headers=owner_headers, json={"items": [{"id": onion.id, "brand": "Amul"}]})
    assert bulk.status_code == 200
    listed = client.get(ITEMS, headers=owner_headers).json()["items"]
    assert [i["brand"] for i in listed if i["id"] == onion.id] == ["Amul"]


def test_presence_item_purchase_is_never_pending(client, auth_headers, test_db):
    salt = InventoryItem(name="Salt", unit="pkt", count_mode="presence")
    test_db.add(salt)
    test_db.commit()

    line = _buy(client, auth_headers, salt, quantity="1", total="40")

    assert line["price_status"] == "approved"


def test_pending_row_older_than_an_approved_purchase_is_superseded(client, auth_headers, owner_headers, onion):
    older = _buy(client, auth_headers, onion, total="160")        # pending, 40/kg
    _buy(client, owner_headers, onion, total="176")               # approved later, 44/kg
    newer = _buy(client, auth_headers, onion, total="200")        # pending, after the approved one

    rows = {r["purchase_id"]: r for r in client.get(f"{PURCHASES}/pending-prices", headers=owner_headers).json()}

    assert rows[older["id"]]["superseded"] is True
    assert rows[newer["id"]]["superseded"] is False


def test_approve_all_only_the_listed_ids(client, auth_headers, owner_headers, onion):
    first = _buy(client, auth_headers, onion, total="160")
    second = _buy(client, auth_headers, onion, total="176")

    r = client.post(f"{PURCHASES}/price-review/approve-all", headers=owner_headers, json={"purchase_ids": [first["id"]]})

    assert r.json() == {"approved": 1}
    left = client.get(f"{PURCHASES}/pending-prices", headers=owner_headers).json()
    assert [row["purchase_id"] for row in left] == [second["id"]]
