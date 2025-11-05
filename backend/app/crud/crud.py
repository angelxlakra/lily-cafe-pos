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
from app.utils.rounding import round_down_to_rupee


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
    db: Session,
    available_only: bool = False,
    category_id: Optional[int] = None,
    search: Optional[str] = None
) -> List[models.MenuItem]:
    """
    Get menu items with optional filtering.

    Args:
        db: Database session
        available_only: If True, only return available items
        category_id: If provided, filter by category
        search: If provided, search in item name and description

    Returns:
        List of menu items
    """
    query = db.query(models.MenuItem)

    if available_only:
        query = query.filter(models.MenuItem.is_available == True)

    if category_id:
        query = query.filter(models.MenuItem.category_id == category_id)

    if search:
        # Search in both name and description (case-insensitive)
        search_term = f"%{search}%"
        query = query.filter(
            (models.MenuItem.name.ilike(search_term)) |
            (models.MenuItem.description.ilike(search_term))
        )

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


def generate_order_number(db: Session) -> str:
    """
    Generate sequential order number in format: ORD-YYYYMMDD-####
    Example: ORD-20250130-0001

    Order numbers reset daily. The sequence increments for each order
    created on the same day.
    """
    today = date.today()
    today_str = today.strftime("%Y%m%d")

    # Get the last order created today.
    # Use the order_number prefix instead of created_at since timestamps are stored in UTC.
    last_order = (
        db.query(models.Order)
        .filter(models.Order.order_number.like(f"ORD-{today_str}-%"))
        .order_by(models.Order.order_number.desc())
        .first()
    )

    if last_order and last_order.order_number.startswith(f"ORD-{today_str}-"):
        # Extract the sequence number and increment
        try:
            last_seq = int(last_order.order_number.split("-")[-1])
            new_seq = last_seq + 1
        except (ValueError, IndexError):
            # If parsing fails, start from 1
            new_seq = 1
    else:
        # First order of the day
        new_seq = 1

    return f"ORD-{today_str}-{new_seq:04d}"


def get_orders(
    db: Session,
    status: Optional[models.OrderStatus] = None,
    table_number: Optional[int] = None,
    today_only: bool = False,
    date_str: Optional[str] = None,
) -> List[models.Order]:
    """
    Get orders with optional filtering.

    Args:
        db: Database session
        status: Filter by order status
        table_number: Filter by table number
        today_only: If True, only return today's orders
        date_str: Filter by specific date in YYYY-MM-DD format

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

    if date_str:
        try:
            from datetime import datetime
            filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            query = query.filter(func.date(models.Order.created_at) == filter_date)
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")

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


def create_order(db: Session, order: schemas.OrderCreate) -> tuple[models.Order, list[models.OrderItem]]:
    """
    Create a new order OR update existing active order (smart logic).

    This implements "upsert" behavior:
    - If table has an active order: Update it with new items
    - If table is empty: Create a new order

    This allows waiters to keep adding items to a table without worrying
    about whether to create or update.

    Args:
        db: Database session
        order: Order creation data

    Returns:
        Tuple of (order, new_items_only) where:
        - order: The created or updated order with all items
        - new_items_only: List of only the newly added OrderItems (for chit printing)

    Raises:
        ValueError: If any menu item is not found or not available
    """
    # Check if table already has an active order
    existing_order = get_active_order_for_table(db, order.table_number)

    if existing_order:
        # Update existing order: append new items or merge quantities for same items
        # Create a map of existing items by menu_item_id
        existing_items_map = {
            item.menu_item_id: item for item in existing_order.order_items
        }

        # Track new items for chit printing
        new_items_only = []

        # Process new items
        for item in order.items:
            # Get menu item
            menu_item = get_menu_item(db, item.menu_item_id)
            if not menu_item:
                raise ValueError(f"Menu item {item.menu_item_id} not found")
            if not menu_item.is_available:
                raise ValueError(f"Menu item '{menu_item.name}' is not available")

            # Check if this item already exists in the order
            if menu_item.id in existing_items_map:
                # Update quantity of existing item
                existing_item = existing_items_map[menu_item.id]
                old_quantity = existing_item.quantity
                existing_item.quantity += item.quantity
                existing_item.subtotal = existing_item.quantity * existing_item.unit_price

                # Create a virtual OrderItem for the NEW quantity only (for chit printing)
                new_item_chit = models.OrderItem(
                    order_id=existing_order.id,
                    menu_item_id=menu_item.id,
                    menu_item_name=menu_item.name,
                    quantity=item.quantity,  # Only the additional quantity
                    unit_price=menu_item.price,
                    subtotal=menu_item.price * item.quantity,
                )
                new_items_only.append(new_item_chit)
            else:
                # Add new item to order
                item_subtotal = menu_item.price * item.quantity
                new_order_item = models.OrderItem(
                    order_id=existing_order.id,
                    menu_item_id=menu_item.id,
                    menu_item_name=menu_item.name,
                    quantity=item.quantity,
                    unit_price=menu_item.price,
                    subtotal=item_subtotal,
                )
                db.add(new_order_item)
                new_items_only.append(new_order_item)

        # Recalculate totals from ALL items (old + new)
        db.flush()  # Flush to get updated items
        db.refresh(existing_order)  # Refresh to get all order_items

        subtotal = sum(item.subtotal for item in existing_order.order_items)
        gst_amount = int(subtotal * settings.GST_RATE / 100)
        # Round down total to nearest rupee (customer-friendly, no paise)
        total_amount = round_down_to_rupee(subtotal + gst_amount)

        existing_order.subtotal = subtotal
        existing_order.gst_amount = gst_amount
        existing_order.total_amount = total_amount
        existing_order.updated_at = datetime.utcnow()

        # Update customer name if provided
        if order.customer_name:
            existing_order.customer_name = order.customer_name

        db.commit()
        db.refresh(existing_order)
        return existing_order, new_items_only

    else:
        # Create new order (all items are new)
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
        # Round down total to nearest rupee (customer-friendly, no paise)
        total_amount = round_down_to_rupee(subtotal + gst_amount)

        # Create order
        db_order = models.Order(
            order_number=generate_order_number(db),
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
        # For new orders, all items are new
        return db_order, db_order.order_items


def update_order(
    db: Session, order_id: int, order: schemas.OrderUpdate
) -> Optional[models.Order]:
    """Update an existing order (status/metadata only)."""
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


def admin_edit_order(
    db: Session, order_id: int, order_update: schemas.OrderItemsUpdate
) -> Optional[models.Order]:
    """
    Admin function to edit order items and recalculate totals.

    This replaces all items in the order with the new items provided.
    Used by admin to fix order mistakes or make changes requested by customers.

    Args:
        db: Database session
        order_id: Order ID to edit
        order_update: New order items and optional customer name

    Returns:
        Updated order with new items, or None if order not found

    Raises:
        ValueError: If any menu item is not found or not available
    """
    db_order = get_order(db, order_id)
    if not db_order:
        return None

    # Delete existing order items
    for old_item in db_order.order_items:
        db.delete(old_item)
    db.flush()  # Flush deletes before adding new items

    # Add new items
    subtotal = 0
    for item in order_update.items:
        # Get menu item
        menu_item = get_menu_item(db, item.menu_item_id)
        if not menu_item:
            raise ValueError(f"Menu item {item.menu_item_id} not found")
        if not menu_item.is_available:
            raise ValueError(f"Menu item '{menu_item.name}' is not available")

        # Calculate item subtotal
        item_subtotal = menu_item.price * item.quantity
        subtotal += item_subtotal

        # Create new order item
        new_order_item = models.OrderItem(
            order_id=db_order.id,
            menu_item_id=menu_item.id,
            menu_item_name=menu_item.name,
            quantity=item.quantity,
            unit_price=menu_item.price,
            subtotal=item_subtotal,
        )
        db.add(new_order_item)

    # Recalculate totals
    gst_amount = int(subtotal * settings.GST_RATE / 100)
    # Round down total to nearest rupee (customer-friendly, no paise)
    total_amount = round_down_to_rupee(subtotal + gst_amount)

    db_order.subtotal = subtotal
    db_order.gst_amount = gst_amount
    db_order.total_amount = total_amount
    db_order.updated_at = datetime.utcnow()

    # Update customer name if provided
    if order_update.customer_name:
        db_order.customer_name = order_update.customer_name

    db.commit()
    db.refresh(db_order)
    return db_order


def cancel_order(db: Session, order_id: int) -> Optional[models.Order]:
    """
    Cancel an order (soft delete - sets status to CANCELED).

    Canceled orders remain in the database for record keeping but are
    not shown in active orders. They also don't appear in order history.

    Args:
        db: Database session
        order_id: Order ID to cancel

    Returns:
        Canceled order, or None if order not found

    Raises:
        ValueError: If order is already paid (cannot cancel paid orders)
    """
    db_order = get_order(db, order_id)
    if not db_order:
        return None

    # Don't allow canceling paid orders
    if db_order.status == models.OrderStatus.PAID:
        raise ValueError("Cannot cancel a paid order")

    db_order.status = models.OrderStatus.CANCELED
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

    # If order is fully paid, mark as paid
    total_paid += payment.amount
    if total_paid >= order.total_amount:
        order.status = models.OrderStatus.PAID
        order.updated_at = datetime.utcnow()
        db.commit()

    return db_payment


def get_payments_for_order(db: Session, order_id: int) -> List[models.Payment]:
    """Get all payments for an order."""
    return db.query(models.Payment).filter(models.Payment.order_id == order_id).all()

def create_payments_batch(
    db: Session, order_id: int, payments: List[schemas.PaymentCreate]
) -> List[models.Payment]:
    """
    Add multiple payments to an order atomically (for split payments).

      This is the preferred way to handle split payments as it:
      1. Validates the total equals order amount BEFORE creating any payments
      2. Creates all payments in a single transaction (atomic)
      3. Marks order as paid only if total matches exactly

      Args:
          db: Database session
          order_id: Order ID
          payments: List of payments to create

      Returns:
          List of created payments

      Raises:
          ValueError: If order not found, total doesn't match, or validation fails
    """

    order = get_order(db, order_id)

    if not order:
        raise ValueError(f"Order {order_id} not found")
    

    if order.status == models.OrderStatus.PAID:
        raise ValueError("Order is already paid")

    existing_total = sum(p.amount for p in order.payments)

    new_payments_total = sum(p.amount for p in payments)

    total_after = existing_total + new_payments_total

    if total_after != order.total_amount:
        raise ValueError(
            f"Payment total {total_after} does not match order total {order.total_amount}. "
            f"Expected {order.total_amount - existing_total} more to complete payment"
        )

    created_payments = []
    for payment in payments:
        db_payment = models.Payment(
            order_id=order_id,
            payment_method=payment.payment_method,
            amount=payment.amount
        )
        db.add(db_payment)
        created_payments.append(db_payment)
    

    order.status = models.OrderStatus.PAID
    order.updated_at = datetime.utcnow()

    db.commit()

    for payment in created_payments:
        db.refresh(payment)
    db.refresh(order)

    return created_payments
