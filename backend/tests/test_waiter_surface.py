"""
The waiter screens run without a login.

/tables, /order/:table and /active-orders are not behind ProtectedRoute — a
waiter uses them on a phone with no credentials. Every endpoint those screens
call must therefore stay reachable anonymously.

This is a guard rail for future access-control work: tightening auth is good,
but tightening it here logs the whole floor staff out of the app, and the
failure only shows up on a phone in service. If a change makes one of these
fail, either keep the endpoint open or move that feature behind the admin UI.
"""

import pytest


@pytest.fixture
def active_order(client, sample_menu_items):
    response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 3,
            "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}],
        },
    )
    assert response.status_code == 201
    return response.json()


class TestWaiterScreensNeedNoLogin:
    def test_tables_page_lists_active_orders(self, client):
        """TablesPage + ActiveOrdersPage: useActiveOrders."""
        assert client.get("/api/v1/orders/active").status_code == 200

    def test_app_config_is_readable(self, client):
        """All three waiter screens: useAppConfig (GST rate, table count)."""
        assert client.get("/api/v1/config").status_code == 200

    def test_menu_is_readable(self, client, sample_menu_items):
        """OrderPage: useMenuItems."""
        response = client.get("/api/v1/menu")
        assert response.status_code == 200
        assert len(response.json()) > 0

    def test_categories_are_readable(self, client, sample_categories):
        """OrderPage: useCategories."""
        assert client.get("/api/v1/categories").status_code == 200

    def test_an_order_can_be_placed(self, client, sample_menu_items):
        """OrderPage: useCreateOrUpdateOrder — the core waiter action."""
        response = client.post(
            "/api/v1/orders",
            json={
                "table_number": 4,
                "notes": "No onion",
                "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 2}],
            },
        )
        assert response.status_code == 201
        assert response.json()["notes"] == "No onion"

    def test_a_table_can_be_checked_for_an_active_order(self, client, active_order):
        """OrderPage: check whether the table already has an open order."""
        response = client.get("/api/v1/orders/table/3/active")
        assert response.status_code == 200

    def test_an_active_order_can_be_opened(self, client, active_order):
        """ActiveOrdersPage: useOrder for the details modal."""
        response = client.get(f"/api/v1/orders/{active_order['id']}")
        assert response.status_code == 200


class TestWaiterScreensCannotChangeOrders:
    """Reading is open; changing an order is not, and the UI must not offer it."""

    def test_editing_an_order_needs_a_login(self, client, active_order):
        response = client.put(
            f"/api/v1/orders/{active_order['id']}",
            json={
                "customer_name": "Rahul",
                "items": [{"menu_item_id": 1, "quantity": 1}],
            },
        )
        assert response.status_code == 401

    def test_changing_order_metadata_needs_a_login(self, client, active_order):
        response = client.patch(
            f"/api/v1/orders/{active_order['id']}", json={"customer_name": "Rahul"}
        )
        assert response.status_code == 401

    def test_canceling_an_order_needs_a_login(self, client, active_order):
        response = client.delete(f"/api/v1/orders/{active_order['id']}")
        assert response.status_code == 401
