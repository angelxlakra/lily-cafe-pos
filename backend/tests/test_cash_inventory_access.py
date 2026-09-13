"""
Access rules for the cash counter and inventory.

Cash counter: every route needs a login, actions are recorded against the
real username, and previous days are owner-only.

Inventory: every route needs a login. Stock movements are day-to-day work any
signed-in staff member can do; categories and items are master data and,
like the menu, owner-only.
"""

from datetime import date, timedelta

import pytest

from app.models.cash_models import DailyCashCounter
from app.models.inventory_models import InventoryCategory, InventoryItem


TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)


def _open_payload(day: date):
    return {
        "date": day.isoformat(),
        "opening_500s": 2,
        "opening_200s": 0,
        "opening_100s": 5,
        "opening_50s": 0,
        "opening_20s": 0,
        "opening_10s": 0,
        "notes": "morning float",
    }


def _close_payload(day: date):
    return {
        "date": day.isoformat(),
        "closing_500s": 3,
        "closing_200s": 0,
        "closing_100s": 5,
        "closing_50s": 0,
        "closing_20s": 0,
        "closing_10s": 0,
        "notes": "end of day",
    }


@pytest.fixture
def yesterdays_counter(test_db):
    counter = DailyCashCounter(
        date=YESTERDAY,
        opening_balance=1000,
        opened_by="admin",
        opening_500s=2,
        opening_200s=0,
        opening_100s=0,
        opening_50s=0,
        opening_20s=0,
        opening_10s=0,
    )
    test_db.add(counter)
    test_db.commit()
    test_db.refresh(counter)
    return counter


@pytest.fixture
def inventory_category(test_db):
    category = InventoryCategory(name="Dry Goods")
    test_db.add(category)
    test_db.commit()
    test_db.refresh(category)
    return category


@pytest.fixture
def inventory_item(test_db, inventory_category):
    item = InventoryItem(
        name="Coffee Beans",
        category_id=inventory_category.id,
        unit="kg",
        current_quantity=10,
        min_threshold=2,
    )
    test_db.add(item)
    test_db.commit()
    test_db.refresh(item)
    return item


# ============================================================================
# Cash counter
# ============================================================================


class TestCashCounterRequiresLogin:
    """Every cash route was previously reachable with no credentials at all."""

    @pytest.mark.parametrize(
        "method,path,body",
        [
            ("post", "/api/v1/cash-counter/open", _open_payload(TODAY)),
            ("post", "/api/v1/cash-counter/close", _close_payload(TODAY)),
            ("post", "/api/v1/cash-counter/verify/1", {"owner_password": "x"}),
            ("post", "/api/v1/cash-counter/reopen/1", {"owner_password": "x"}),
            ("get", "/api/v1/cash-counter/today", None),
            ("get", "/api/v1/cash-counter/history", None),
            ("get", f"/api/v1/cash-counter/day/{TODAY.isoformat()}", None),
        ],
    )
    def test_route_rejects_anonymous(self, client, method, path, body):
        response = client.request(method.upper(), path, json=body)
        assert response.status_code == 401


class TestCashCounterAttribution:
    def test_open_records_the_real_username(self, client, auth_headers, test_db):
        response = client.post(
            "/api/v1/cash-counter/open", json=_open_payload(TODAY), headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["opened_by"] == "admin"

    def test_close_records_the_real_username(self, client, owner_headers, test_db):
        client.post(
            "/api/v1/cash-counter/open", json=_open_payload(TODAY), headers=owner_headers
        )
        response = client.post(
            "/api/v1/cash-counter/close", json=_close_payload(TODAY), headers=owner_headers
        )
        assert response.status_code == 200
        assert response.json()["closed_by"] == "owner"


class TestCashCounterDateWindow:
    def test_admin_cannot_open_a_previous_day(self, client, auth_headers):
        response = client.post(
            "/api/v1/cash-counter/open",
            json=_open_payload(YESTERDAY),
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_owner_can_open_a_previous_day(self, client, owner_headers):
        response = client.post(
            "/api/v1/cash-counter/open",
            json=_open_payload(YESTERDAY),
            headers=owner_headers,
        )
        assert response.status_code == 201

    def test_admin_cannot_close_a_previous_day(
        self, client, auth_headers, yesterdays_counter
    ):
        response = client.post(
            "/api/v1/cash-counter/close",
            json=_close_payload(YESTERDAY),
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_admin_cannot_look_up_a_previous_day(
        self, client, auth_headers, yesterdays_counter
    ):
        response = client.get(
            f"/api/v1/cash-counter/day/{YESTERDAY.isoformat()}", headers=auth_headers
        )
        assert response.status_code == 403

    def test_admin_can_look_up_today(self, client, auth_headers):
        response = client.get(
            f"/api/v1/cash-counter/day/{TODAY.isoformat()}", headers=auth_headers
        )
        assert response.status_code == 200

    def test_owner_can_look_up_a_previous_day(
        self, client, owner_headers, yesterdays_counter
    ):
        response = client.get(
            f"/api/v1/cash-counter/day/{YESTERDAY.isoformat()}", headers=owner_headers
        )
        assert response.status_code == 200

    def test_history_is_owner_only(self, client, auth_headers):
        response = client.get("/api/v1/cash-counter/history", headers=auth_headers)
        assert response.status_code == 403

    def test_owner_can_read_history(self, client, owner_headers, yesterdays_counter):
        response = client.get("/api/v1/cash-counter/history", headers=owner_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_admin_can_still_read_today(self, client, auth_headers):
        response = client.get("/api/v1/cash-counter/today", headers=auth_headers)
        assert response.status_code == 200


# ============================================================================
# Inventory
# ============================================================================


class TestInventoryRequiresLogin:
    """Every inventory route was previously reachable with no credentials."""

    @pytest.mark.parametrize(
        "method,path,body",
        [
            ("get", "/api/v1/inventory/categories", None),
            ("post", "/api/v1/inventory/categories", {"name": "New"}),
            ("patch", "/api/v1/inventory/categories/1", {"name": "New"}),
            ("delete", "/api/v1/inventory/categories/1", None),
            ("get", "/api/v1/inventory/items", None),
            ("get", "/api/v1/inventory/items/low-stock", None),
            ("get", "/api/v1/inventory/items/1", None),
            ("delete", "/api/v1/inventory/items/1", None),
            ("get", "/api/v1/inventory/transactions", None),
            (
                "post",
                "/api/v1/inventory/transactions/adjustment",
                {"item_id": 1, "new_quantity": 5, "notes": "count"},
            ),
        ],
    )
    def test_route_rejects_anonymous(self, client, method, path, body):
        response = client.request(method.upper(), path, json=body)
        assert response.status_code == 401


class TestInventoryMasterDataIsOwnerOnly:
    def test_admin_cannot_create_category(self, client, auth_headers):
        response = client.post(
            "/api/v1/inventory/categories", json={"name": "Spices"}, headers=auth_headers
        )
        assert response.status_code == 403

    def test_admin_cannot_update_category(
        self, client, auth_headers, inventory_category
    ):
        response = client.patch(
            f"/api/v1/inventory/categories/{inventory_category.id}",
            json={"name": "Renamed"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_admin_cannot_delete_category(
        self, client, auth_headers, inventory_category
    ):
        response = client.delete(
            f"/api/v1/inventory/categories/{inventory_category.id}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_admin_cannot_create_item(self, client, auth_headers, inventory_category):
        response = client.post(
            "/api/v1/inventory/items",
            json={
                "name": "Sugar",
                "category_id": inventory_category.id,
                "unit": "kg",
                "current_quantity": 0,
                "min_threshold": 1,
            },
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_admin_cannot_update_item(self, client, auth_headers, inventory_item):
        response = client.patch(
            f"/api/v1/inventory/items/{inventory_item.id}",
            json={"min_threshold": 99},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_admin_cannot_delete_item(self, client, auth_headers, inventory_item):
        response = client.delete(
            f"/api/v1/inventory/items/{inventory_item.id}", headers=auth_headers
        )
        assert response.status_code == 403

    def test_owner_can_create_category(self, client, owner_headers):
        response = client.post(
            "/api/v1/inventory/categories",
            json={"name": "Spices"},
            headers=owner_headers,
        )
        assert response.status_code == 201

    def test_owner_can_update_item(self, client, owner_headers, inventory_item):
        response = client.patch(
            f"/api/v1/inventory/items/{inventory_item.id}",
            json={"min_threshold": 99},
            headers=owner_headers,
        )
        assert response.status_code == 200


class TestInventoryDailyWorkStaysWithAdmin:
    """Counting stock and recording movements is the day's work, not master data."""

    def test_admin_can_read_categories(self, client, auth_headers, inventory_category):
        response = client.get("/api/v1/inventory/categories", headers=auth_headers)
        assert response.status_code == 200

    def test_admin_can_read_items(self, client, auth_headers, inventory_item):
        response = client.get("/api/v1/inventory/items", headers=auth_headers)
        assert response.status_code == 200

    def test_admin_can_read_low_stock(self, client, auth_headers, inventory_item):
        response = client.get("/api/v1/inventory/items/low-stock", headers=auth_headers)
        assert response.status_code == 200

    def test_admin_can_read_transactions(self, client, auth_headers):
        response = client.get("/api/v1/inventory/transactions", headers=auth_headers)
        assert response.status_code == 200

    def test_admin_can_record_an_adjustment(self, client, auth_headers, inventory_item):
        response = client.post(
            "/api/v1/inventory/transactions/adjustment",
            json={
                "item_id": inventory_item.id,
                "new_quantity": 8,
                "notes": "daily count",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    def test_admin_can_record_a_purchase(self, client, auth_headers, inventory_item):
        response = client.post(
            "/api/v1/inventory/transactions/purchase",
            json={"items": [{"item_id": inventory_item.id, "quantity": 5}]},
            headers=auth_headers,
        )
        assert response.status_code == 201
