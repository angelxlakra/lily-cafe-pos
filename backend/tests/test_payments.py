"""
Tests for payment processing functionality.
"""

import pytest
from app.models.models import OrderStatus, PaymentMethod


def test_create_single_payment(client, test_db, sample_order):
    """Test creating a single payment for an order."""
    # Create a test order first
    # ... (you'll need to set this up based on your existing test fixtures)

    response = client.post(
        f"/api/v1/orders/{sample_order.id}/payments",
        json={
            "payment_method": "cash",
            "amount": sample_order.total_amount
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["payment_method"] == "cash"
    assert data["amount"] == sample_order.total_amount


def test_create_split_payments(client, test_db, sample_order, auth_token):
    """Test creating multiple payments at once (split payment)."""
    # Calculate split amounts
    half = sample_order.total_amount // 2
    remainder = sample_order.total_amount - half

    response = client.post(
        f"/api/v1/orders/{sample_order.id}/payments/batch",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "payments": [
                {"payment_method": "upi", "amount": half},
                {"payment_method": "cash", "amount": remainder}
            ]
        }
    )

    assert response.status_code == 201
    payments = response.json()
    assert len(payments) == 2
    assert sum(p["amount"] for p in payments) == sample_order.total_amount

    # Verify order is marked as paid
    order_response = client.get(f"/api/v1/orders/{sample_order.id}")
    assert order_response.json()["status"] == "paid"


def test_split_payment_wrong_total(client, test_db, sample_order, auth_token):
    """Test that split payments fail if total doesn't match order total."""
    response = client.post(
        f"/api/v1/orders/{sample_order.id}/payments/batch",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "payments": [
                {"payment_method": "upi", "amount": 10000},  # Wrong total
                {"payment_method": "cash", "amount": 5000}
            ]
        }
    )

    assert response.status_code == 400
    assert "does not match order total" in response.json()["detail"]


def test_cannot_pay_already_paid_order(client, test_db, paid_order, auth_token):
    """Test that you cannot add payments to already paid orders."""
    response = client.post(
        f"/api/v1/orders/{paid_order.id}/payments/batch",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "payments": [
                {"payment_method": "cash", "amount": 1000}
            ]
        }
    )

    assert response.status_code == 400
    assert "already paid" in response.json()["detail"].lower()


def test_generate_receipt_for_paid_order(client, test_db, paid_order):
    """Test generating PDF receipt for a paid order."""
    response = client.get(f"/api/v1/orders/{paid_order.id}/receipt")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert b"PDF" in response.content[:10]  # PDF files start with %PDF


def test_cannot_generate_receipt_for_unpaid_order(client, test_db, sample_order):
    """Test that receipt generation fails for unpaid orders."""
    response = client.get(f"/api/v1/orders/{sample_order.id}/receipt")

    assert response.status_code == 400
    assert "unpaid" in response.json()["detail"].lower()