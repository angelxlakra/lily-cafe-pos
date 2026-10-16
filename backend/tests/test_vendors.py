"""
Vendors and the order message's data: a default vendor per item, set from
the setup grid or an item edit, and a vendor's name and phone kept current.
"""

from decimal import Decimal

import pytest

from app.models.inventory_models import InventoryItem, Vendor

ITEMS = "/api/v1/inventory/items"
VENDORS = "/api/v1/inventory/vendors"


@pytest.fixture
def raju(test_db):
    vendor = Vendor(name="Raju Chicken Centre")
    test_db.add(vendor)
    test_db.commit()
    return vendor


@pytest.fixture
def chicken(test_db):
    item = InventoryItem(name="Chicken boneless", unit="kg", current_quantity=Decimal("2"), min_threshold=Decimal("5"))
    test_db.add(item)
    test_db.commit()
    return item


def test_setup_grid_sets_and_clears_a_default_vendor(client, owner_headers, test_db, raju, chicken):
    r = client.patch(ITEMS, headers=owner_headers, json={"items": [{"id": chicken.id, "default_vendor_id": raju.id}]})
    assert r.status_code == 200, r.text
    test_db.refresh(chicken)
    assert chicken.default_vendor_id == raju.id

    listed = client.get(ITEMS, headers=owner_headers, params={"is_active": True}).json()["items"]
    assert listed[0]["default_vendor_id"] == raju.id

    r = client.patch(ITEMS, headers=owner_headers, json={"items": [{"id": chicken.id, "default_vendor_id": None}]})
    assert r.status_code == 200, r.text
    test_db.refresh(chicken)
    assert chicken.default_vendor_id is None


def test_an_unknown_vendor_is_refused_everywhere(client, owner_headers, chicken):
    bulk = client.patch(ITEMS, headers=owner_headers, json={"items": [{"id": chicken.id, "default_vendor_id": 999}]})
    one = client.patch(f"{ITEMS}/{chicken.id}", headers=owner_headers, json={"default_vendor_id": 999})
    new = client.post(ITEMS, headers=owner_headers, json={"name": "Paneer", "unit": "kg", "default_vendor_id": 999})

    assert (bulk.status_code, one.status_code, new.status_code) == (400, 400, 400)


def test_owner_sets_a_vendors_phone_and_name(client, owner_headers, raju):
    r = client.patch(f"{VENDORS}/{raju.id}", headers=owner_headers, json={"phone": " 98450 12345 ", "name": " Raju Chicken "})

    assert r.status_code == 200, r.text
    assert (r.json()["phone"], r.json()["name"]) == ("98450 12345", "Raju Chicken")


def test_a_rename_cant_make_two_vendors_one_name(client, owner_headers, test_db, raju):
    other = Vendor(name="Lakshmi Dairy")
    test_db.add(other)
    test_db.commit()

    r = client.patch(f"{VENDORS}/{other.id}", headers=owner_headers, json={"name": "raju chicken centre"})

    assert r.status_code == 409


def test_only_the_owner_edits_a_vendor(client, auth_headers, raju):
    assert client.patch(f"{VENDORS}/{raju.id}", headers=auth_headers, json={"phone": "1"}).status_code == 403
