"""
CRUD (Create, Read, Update, Delete) operations for Lily Cafe POS System.
Database operations for menu items, orders, payments, and categories.
"""

from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models import models
from app.schemas import schemas
from app.core.config import settings


# ============================================================================
# Category Operations
# ============================================================================


def get_categories(db: Session) -> List[models.Category]:
    """Get all categories."""
    return db.query(models.Category).all()


def get_category(db: Session, category_id: int) -> Optional[models.Category]:
    """Get a single category by ID."""
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def create_category(db: Session, category: schemas.CategoryCreate) -> models.Category:
    """Create a new category."""
    db_category = models.Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


# ============================================================================
# Menu Item Operations
# ============================================================================


def get_menu_items(
    db: Session, available_only: bool = False, category_id: Optional[int] = None
) -> List[models.MenuItem]:
    """
    Get menu items with optional filtering.

    Args:
        db: Database session
        available_only: If True, only return available items
        category_id: If provided, filter by category

    Returns:
        List of menu items
    """
    query = db.query(models.MenuItem)

    if available_only:
        query = query.filter(models.MenuItem.is_available == True)

    if category_id:
        query = query.filter(models.MenuItem.category_id == category_id)

    return query.all()


def get_menu_item(db: Session, item_id: int) -> Optional[models.MenuItem]:
    """Get a single menu item by ID."""
    return db.query(models.MenuItem).filter(models.MenuItem.id == item_id).first()


def create_menu_item(db: Session, item: schemas.MenuItemCreate) -> models.MenuItem:
    """Create a new menu item."""
    db_item = models.MenuItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_menu_item(
    db: Session, item_id: int, item: schemas.MenuItemUpdate
) -> Optional[models.MenuItem]:
    """Update an existing menu item."""
    db_item = get_menu_item(db, item_id)
    if not db_item:
        return None

    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_menu_item(db: Session, item_id: int) -> bool:
    """
    Soft delete a menu item (set is_available = False).

    Returns:
        True if item was deleted, False if not found
    """
    db_item = get_menu_item(db, item_id)
    if not db_item:
        return False

    db_item.is_available = False
    db.commit()
    return True


# ============================================================================
# Order Operations
# ============================================================================


def generate_order_number() -> str:
    """
    Generate order number in format: ORD-YYYYMMDD-####
    Example: ORD-20250130-0001
    """
    today = date.today().strftime("%Y%m%d")
    # In a production system, you'd query the database for the last order number
    # For now, use timestamp-based unique number
    time_suffix = datetime.now().strftime("%H%M%S")
    return f"ORD-{today}-{time_suffix}"


def get_orders(
    db: Session,
    status: Optional[models.OrderStatus] = None,
    table_number: Optional[int] = None,
    today_only: bool = False,
) -> List[models.Order]:
    """
    Get orders with optional filtering.

    Args:
        db: Database session
        status: Filter by order status
        table_number: Filter by table number
        today_only: If True, only return today's orders

    Returns:
        List of orders
    """
    query = db.query(models.Order)

    if status:
        query = query.filter(models.Order.status == status)

    if table_number:
        query = query.filter(models.Order.table_number == table_number)

    if today_only:
        today = date.today()
        query = query.filter(func.date(models.Order.created_at) == today)

    return query.order_by(models.Order.created_at.desc()).all()


def get_order(db: Session, order_id: int) -> Optional[models.Order]:
    """Get a single order by ID with all related data."""
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_active_order_for_table(db: Session, table_number: int) -> Optional[models.Order]:
    """
    Check if a table has an active order.

    Args:
        db: Database session
        table_number: Table number to check

    Returns:
        Active order if exists, None otherwise
    """
    return (
        db.query(models.Order)
        .filter(
            and_(
                models.Order.table_number == table_number,
                models.Order.status == models.OrderStatus.ACTIVE,
            )
        )
        .first()
    )


def create_order(db: Session, order: schemas.OrderCreate) -> models.Order:
    """
    Create a new order with order items.

    Args:
        db: Database session
        order: Order creation data

    Returns:
        Created order with all items

    Raises:
        ValueError: If any menu item is not found or not available
    """
    # Check if table already has an active order
    existing_order = get_active_order_for_table(db, order.table_number)
    if existing_order:
        raise ValueError(f"Table {order.table_number} already has an active order")

    # Calculate totals
    subtotal = 0
    order_items = []

    for item in order.items:
        # Get menu item
        menu_item = get_menu_item(db, item.menu_item_id)
        if not menu_item:
            raise ValueError(f"Menu item {item.menu_item_id} not found")
        if not menu_item.is_available:
            raise ValueError(f"Menu item '{menu_item.name}' is not available")

        # Calculate item subtotal
        item_subtotal = menu_item.price * item.quantity
        subtotal += item_subtotal

        # Create order item with snapshot data
        order_items.append(
            models.OrderItem(
                menu_item_id=menu_item.id,
                menu_item_name=menu_item.name,
                quantity=item.quantity,
                unit_price=menu_item.price,
                subtotal=item_subtotal,
            )
        )

    # Calculate GST
    gst_amount = int(subtotal * settings.GST_RATE / 100)
    total_amount = subtotal + gst_amount

    # Create order
    db_order = models.Order(
        order_number=generate_order_number(),
        table_number=order.table_number,
        customer_name=order.customer_name,
        subtotal=subtotal,
        gst_amount=gst_amount,
        total_amount=total_amount,
        status=models.OrderStatus.ACTIVE,
        order_items=order_items,
    )

    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def update_order(
    db: Session, order_id: int, order: schemas.OrderUpdate
) -> Optional[models.Order]:
    """Update an existing order."""
    db_order = get_order(db, order_id)
    if not db_order:
        return None

    update_data = order.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_order, field, value)

    db_order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_order)
    return db_order


# ============================================================================
# Payment Operations
# ============================================================================


def create_payment(
    db: Session, order_id: int, payment: schemas.PaymentCreate
) -> models.Payment:
    """
    Add a payment to an order.

    Args:
        db: Database session
        order_id: Order ID
        payment: Payment data

    Returns:
        Created payment

    Raises:
        ValueError: If order not found or payment amount invalid
    """
    order = get_order(db, order_id)
    if not order:
        raise ValueError(f"Order {order_id} not found")

    # Check if payment amount doesn't exceed remaining balance
    total_paid = sum(p.amount for p in order.payments)
    remaining = order.total_amount - total_paid

    if payment.amount > remaining:
        raise ValueError(
            f"Payment amount {payment.amount} exceeds remaining balance {remaining}"
        )

    db_payment = models.Payment(
        order_id=order_id,
        payment_method=payment.payment_method,
        amount=payment.amount,
    )

    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)

    # If order is fully paid, mark as completed
    total_paid += payment.amount
    if total_paid >= order.total_amount:
        order.status = models.OrderStatus.COMPLETED
        order.updated_at = datetime.utcnow()
        db.commit()

    return db_payment


def get_payments_for_order(db: Session, order_id: int) -> List[models.Payment]:
    """Get all payments for an order."""
    return db.query(models.Payment).filter(models.Payment.order_id == order_id).all()
