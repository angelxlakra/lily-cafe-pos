"""
Tests for the admin vs owner access rules.

The reception ("admin") login runs the day: it can take orders, bill them and
print receipts, but it is confined to the current day and cannot retroactively
change a bill or touch the menu. The owner login has no such limits.
"""

from datetime import date, datetime, timedelta

import pytest

from app.core import business_time
from app.models import models


# ============================================================================
# Helpers
# ============================================================================


def _make_order(db, *, order_date: date, status=models.OrderStatus.PAID, seq=1):
    """Create an order stamped with a given business date."""
    order = models.Order(
        order_number=f"ORD-{order_date.strftime('%Y%m%d')}-{seq:04d}",
        table_number=4,
        customer_name="History Customer",
        subtotal=10000,
        gst_amount=500,
        total_amount=10500,
        status=status,
        created_at=datetime.combine(order_date, datetime.min.time()),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@pytest.fixture
def yesterdays_order(test_db):
    return _make_order(test_db, order_date=business_time.business_today() - timedelta(days=1))


@pytest.fixture
def todays_paid_order(test_db):
    return _make_order(test_db, order_date=business_time.business_today(), seq=2)


# ============================================================================
# Order history date window
# ============================================================================


class TestOrderHistoryDateWindow:
    """Admin sees today only; owner sees any day."""

    def test_history_requires_authentication(self, client):
        response = client.get("/api/v1/orders/history")
        assert response.status_code == 401

    def test_admin_history_defaults_to_today(self, client, auth_headers):
        response = client.get("/api/v1/orders/history", headers=auth_headers)
        assert response.status_code == 200

    def test_admin_can_request_today(self, client, auth_headers):
        today = date.today().isoformat()
        response = client.get(
            f"/api/v1/orders/history?start_date={today}&end_date={today}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_admin_cannot_request_previous_day(self, client, auth_headers):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        response = client.get(
            f"/api/v1/orders/history?start_date={yesterday}&end_date={yesterday}",
            headers=auth_headers,
        )
        assert response.status_code == 403
        assert "Owner login required" in response.json()["detail"]

    def test_admin_cannot_request_range_spanning_previous_days(self, client, auth_headers):
        start = (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()
        response = client.get(
            f"/api/v1/orders/history?start_date={start}&end_date={end}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_admin_cannot_use_legacy_date_param_for_past(self, client, auth_headers):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        response = client.get(
            f"/api/v1/orders/history?date={yesterday}", headers=auth_headers
        )
        assert response.status_code == 403

    def test_admin_history_excludes_previous_days(
        self, client, auth_headers, yesterdays_order, todays_paid_order
    ):
        response = client.get("/api/v1/orders/history", headers=auth_headers)
        assert response.status_code == 200
        order_numbers = [item["order_number"] for item in response.json()["items"]]
        assert todays_paid_order.order_number in order_numbers
        assert yesterdays_order.order_number not in order_numbers

    def test_owner_can_read_previous_days(
        self, client, owner_headers, yesterdays_order
    ):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        response = client.get(
            f"/api/v1/orders/history?start_date={yesterday}&end_date={yesterday}",
            headers=owner_headers,
        )
        assert response.status_code == 200
        order_numbers = [item["order_number"] for item in response.json()["items"]]
        assert yesterdays_order.order_number in order_numbers


class TestSingleOrderVisibility:
    """A past order cannot be reached one-by-one either."""

    def test_admin_cannot_read_previous_day_order(
        self, client, auth_headers, yesterdays_order
    ):
        response = client.get(
            f"/api/v1/orders/{yesterdays_order.id}", headers=auth_headers
        )
        assert response.status_code == 403

    def test_owner_can_read_previous_day_order(
        self, client, owner_headers, yesterdays_order
    ):
        response = client.get(
            f"/api/v1/orders/{yesterdays_order.id}", headers=owner_headers
        )
        assert response.status_code == 200

    def test_billed_order_requires_login(self, client, todays_paid_order):
        response = client.get(f"/api/v1/orders/{todays_paid_order.id}")
        assert response.status_code == 401

    def test_active_order_stays_public_for_waiters(self, client, sample_order):
        """Waiter screens have no login, so active orders stay readable."""
        response = client.get(f"/api/v1/orders/{sample_order.id}")
        assert response.status_code == 200


# ============================================================================
# Menu and category modifications
# ============================================================================


class TestMenuIsOwnerOnly:
    def test_admin_cannot_create_menu_item(self, client, auth_headers, sample_categories):
        response = client.post(
            "/api/v1/menu",
            json={"name": "New Item", "price": 5000, "category_id": sample_categories[0].id},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_admin_cannot_update_menu_item(self, client, auth_headers, sample_menu_items):
        response = client.patch(
            f"/api/v1/menu/{sample_menu_items[0].id}",
            json={"price": 9900},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_admin_cannot_delete_menu_item(self, client, auth_headers, sample_menu_items):
        response = client.delete(
            f"/api/v1/menu/{sample_menu_items[0].id}", headers=auth_headers
        )
        assert response.status_code == 403

    def test_admin_cannot_create_category(self, client, auth_headers):
        response = client.post(
            "/api/v1/categories", json={"name": "Desserts 2"}, headers=auth_headers
        )
        assert response.status_code == 403

    def test_admin_can_still_read_the_menu(self, client, auth_headers, sample_menu_items):
        response = client.get("/api/v1/menu", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) > 0

    def test_owner_can_modify_menu(self, client, owner_headers, sample_menu_items):
        response = client.patch(
            f"/api/v1/menu/{sample_menu_items[0].id}",
            json={"price": 9900},
            headers=owner_headers,
        )
        assert response.status_code == 200
        assert response.json()["price"] == 9900


# ============================================================================
# Corrections after the bill is generated
# ============================================================================


class TestPostBillCorrections:
    def test_admin_can_edit_an_open_order(
        self, client, auth_headers, sample_order, sample_menu_items
    ):
        response = client.put(
            f"/api/v1/orders/{sample_order.id}",
            json={"items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 3}]},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_admin_cannot_edit_a_billed_order(
        self, client, auth_headers, todays_paid_order, sample_menu_items
    ):
        response = client.put(
            f"/api/v1/orders/{todays_paid_order.id}",
            json={"items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 3}]},
            headers=auth_headers,
        )
        assert response.status_code == 403
        assert "Owner login required" in response.json()["detail"]

    def test_owner_can_edit_a_billed_order(
        self, client, owner_headers, todays_paid_order, sample_menu_items
    ):
        response = client.put(
            f"/api/v1/orders/{todays_paid_order.id}",
            json={"items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 3}]},
            headers=owner_headers,
        )
        assert response.status_code == 200
        assert response.json()["last_edited_by"] == "owner"
        assert response.json()["edit_count"] == 1

    def test_admin_can_change_the_payment_split_on_a_billed_order(
        self, client, auth_headers, test_db, todays_paid_order
    ):
        """
        The customer says UPI, the bill prints, then they pay half in cash.
        Reception handles that at the counter, so it is not owner-only.
        """
        half = todays_paid_order.total_amount // 2
        response = client.put(
            f"/api/v1/orders/{todays_paid_order.id}/payments",
            json={
                "payments": [
                    {"payment_method": "cash", "amount": half},
                    {
                        "payment_method": "upi",
                        "amount": todays_paid_order.total_amount - half,
                    },
                ]
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(response.json()) == 2

        test_db.refresh(todays_paid_order)
        assert todays_paid_order.last_edited_by == "admin"

    def test_changing_the_split_cannot_change_the_amount(
        self, client, auth_headers, todays_paid_order
    ):
        """The guard that keeps this from being a way to move money."""
        response = client.put(
            f"/api/v1/orders/{todays_paid_order.id}/payments",
            json={
                "payments": [
                    {"payment_method": "cash", "amount": todays_paid_order.total_amount - 5000}
                ]
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "does not match" in response.json()["detail"]

    def test_admin_cannot_change_payments_on_a_previous_day(
        self, client, auth_headers, yesterdays_order
    ):
        response = client.put(
            f"/api/v1/orders/{yesterdays_order.id}/payments",
            json={"payments": [{"payment_method": "cash", "amount": yesterdays_order.total_amount}]},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_owner_can_change_payments_on_a_billed_order(
        self, client, owner_headers, test_db, todays_paid_order
    ):
        response = client.put(
            f"/api/v1/orders/{todays_paid_order.id}/payments",
            json={"payments": [{"payment_method": "cash", "amount": todays_paid_order.total_amount}]},
            headers=owner_headers,
        )
        assert response.status_code == 200

        test_db.refresh(todays_paid_order)
        assert todays_paid_order.last_edited_by == "owner"

    def test_admin_cannot_patch_status_of_a_billed_order(
        self, client, auth_headers, todays_paid_order
    ):
        response = client.patch(
            f"/api/v1/orders/{todays_paid_order.id}",
            json={"status": "active"},
            headers=auth_headers,
        )
        assert response.status_code == 403


# ============================================================================
# Cancellations stay visible
# ============================================================================


class TestCancellationAuditTrail:
    def test_cancel_records_who_and_when(self, client, auth_headers, test_db, sample_order):
        response = client.request(
            "DELETE",
            f"/api/v1/orders/{sample_order.id}",
            json={"reason": "Duplicate order"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        test_db.refresh(sample_order)
        assert sample_order.status == models.OrderStatus.CANCELED
        assert sample_order.canceled_by == "admin"
        assert sample_order.cancel_reason == "Duplicate order"
        assert sample_order.canceled_at is not None

    def test_cancel_works_without_a_reason(self, client, auth_headers, test_db, sample_order):
        response = client.delete(
            f"/api/v1/orders/{sample_order.id}", headers=auth_headers
        )
        assert response.status_code == 200

        test_db.refresh(sample_order)
        assert sample_order.canceled_by == "admin"
        assert sample_order.cancel_reason is None

    def test_canceled_order_stays_in_history_with_audit_fields(
        self, client, auth_headers, frozen_clock, sample_order
    ):
        client.request(
            "DELETE",
            f"/api/v1/orders/{sample_order.id}",
            json={"reason": "Wrong table"},
            headers=auth_headers,
        )

        response = client.get("/api/v1/orders/history", headers=auth_headers)
        assert response.status_code == 200

        canceled = [
            item for item in response.json()["items"]
            if item["order_number"] == sample_order.order_number
        ]
        assert len(canceled) == 1
        assert canceled[0]["status"] == "canceled"
        assert canceled[0]["canceled_by"] == "admin"
        assert canceled[0]["cancel_reason"] == "Wrong table"

    def test_admin_cannot_void_a_billed_order(self, client, auth_headers, todays_paid_order):
        response = client.delete(
            f"/api/v1/orders/{todays_paid_order.id}", headers=auth_headers
        )
        assert response.status_code == 403

    def test_owner_can_void_a_billed_order(
        self, client, owner_headers, test_db, todays_paid_order
    ):
        response = client.delete(
            f"/api/v1/orders/{todays_paid_order.id}", headers=owner_headers
        )
        assert response.status_code == 200

        test_db.refresh(todays_paid_order)
        assert todays_paid_order.status == models.OrderStatus.CANCELED
        assert todays_paid_order.canceled_by == "owner"


# ============================================================================
# Reports must not become a back door to past-day data
# ============================================================================


class TestDishFrequencyDateWindow:
    def test_admin_cannot_request_past_range(self, client, auth_headers):
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = client.get(
            f"/api/v1/analytics/dish-frequency?start_date={start}&end_date={end}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_admin_gets_today_when_no_range_given(self, client, auth_headers):
        response = client.get(
            "/api/v1/analytics/dish-frequency", headers=auth_headers
        )
        assert response.status_code == 200

    def test_owner_can_request_past_range(self, client, owner_headers):
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = client.get(
            f"/api/v1/analytics/dish-frequency?start_date={start}&end_date={end}",
            headers=owner_headers,
        )
        assert response.status_code == 200
