"""
Integration tests for order management API endpoints.

Tests cover:
- POST /api/orders (smart creation/update)
- GET /api/orders/active
- GET /api/orders/{order_id}
- PUT /api/orders/{order_id} (admin edit)
- DELETE /api/orders/{order_id} (cancel)
- PATCH /api/orders/{order_id} (update status)
- GET /api/orders/table/{table_number}/active
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import OrderStatus


# ============================================================================
# Test POST /api/orders - Smart Order Creation
# ============================================================================


def test_create_new_order_api(client: TestClient, sample_menu_items):
    """Test creating a new order via API."""
    response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 5,
            "customer_name": "John Doe",
            "items": [
                {"menu_item_id": sample_menu_items[0].id, "quantity": 2},
                {"menu_item_id": sample_menu_items[1].id, "quantity": 1},
            ]
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["table_number"] == 5
    assert data["customer_name"] == "John Doe"
    assert data["status"] == "active"
    assert len(data["order_items"]) == 2


def test_update_existing_order_api(client: TestClient, sample_menu_items):
    """Test that posting to same table updates the order."""
    # Create first order
    response1 = client.post(
        "/api/v1/orders",
        json={
            "table_number": 5,
            "items": [
                {"menu_item_id": sample_menu_items[0].id, "quantity": 1},
            ]
        }
    )
    assert response1.status_code == 201
    order1_id = response1.json()["id"]

    # Post to same table (should update)
    response2 = client.post(
        "/api/v1/orders",
        json={
            "table_number": 5,
            "items": [
                {"menu_item_id": sample_menu_items[0].id, "quantity": 2},
                {"menu_item_id": sample_menu_items[1].id, "quantity": 1},
            ]
        }
    )

    assert response2.status_code == 201
    data = response2.json()
    assert data["id"] == order1_id  # Same order
    assert len(data["order_items"]) == 2


def test_create_order_invalid_menu_item(client: TestClient):
    """Test creating order with invalid menu item returns 400."""
    response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 1,
            "items": [
                {"menu_item_id": 99999, "quantity": 1},
            ]
        }
    )

    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_create_order_validates_quantity(client: TestClient, sample_menu_items):
    """Test that quantity must be positive."""
    response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 1,
            "items": [
                {"menu_item_id": sample_menu_items[0].id, "quantity": 0},
            ]
        }
    )

    assert response.status_code == 422  # Validation error


def test_create_order_validates_table_number(client: TestClient, sample_menu_items):
    """Test that table number must be in valid range."""
    response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 0,  # Invalid
            "items": [
                {"menu_item_id": sample_menu_items[0].id, "quantity": 1},
            ]
        }
    )

    assert response.status_code == 422  # Validation error


# ============================================================================
# Test GET /api/orders/active
# ============================================================================


def test_get_active_orders_empty(client: TestClient):
    """Test getting active orders when none exist."""
    response = client.get("/api/v1/orders/active")

    assert response.status_code == 200
    assert response.json() == []


def test_get_active_orders_list(client: TestClient, sample_menu_items):
    """Test getting list of active orders."""
    # Create 3 active orders
    for table_num in [1, 2, 3]:
        client.post(
            "/api/v1/orders",
            json={
                "table_number": table_num,
                "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
            }
        )

    response = client.get("/api/v1/orders/active")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(order["status"] == "active" for order in data)


def test_active_orders_excludes_paid(client: TestClient, sample_menu_items, db: Session):
    """Test that active orders endpoint excludes paid orders."""
    # Create active order
    response1 = client.post(
        "/api/v1/orders",
        json={
            "table_number": 1,
            "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
        }
    )
    active_order_id = response1.json()["id"]

    # Create and mark another as paid
    response2 = client.post(
        "/api/v1/orders",
        json={
            "table_number": 2,
            "items": [{"menu_item_id": sample_menu_items[1].id, "quantity": 1}]
        }
    )

    # Update to paid status
    from app import crud
    from app.models.models import Order
    paid_order = db.query(Order).filter(Order.id == response2.json()["id"]).first()
    paid_order.status = OrderStatus.PAID
    db.commit()

    # Get active orders
    response = client.get("/api/v1/orders/active")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == active_order_id


# ============================================================================
# Test GET /api/orders/{order_id}
# ============================================================================


def test_get_order_by_id(client: TestClient, sample_menu_items):
    """Test getting single order by ID."""
    # Create order
    create_response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 5,
            "customer_name": "Jane Doe",
            "items": [
                {"menu_item_id": sample_menu_items[0].id, "quantity": 2},
            ]
        }
    )
    order_id = create_response.json()["id"]

    # Get order
    response = client.get(f"/api/v1/orders/{order_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id
    assert data["table_number"] == 5
    assert data["customer_name"] == "Jane Doe"
    assert len(data["order_items"]) == 1
    assert "subtotal" in data
    assert "gst_amount" in data
    assert "total_amount" in data


def test_get_order_not_found(client: TestClient):
    """Test getting non-existent order returns 404."""
    response = client.get("/api/v1/orders/99999")

    assert response.status_code == 404


# ============================================================================
# Test GET /api/orders/table/{table_number}/active
# ============================================================================


def test_get_active_order_for_table(client: TestClient, sample_menu_items):
    """Test getting active order for a specific table."""
    # Create order for table 5
    client.post(
        "/api/v1/orders",
        json={
            "table_number": 5,
            "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
        }
    )

    # Get active order for table 5
    response = client.get("/api/v1/orders/table/5/active")

    assert response.status_code == 200
    data = response.json()
    assert data["table_number"] == 5
    assert data["status"] == "active"


def test_get_active_order_for_empty_table(client: TestClient):
    """Test getting active order for empty table returns null."""
    response = client.get("/api/v1/orders/table/10/active")

    assert response.status_code == 200
    assert response.json() is None


# ============================================================================
# Test PATCH /api/orders/{order_id} - Update Status
# ============================================================================


def test_update_order_status(client: TestClient, sample_menu_items):
    """Test updating order status via PATCH."""
    # Create order
    create_response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 1,
            "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
        }
    )
    order_id = create_response.json()["id"]

    # Update customer name
    response = client.patch(
        f"/api/v1/orders/{order_id}",
        json={"customer_name": "Updated Name"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["customer_name"] == "Updated Name"


def test_update_order_not_found(client: TestClient):
    """Test updating non-existent order returns 404."""
    response = client.patch(
        "/api/v1/orders/99999",
        json={"status": "canceled"}
    )

    assert response.status_code == 404


# ============================================================================
# Test PUT /api/orders/{order_id} - Admin Edit (requires auth)
# ============================================================================


@pytest.mark.skip(reason="Requires auth implementation")
def test_admin_edit_order_items(client: TestClient, sample_menu_items, auth_headers):
    """Test admin editing order items."""
    # Create order
    create_response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 1,
            "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
        }
    )
    order_id = create_response.json()["id"]

    # Admin edits order
    response = client.put(
        f"/api/v1/orders/{order_id}",
        headers=auth_headers,
        json={
            "items": [
                {"menu_item_id": sample_menu_items[1].id, "quantity": 2},
                {"menu_item_id": sample_menu_items[2].id, "quantity": 1},
            ]
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["order_items"]) == 2


@pytest.mark.skip(reason="Requires auth implementation")
def test_admin_edit_requires_auth(client: TestClient, sample_menu_items):
    """Test that admin edit requires authentication."""
    # Create order
    create_response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 1,
            "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
        }
    )
    order_id = create_response.json()["id"]

    # Try to edit without auth
    response = client.put(
        f"/api/v1/orders/{order_id}",
        json={
            "items": [{"menu_item_id": sample_menu_items[1].id, "quantity": 1}]
        }
    )

    assert response.status_code == 401  # Unauthorized


# ============================================================================
# Test DELETE /api/orders/{order_id} - Cancel Order (requires auth)
# ============================================================================


@pytest.mark.skip(reason="Requires auth implementation")
def test_cancel_order(client: TestClient, sample_menu_items, auth_headers):
    """Test canceling an order."""
    # Create order
    create_response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 1,
            "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
        }
    )
    order_id = create_response.json()["id"]

    # Cancel order
    response = client.delete(
        f"/api/v1/orders/{order_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["order_id"] == order_id

    # Verify order is canceled
    get_response = client.get(f"/api/v1/orders/{order_id}")
    assert get_response.json()["status"] == "canceled"


@pytest.mark.skip(reason="Requires auth implementation")
def test_cancel_order_requires_auth(client: TestClient, sample_menu_items):
    """Test that canceling order requires authentication."""
    # Create order
    create_response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 1,
            "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
        }
    )
    order_id = create_response.json()["id"]

    # Try to cancel without auth
    response = client.delete(f"/api/v1/orders/{order_id}")

    assert response.status_code == 401  # Unauthorized


@pytest.mark.skip(reason="Requires auth implementation")
def test_cannot_cancel_paid_order_api(client: TestClient, sample_menu_items, auth_headers, db: Session):
    """Test that paid orders cannot be canceled."""
    # Create order
    create_response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 1,
            "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
        }
    )
    order_id = create_response.json()["id"]

    # Mark as paid
    from app.models.models import Order
    order = db.query(Order).filter(Order.id == order_id).first()
    order.status = OrderStatus.PAID
    db.commit()

    # Try to cancel
    response = client.delete(
        f"/api/v1/orders/{order_id}",
        headers=auth_headers
    )

    assert response.status_code == 400
    assert "Cannot cancel a paid order" in response.json()["detail"]


# ============================================================================
# Test Order Filtering
# ============================================================================


def test_list_orders_filter_by_status(client: TestClient, sample_menu_items, db: Session):
    """Test filtering orders by status."""
    # Create multiple orders
    for i in range(3):
        client.post(
            "/api/v1/orders",
            json={
                "table_number": i + 1,
                "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
            }
        )

    # Mark one as paid
    from app.models.models import Order
    orders = db.query(Order).all()
    orders[0].status = OrderStatus.PAID
    db.commit()

    # Filter by active
    response = client.get("/api/v1/orders?status=active")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # Filter by paid
    response = client.get("/api/v1/orders?status=paid")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_orders_filter_by_table(client: TestClient, sample_menu_items):
    """Test filtering orders by table number."""
    # Create orders on different tables
    for table_num in [1, 2, 3]:
        client.post(
            "/api/v1/orders",
            json={
                "table_number": table_num,
                "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
            }
        )

    # Filter by table 2
    response = client.get("/api/v1/orders?table_number=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["table_number"] == 2


# ============================================================================
# Test GST in API Responses
# ============================================================================


def test_order_response_includes_gst_breakdown(client: TestClient, sample_menu_items):
    """Test that order response includes GST breakdown."""
    response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 1,
            "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "subtotal" in data
    assert "gst_amount" in data
    assert "total_amount" in data

    # Verify calculation: ₹80 (8000 paise)
    assert data["subtotal"] == 8000
    assert data["gst_amount"] == 400  # 5% of 8000
    assert data["total_amount"] == 8400  # 8000 + 400


def test_order_items_include_snapshots(client: TestClient, sample_menu_items):
    """Test that order items include snapshotted data."""
    response = client.post(
        "/api/v1/orders",
        json={
            "table_number": 1,
            "items": [{"menu_item_id": sample_menu_items[0].id, "quantity": 2}]
        }
    )

    assert response.status_code == 201
    data = response.json()
    order_item = data["order_items"][0]

    assert "menu_item_name" in order_item
    assert "unit_price" in order_item
    assert "subtotal" in order_item
    assert order_item["menu_item_name"] == "Masala Dosa"
    assert order_item["unit_price"] == 8000
    assert order_item["subtotal"] == 16000  # 2 * 8000
