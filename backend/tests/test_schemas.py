"""
Unit tests for Pydantic schemas.
Tests validation, serialization, and field constraints for all schemas.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app import schemas
from app.models.models import OrderStatus, PaymentMethod


class TestCategorySchemas:
    """Test Category schemas."""

    def test_category_create_valid(self):
        """Test creating a valid category."""
        category = schemas.CategoryCreate(name="Beverages")
        assert category.name == "Beverages"

    def test_category_create_empty_name(self):
        """Test creating category with empty name fails."""
        with pytest.raises(ValidationError) as exc_info:
            schemas.CategoryCreate(name="")

        errors = exc_info.value.errors()
        assert any("name" in str(error["loc"]) for error in errors)

    def test_category_create_too_long_name(self):
        """Test creating category with name exceeding max length."""
        long_name = "A" * 101  # Max is 100
        with pytest.raises(ValidationError):
            schemas.CategoryCreate(name=long_name)

    def test_category_response(self):
        """Test Category response schema."""
        now = datetime.utcnow()
        category = schemas.Category(id=1, name="Beverages", created_at=now)

        assert category.id == 1
        assert category.name == "Beverages"
        assert category.created_at == now


class TestMenuItemSchemas:
    """Test MenuItem schemas."""

    def test_menu_item_create_valid(self):
        """Test creating a valid menu item."""
        item = schemas.MenuItemCreate(
            name="Filter Coffee",
            description="South Indian filter coffee",
            price=4000,
            category_id=1,
        )

        assert item.name == "Filter Coffee"
        assert item.description == "South Indian filter coffee"
        assert item.price == 4000
        assert item.category_id == 1

    def test_menu_item_create_without_description(self):
        """Test creating menu item without optional description."""
        item = schemas.MenuItemCreate(name="Coffee", price=4000, category_id=1)

        assert item.name == "Coffee"
        assert item.description is None
        assert item.price == 4000

    def test_menu_item_create_zero_price(self):
        """Test creating menu item with zero price fails."""
        with pytest.raises(ValidationError) as exc_info:
            schemas.MenuItemCreate(name="Free Item", price=0, category_id=1)

        errors = exc_info.value.errors()
        assert any("price" in str(error["loc"]) for error in errors)

    def test_menu_item_create_negative_price(self):
        """Test creating menu item with negative price fails."""
        with pytest.raises(ValidationError):
            schemas.MenuItemCreate(name="Bad Item", price=-100, category_id=1)

    def test_menu_item_create_empty_name(self):
        """Test creating menu item with empty name fails."""
        with pytest.raises(ValidationError):
            schemas.MenuItemCreate(name="", price=1000, category_id=1)

    def test_menu_item_update_partial(self):
        """Test updating menu item with partial data."""
        update = schemas.MenuItemUpdate(price=5000)

        assert update.price == 5000
        assert update.name is None
        assert update.description is None
        assert update.category_id is None
        assert update.is_available is None

    def test_menu_item_update_all_fields(self):
        """Test updating menu item with all fields."""
        update = schemas.MenuItemUpdate(
            name="Updated Coffee",
            description="New description",
            price=5000,
            category_id=2,
            is_available=False,
        )

        assert update.name == "Updated Coffee"
        assert update.description == "New description"
        assert update.price == 5000
        assert update.category_id == 2
        assert update.is_available is False


class TestOrderItemSchemas:
    """Test OrderItem schemas."""

    def test_order_item_create_valid(self):
        """Test creating a valid order item."""
        item = schemas.OrderItemCreate(menu_item_id=1, quantity=2)

        assert item.menu_item_id == 1
        assert item.quantity == 2

    def test_order_item_create_zero_quantity(self):
        """Test creating order item with zero quantity fails."""
        with pytest.raises(ValidationError) as exc_info:
            schemas.OrderItemCreate(menu_item_id=1, quantity=0)

        errors = exc_info.value.errors()
        assert any("quantity" in str(error["loc"]) for error in errors)

    def test_order_item_create_negative_quantity(self):
        """Test creating order item with negative quantity fails."""
        with pytest.raises(ValidationError):
            schemas.OrderItemCreate(menu_item_id=1, quantity=-1)

    def test_order_item_response(self):
        """Test OrderItem response schema."""
        item = schemas.OrderItem(
            id=1,
            menu_item_id=10,
            menu_item_name="Filter Coffee",
            quantity=2,
            unit_price=4000,
            subtotal=8000,
        )

        assert item.id == 1
        assert item.menu_item_id == 10
        assert item.menu_item_name == "Filter Coffee"
        assert item.quantity == 2
        assert item.unit_price == 4000
        assert item.subtotal == 8000


class TestPaymentSchemas:
    """Test Payment schemas."""

    def test_payment_create_valid_upi(self):
        """Test creating a valid UPI payment."""
        payment = schemas.PaymentCreate(payment_method=PaymentMethod.UPI, amount=10000)

        assert payment.payment_method == PaymentMethod.UPI
        assert payment.amount == 10000

    def test_payment_create_valid_cash(self):
        """Test creating a valid cash payment."""
        payment = schemas.PaymentCreate(payment_method=PaymentMethod.CASH, amount=5000)

        assert payment.payment_method == PaymentMethod.CASH
        assert payment.amount == 5000

    def test_payment_create_valid_card(self):
        """Test creating a valid card payment."""
        payment = schemas.PaymentCreate(payment_method=PaymentMethod.CARD, amount=15000)

        assert payment.payment_method == PaymentMethod.CARD
        assert payment.amount == 15000

    def test_payment_create_zero_amount(self):
        """Test creating payment with zero amount fails."""
        with pytest.raises(ValidationError) as exc_info:
            schemas.PaymentCreate(payment_method=PaymentMethod.CASH, amount=0)

        errors = exc_info.value.errors()
        assert any("amount" in str(error["loc"]) for error in errors)

    def test_payment_create_negative_amount(self):
        """Test creating payment with negative amount fails."""
        with pytest.raises(ValidationError):
            schemas.PaymentCreate(payment_method=PaymentMethod.UPI, amount=-100)

    def test_payment_create_invalid_method(self):
        """Test creating payment with invalid method fails."""
        with pytest.raises(ValidationError):
            schemas.PaymentCreate(payment_method="bitcoin", amount=1000)


class TestOrderSchemas:
    """Test Order schemas."""

    def test_order_create_valid(self):
        """Test creating a valid order."""
        order = schemas.OrderCreate(
            table_number=5,
            customer_name="John Doe",
            items=[
                schemas.OrderItemCreate(menu_item_id=1, quantity=2),
                schemas.OrderItemCreate(menu_item_id=2, quantity=1),
            ],
        )

        assert order.table_number == 5
        assert order.customer_name == "John Doe"
        assert len(order.items) == 2

    def test_order_create_without_customer_name(self):
        """Test creating order without optional customer name."""
        order = schemas.OrderCreate(
            table_number=3,
            items=[schemas.OrderItemCreate(menu_item_id=1, quantity=1)],
        )

        assert order.table_number == 3
        assert order.customer_name is None
        assert len(order.items) == 1

    def test_order_create_empty_items(self):
        """Test creating order with no items fails."""
        with pytest.raises(ValidationError) as exc_info:
            schemas.OrderCreate(table_number=5, items=[])

        errors = exc_info.value.errors()
        assert any("items" in str(error["loc"]) for error in errors)

    def test_order_create_table_number_zero(self):
        """Test creating order with table number 0 fails."""
        with pytest.raises(ValidationError) as exc_info:
            schemas.OrderCreate(
                table_number=0,
                items=[schemas.OrderItemCreate(menu_item_id=1, quantity=1)],
            )

        errors = exc_info.value.errors()
        assert any("table_number" in str(error["loc"]) for error in errors)

    def test_order_create_table_number_too_high(self):
        """Test creating order with table number > 50 fails."""
        with pytest.raises(ValidationError):
            schemas.OrderCreate(
                table_number=51,
                items=[schemas.OrderItemCreate(menu_item_id=1, quantity=1)],
            )

    def test_order_update_status(self):
        """Test updating order status."""
        update = schemas.OrderUpdate(status=OrderStatus.PAID)

        assert update.status == OrderStatus.PAID
        assert update.customer_name is None

    def test_order_update_customer_name(self):
        """Test updating order customer name."""
        update = schemas.OrderUpdate(customer_name="Jane Smith")

        assert update.customer_name == "Jane Smith"
        assert update.status is None

    def test_order_summary(self):
        """Test OrderSummary schema."""
        now = datetime.utcnow()
        summary = schemas.OrderSummary(
            id=1,
            order_number="ORD-20241030-0001",
            table_number=5,
            customer_name="John",
            total_amount=23600,
            status=OrderStatus.ACTIVE,
            created_at=now,
            item_count=3,
        )

        assert summary.id == 1
        assert summary.order_number == "ORD-20241030-0001"
        assert summary.table_number == 5
        assert summary.total_amount == 23600
        assert summary.status == OrderStatus.ACTIVE
        assert summary.item_count == 3


class TestAuthenticationSchemas:
    """Test authentication schemas."""

    def test_login_request_valid(self):
        """Test valid login request."""
        login = schemas.LoginRequest(username="admin", password="secret123")

        assert login.username == "admin"
        assert login.password == "secret123"

    def test_login_request_missing_username(self):
        """Test login request with missing username fails."""
        with pytest.raises(ValidationError):
            schemas.LoginRequest(password="secret123")

    def test_login_request_missing_password(self):
        """Test login request with missing password fails."""
        with pytest.raises(ValidationError):
            schemas.LoginRequest(username="admin")

    def test_token_response(self):
        """Test token response schema."""
        token = schemas.Token(access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

        assert token.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert token.token_type == "bearer"

    def test_token_response_custom_type(self):
        """Test token response with custom token type."""
        token = schemas.Token(
            access_token="some.token.here", token_type="custom"
        )

        assert token.token_type == "custom"

    def test_token_data(self):
        """Test token data schema."""
        token_data = schemas.TokenData(username="admin")

        assert token_data.username == "admin"

    def test_token_data_optional_username(self):
        """Test token data with optional username."""
        token_data = schemas.TokenData()

        assert token_data.username is None


class TestSchemaValidationEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_menu_item_max_length_name(self):
        """Test menu item with maximum allowed name length."""
        max_name = "A" * 200
        item = schemas.MenuItemCreate(name=max_name, price=1000, category_id=1)

        assert len(item.name) == 200

    def test_menu_item_exceed_max_length_name(self):
        """Test menu item with name exceeding maximum length."""
        too_long = "A" * 201
        with pytest.raises(ValidationError):
            schemas.MenuItemCreate(name=too_long, price=1000, category_id=1)

    def test_menu_item_max_length_description(self):
        """Test menu item with maximum allowed description length."""
        max_desc = "A" * 500
        item = schemas.MenuItemCreate(
            name="Test", description=max_desc, price=1000, category_id=1
        )

        assert len(item.description) == 500

    def test_order_create_minimum_table_number(self):
        """Test order with minimum valid table number."""
        order = schemas.OrderCreate(
            table_number=1,
            items=[schemas.OrderItemCreate(menu_item_id=1, quantity=1)],
        )

        assert order.table_number == 1

    def test_order_create_maximum_table_number(self):
        """Test order with maximum valid table number."""
        order = schemas.OrderCreate(
            table_number=50,
            items=[schemas.OrderItemCreate(menu_item_id=1, quantity=1)],
        )

        assert order.table_number == 50

    def test_large_price_value(self):
        """Test menu item with very large price."""
        large_price = 1000000000  # ₹10,000,000 in paise
        item = schemas.MenuItemCreate(
            name="Expensive Item", price=large_price, category_id=1
        )

        assert item.price == large_price

    def test_large_quantity_value(self):
        """Test order item with large quantity."""
        large_quantity = 100
        item = schemas.OrderItemCreate(menu_item_id=1, quantity=large_quantity)

        assert item.quantity == large_quantity
