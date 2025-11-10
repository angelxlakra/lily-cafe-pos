"""
Unit tests for order management functionality.

Tests cover:
- Order number generation (daily sequential counter)
- Smart order creation/update (upsert behavior)
- GST calculations (18%)
- Order item snapshots
- Active order listing
- Admin order editing
- Order cancellation
- Edge cases and error handling
"""

import pytest
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.session import Base
from app.models.models import Order, OrderItem, MenuItem, Category, OrderStatus, PaymentMethod
from app.schemas.schemas import OrderCreate, OrderItemCreate, OrderItemsUpdate
from app import crud
from app.core.config import settings


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Session:
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_category(db: Session) -> Category:
    """Create a sample category."""
    category = Category(name="Test Category")
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def sample_menu_items(db: Session, sample_category: Category) -> list[MenuItem]:
    """Create sample menu items."""
    items = [
        MenuItem(
            name="Masala Dosa",
            description="Crispy dosa with potato filling",
            price=8000,  # ₹80 in paise
            category_id=sample_category.id,
            is_available=True,
        ),
        MenuItem(
            name="Filter Coffee",
            description="South Indian filter coffee",
            price=4000,  # ₹40 in paise
            category_id=sample_category.id,
            is_available=True,
        ),
        MenuItem(
            name="Idli (2 pcs)",
            description="Steamed rice cakes",
            price=5000,  # ₹50 in paise
            category_id=sample_category.id,
            is_available=True,
        ),
    ]
    for item in items:
        db.add(item)
    db.commit()
    for item in items:
        db.refresh(item)
    return items


# ============================================================================
# Test Order Number Generation
# ============================================================================


def test_order_number_generation_first_order(db: Session):
    """Test that first order of the day gets number 0001."""
    order_number = crud.generate_order_number(db)
    today_str = date.today().strftime("%Y%m%d")
    assert order_number == f"ORD-{today_str}-0001"


def test_order_number_generation_sequential(db: Session, sample_menu_items):
    """Test that order numbers increment sequentially."""
    # Create first order
    order1_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order1, _ = crud.create_order(db, order1_data)

    # Create second order at different table
    order2_data = OrderCreate(
        table_number=2,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=1)]
    )
    order2, _ = crud.create_order(db, order2_data)

    today_str = date.today().strftime("%Y%m%d")
    assert order1.order_number == f"ORD-{today_str}-0001"
    assert order2.order_number == f"ORD-{today_str}-0002"


def test_order_number_generation_daily_reset(db: Session, sample_menu_items):
    """Test that order numbers reset daily."""
    # Create an order with yesterday's date
    yesterday = date.today() - timedelta(days=1)
    yesterday_order = Order(
        order_number=f"ORD-{yesterday.strftime('%Y%m%d')}-0005",
        table_number=1,
        subtotal=8000,
        gst_amount=1440,
        total_amount=9440,
        status=OrderStatus.ACTIVE,
        created_at=datetime.combine(yesterday, datetime.min.time()),
    )
    db.add(yesterday_order)
    db.commit()

    # Generate new order number for today
    order_number = crud.generate_order_number(db)
    today_str = date.today().strftime("%Y%m%d")
    assert order_number == f"ORD-{today_str}-0001"


# ============================================================================
# Test Smart Order Creation (Upsert Logic)
# ============================================================================


def test_create_order_new_table(db: Session, sample_menu_items):
    """Test creating a new order on an empty table."""
    order_data = OrderCreate(
        table_number=5,
        customer_name="John Doe",
        items=[
            OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=2),
            OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=1),
        ]
    )

    order, _ = crud.create_order(db, order_data)

    assert order.table_number == 5
    assert order.customer_name == "John Doe"
    assert order.status == OrderStatus.ACTIVE
    assert len(order.order_items) == 2
    assert order.order_items[0].quantity == 2
    assert order.order_items[1].quantity == 1


def test_create_order_updates_existing(db: Session, sample_menu_items):
    """Test that creating order on table with active order updates it."""
    # Create first order
    order_data_1 = OrderCreate(
        table_number=5,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order1, _ = crud.create_order(db, order_data_1)
    original_order_id = order1.id
    original_order_number = order1.order_number

    # Create "new" order on same table (should update)
    order_data_2 = OrderCreate(
        table_number=5,
        items=[
            OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=2),
            OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=1),
        ]
    )
    order2, _ = crud.create_order(db, order_data_2)

    # Should be same order, updated
    assert order2.id == original_order_id
    assert order2.order_number == original_order_number
    assert len(order2.order_items) == 2
    assert order2.order_items[0].quantity == 2


def test_create_order_replaces_items_completely(db: Session, sample_menu_items):
    """Test that updating an order replaces items (doesn't merge)."""
    # Create order with Dosa
    order_data_1 = OrderCreate(
        table_number=5,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=2)]
    )
    order1, _ = crud.create_order(db, order_data_1)

    # Update with Coffee only
    order_data_2 = OrderCreate(
        table_number=5,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=1)]
    )
    order2, _ = crud.create_order(db, order_data_2)

    # Should only have Coffee now, not Dosa
    assert len(order2.order_items) == 1
    assert order2.order_items[0].menu_item_id == sample_menu_items[1].id


# ============================================================================
# Test GST Calculations
# ============================================================================


def test_gst_calculation_18_percent(db: Session, sample_menu_items):
    """Test that GST is calculated correctly at 18%."""
    order_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    # Masala Dosa: ₹80 (8000 paise)
    # GST 18%: 8000 * 0.18 = 1440 paise
    # Total: 8000 + 1440 = 9440 paise
    assert order.subtotal == 8000
    assert order.gst_amount == 1440
    assert order.total_amount == 9440


def test_gst_calculation_multiple_items(db: Session, sample_menu_items):
    """Test GST calculation with multiple items."""
    order_data = OrderCreate(
        table_number=1,
        items=[
            OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=2),  # 2 * 8000 = 16000
            OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=3),  # 3 * 4000 = 12000
        ]
    )
    order, _ = crud.create_order(db, order_data)

    # Subtotal: 16000 + 12000 = 28000
    # GST 18%: 28000 * 0.18 = 5040
    # Total: 28000 + 5040 = 33040
    assert order.subtotal == 28000
    assert order.gst_amount == 5040
    assert order.total_amount == 33040


def test_gst_recalculated_on_update(db: Session, sample_menu_items):
    """Test that GST is recalculated when order is updated."""
    # Create initial order
    order_data_1 = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order1, _ = crud.create_order(db, order_data_1)
    initial_gst = order1.gst_amount

    # Update order with more items
    order_data_2 = OrderCreate(
        table_number=1,
        items=[
            OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=2),
            OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=1),
        ]
    )
    order2, _ = crud.create_order(db, order_data_2)

    # GST should be recalculated
    # New subtotal: (2 * 8000) + (1 * 4000) = 20000
    # New GST: 20000 * 0.18 = 3600
    assert order2.gst_amount == 3600
    assert order2.gst_amount != initial_gst


# ============================================================================
# Test Order Item Snapshots
# ============================================================================


def test_order_item_snapshots_price(db: Session, sample_menu_items):
    """Test that order items snapshot the price at order time."""
    order_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    # Order item should have snapshotted the price
    assert order.order_items[0].unit_price == 8000
    assert order.order_items[0].menu_item_name == "Masala Dosa"

    # Now change the menu item price
    sample_menu_items[0].price = 9000
    db.commit()

    # Order should still have old price
    db.refresh(order)
    assert order.order_items[0].unit_price == 8000  # Old price preserved


def test_order_item_snapshots_name(db: Session, sample_menu_items):
    """Test that order items snapshot the name at order time."""
    order_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    original_name = order.order_items[0].menu_item_name
    assert original_name == "Masala Dosa"

    # Change menu item name
    sample_menu_items[0].name = "Special Masala Dosa"
    db.commit()

    # Order should still have old name
    db.refresh(order)
    assert order.order_items[0].menu_item_name == original_name


# ============================================================================
# Test Active Orders
# ============================================================================


def test_get_active_orders(db: Session, sample_menu_items):
    """Test getting only active orders."""
    # Create active order
    order_data_1 = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    active_order, _ = crud.create_order(db, order_data_1)

    # Create and mark as paid
    order_data_2 = OrderCreate(
        table_number=2,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=1)]
    )
    paid_order, _ = crud.create_order(db, order_data_2)
    paid_order.status = OrderStatus.PAID
    db.commit()

    # Get active orders
    active_orders = crud.get_orders(db, status=OrderStatus.ACTIVE)

    assert len(active_orders) == 1
    assert active_orders[0].id == active_order.id
    assert active_orders[0].status == OrderStatus.ACTIVE


def test_get_active_order_for_table(db: Session, sample_menu_items):
    """Test getting active order for a specific table."""
    order_data = OrderCreate(
        table_number=5,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    # Should find the order
    found_order = crud.get_active_order_for_table(db, 5)
    assert found_order is not None
    assert found_order.id == order.id

    # Should not find order for different table
    not_found = crud.get_active_order_for_table(db, 10)
    assert not_found is None


def test_only_one_active_order_per_table(db: Session, sample_menu_items):
    """Test business rule: only one active order per table."""
    # Create first order
    order_data_1 = OrderCreate(
        table_number=5,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order1, _ = crud.create_order(db, order_data_1)

    # Try to create another order (should update existing)
    order_data_2 = OrderCreate(
        table_number=5,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=1)]
    )
    order2, _ = crud.create_order(db, order_data_2)

    # Should be same order
    assert order1.id == order2.id

    # Verify only one active order exists for this table
    active_orders = crud.get_orders(db, status=OrderStatus.ACTIVE, table_number=5)
    assert len(active_orders) == 1


# ============================================================================
# Test Admin Order Editing
# ============================================================================


def test_admin_edit_order(db: Session, sample_menu_items):
    """Test admin can edit order items."""
    # Create order
    order_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    # Admin edits order
    edit_data = OrderItemsUpdate(
        items=[
            OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=2),
            OrderItemCreate(menu_item_id=sample_menu_items[2].id, quantity=1),
        ]
    )
    updated_order = crud.admin_edit_order(db, order.id, edit_data)

    assert updated_order is not None
    assert len(updated_order.order_items) == 2
    assert updated_order.order_items[0].menu_item_id == sample_menu_items[1].id
    assert updated_order.order_items[0].quantity == 2


def test_admin_edit_recalculates_totals(db: Session, sample_menu_items):
    """Test that admin edit recalculates GST and totals."""
    # Create order: 1 Dosa (8000)
    order_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)
    original_total = order.total_amount

    # Edit to: 2 Coffee (2 * 4000 = 8000)
    edit_data = OrderItemsUpdate(
        items=[OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=2)]
    )
    updated_order = crud.admin_edit_order(db, order.id, edit_data)

    # Same subtotal but verify recalculation happened
    assert updated_order.subtotal == 8000
    assert updated_order.gst_amount == 1440  # 18% of 8000
    assert updated_order.total_amount == 9440


def test_admin_edit_nonexistent_order(db: Session):
    """Test editing non-existent order returns None."""
    edit_data = OrderItemsUpdate(
        items=[OrderItemCreate(menu_item_id=1, quantity=1)]
    )
    result = crud.admin_edit_order(db, 99999, edit_data)
    assert result is None


def test_admin_edit_unavailable_item(db: Session, sample_menu_items):
    """Test editing order with unavailable item raises error."""
    # Create order
    order_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    # Mark item as unavailable
    sample_menu_items[1].is_available = False
    db.commit()

    # Try to edit with unavailable item
    edit_data = OrderItemsUpdate(
        items=[OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=1)]
    )

    with pytest.raises(ValueError, match="not available"):
        crud.admin_edit_order(db, order.id, edit_data)


# ============================================================================
# Test Table Number Changes
# ============================================================================


def test_admin_change_table_number(db: Session, sample_menu_items):
    """Test admin can change table number when editing an order."""
    # Create order on table 5
    order_data = OrderCreate(
        table_number=5,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    # Change to table 7 while editing
    edit_data = OrderItemsUpdate(
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)],
        table_number=7
    )
    updated_order = crud.admin_edit_order(db, order.id, edit_data)

    assert updated_order is not None
    assert updated_order.table_number == 7

    # Verify old table 5 has no active order
    old_table_order = crud.get_active_order_for_table(db, 5)
    assert old_table_order is None

    # Verify new table 7 has the order
    new_table_order = crud.get_active_order_for_table(db, 7)
    assert new_table_order is not None
    assert new_table_order.id == order.id


def test_admin_change_table_to_occupied_table_fails(db: Session, sample_menu_items):
    """Test that changing table to an occupied table fails."""
    # Create order on table 5
    order1_data = OrderCreate(
        table_number=5,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order1, _ = crud.create_order(db, order1_data)

    # Create order on table 7
    order2_data = OrderCreate(
        table_number=7,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=1)]
    )
    order2, _ = crud.create_order(db, order2_data)

    # Try to move order from table 5 to table 7 (already occupied)
    edit_data = OrderItemsUpdate(
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)],
        table_number=7
    )

    with pytest.raises(ValueError, match="already has an active order"):
        crud.admin_edit_order(db, order1.id, edit_data)

    # Verify both orders are still on their original tables
    assert crud.get_active_order_for_table(db, 5).id == order1.id
    assert crud.get_active_order_for_table(db, 7).id == order2.id


def test_admin_change_table_number_without_changing_items(db: Session, sample_menu_items):
    """Test admin can change only the table number without changing items."""
    # Create order on table 3
    order_data = OrderCreate(
        table_number=3,
        customer_name="John Doe",
        items=[
            OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=2),
            OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=1)
        ]
    )
    order, _ = crud.create_order(db, order_data)
    original_subtotal = order.subtotal
    original_total = order.total_amount

    # Change only the table number, keep same items
    edit_data = OrderItemsUpdate(
        items=[
            OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=2),
            OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=1)
        ],
        table_number=8
    )
    updated_order = crud.admin_edit_order(db, order.id, edit_data)

    assert updated_order.table_number == 8
    assert updated_order.subtotal == original_subtotal
    assert updated_order.total_amount == original_total
    assert updated_order.customer_name == "John Doe"
    assert len(updated_order.order_items) == 2


def test_admin_change_table_to_same_table_number(db: Session, sample_menu_items):
    """Test that setting table to same number doesn't cause conflicts."""
    # Create order on table 4
    order_data = OrderCreate(
        table_number=4,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    # Edit order with same table number
    edit_data = OrderItemsUpdate(
        items=[OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=2)],
        table_number=4  # Same table
    )
    updated_order = crud.admin_edit_order(db, order.id, edit_data)

    assert updated_order is not None
    assert updated_order.table_number == 4


def test_admin_change_table_and_items_together(db: Session, sample_menu_items):
    """Test admin can change both table number and items in one operation."""
    # Create order on table 2
    order_data = OrderCreate(
        table_number=2,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    # Change table and items
    edit_data = OrderItemsUpdate(
        items=[
            OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=3),
            OrderItemCreate(menu_item_id=sample_menu_items[2].id, quantity=1)
        ],
        table_number=9
    )
    updated_order = crud.admin_edit_order(db, order.id, edit_data)

    assert updated_order.table_number == 9
    assert len(updated_order.order_items) == 2
    assert updated_order.order_items[0].quantity == 3


def test_admin_edit_without_table_number_keeps_original(db: Session, sample_menu_items):
    """Test that omitting table_number keeps the original table."""
    # Create order on table 6
    order_data = OrderCreate(
        table_number=6,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    # Edit items without specifying table_number
    edit_data = OrderItemsUpdate(
        items=[OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=2)]
    )
    updated_order = crud.admin_edit_order(db, order.id, edit_data)

    assert updated_order.table_number == 6  # Should remain unchanged


# ============================================================================
# Test Order Cancellation
# ============================================================================


def test_cancel_order(db: Session, sample_menu_items):
    """Test canceling an active order."""
    # Create order
    order_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    # Cancel order
    canceled_order = crud.cancel_order(db, order.id)

    assert canceled_order is not None
    assert canceled_order.status == OrderStatus.CANCELED


def test_cancel_nonexistent_order(db: Session):
    """Test canceling non-existent order returns None."""
    result = crud.cancel_order(db, 99999)
    assert result is None


def test_cannot_cancel_paid_order(db: Session, sample_menu_items):
    """Test that paid orders cannot be canceled."""
    # Create and pay order
    order_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)
    order.status = OrderStatus.PAID
    db.commit()

    # Try to cancel
    with pytest.raises(ValueError, match="Cannot cancel a paid order"):
        crud.cancel_order(db, order.id)


def test_canceled_order_not_in_active_list(db: Session, sample_menu_items):
    """Test that canceled orders don't appear in active orders."""
    # Create order
    order_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    # Cancel it
    crud.cancel_order(db, order.id)

    # Should not appear in active orders
    active_orders = crud.get_orders(db, status=OrderStatus.ACTIVE)
    assert len(active_orders) == 0


# ============================================================================
# Test Edge Cases
# ============================================================================


def test_create_order_with_invalid_menu_item(db: Session):
    """Test creating order with non-existent menu item raises error."""
    order_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=99999, quantity=1)]
    )

    with pytest.raises(ValueError, match="not found"):
        crud.create_order(db, order_data)


def test_create_order_with_unavailable_item(db: Session, sample_menu_items):
    """Test creating order with unavailable item raises error."""
    # Mark item as unavailable
    sample_menu_items[0].is_available = False
    db.commit()

    order_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )

    with pytest.raises(ValueError, match="not available"):
        crud.create_order(db, order_data)


def test_order_subtotal_calculation(db: Session, sample_menu_items):
    """Test that order item subtotals are calculated correctly."""
    order_data = OrderCreate(
        table_number=1,
        items=[
            OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=3),
        ]
    )
    order, _ = crud.create_order(db, order_data)

    # Item subtotal should be quantity * unit_price
    assert order.order_items[0].subtotal == 3 * 8000
    assert order.order_items[0].subtotal == 24000


def test_multiple_tables_independent(db: Session, sample_menu_items):
    """Test that orders on different tables are independent."""
    # Create orders on different tables
    order_data_1 = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order1, _ = crud.create_order(db, order_data_1)

    order_data_2 = OrderCreate(
        table_number=2,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[1].id, quantity=2)]
    )
    order2, _ = crud.create_order(db, order_data_2)

    order_data_3 = OrderCreate(
        table_number=3,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[2].id, quantity=3)]
    )
    order3, _ = crud.create_order(db, order_data_3)

    # All should be different orders
    assert order1.id != order2.id != order3.id
    assert order1.table_number == 1
    assert order2.table_number == 2
    assert order3.table_number == 3

    # All should be active
    active_orders = crud.get_orders(db, status=OrderStatus.ACTIVE)
    assert len(active_orders) == 3


def test_customer_name_optional(db: Session, sample_menu_items):
    """Test that customer name is optional."""
    order_data = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order, _ = crud.create_order(db, order_data)

    assert order.customer_name is None


def test_customer_name_updated(db: Session, sample_menu_items):
    """Test that customer name can be updated."""
    # Create order without name
    order_data_1 = OrderCreate(
        table_number=1,
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=1)]
    )
    order1, _ = crud.create_order(db, order_data_1)
    assert order1.customer_name is None

    # Update order with name
    order_data_2 = OrderCreate(
        table_number=1,
        customer_name="Jane Doe",
        items=[OrderItemCreate(menu_item_id=sample_menu_items[0].id, quantity=2)]
    )
    order2, _ = crud.create_order(db, order_data_2)

    assert order2.customer_name == "Jane Doe"
