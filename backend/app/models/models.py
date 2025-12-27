"""
SQLAlchemy database models for Lily Cafe POS System.
Defines the schema for menu items, orders, payments, and categories.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base


class OrderStatus(str, enum.Enum):
    """Order status enumeration."""

    ACTIVE = "active"  # Order saved, not yet paid
    PAID = "paid"  # Bill generated, payment completed
    CANCELED = "canceled"  # Order canceled by admin


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration."""

    CASH = "cash"
    UPI = "upi"
    CARD = "card"


class Category(Base):
    """Menu item categories (e.g., Coffee, Tea, Snacks, Meals)."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    menu_items = relationship("MenuItem", back_populates="category")


class MenuItem(Base):
    """Menu items available for ordering."""

    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(String(500))
    # Price stored in paise (�80 = 8000 paise) to avoid float precision issues
    price = Column(Integer, nullable=False)  # Price in paise
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    is_vegetarian = Column(Boolean, default=True)  # True for veg, False for non-veg
    is_beverage = Column(Boolean, default=False)  # True for beverages (tea, coffee, juice, etc.)
    is_available = Column(Boolean, default=True)  # Soft delete flag
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    category = relationship("Category", back_populates="menu_items")
    order_items = relationship("OrderItem", back_populates="menu_item")


class Order(Base):
    """Customer orders placed at tables."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    table_number = Column(Integer, nullable=False, index=True)
    customer_name = Column(String(200))  # Optional customer name
    subtotal = Column(Integer, nullable=False)  # Amount in paise before GST
    gst_amount = Column(Integer, nullable=False)  # GST amount in paise
    total_amount = Column(Integer, nullable=False)  # Final total in paise
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.ACTIVE, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Individual items in an order with snapshotted menu item details."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)

    # Snapshot fields - preserve menu item details at time of order
    menu_item_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    quantity_served = Column(Integer, default=0, nullable=False)  # Track how many items have been served
    unit_price = Column(Integer, nullable=False)  # Price in paise at time of order
    subtotal = Column(Integer, nullable=False)  # quantity * unit_price
    is_beverage = Column(Boolean, default=False)  # Snapshot of is_beverage at time of order
    is_served = Column(Boolean, default=False)  # Track if item has been served to customer

    # Relationships
    order = relationship("Order", back_populates="order_items")
    menu_item = relationship("MenuItem", back_populates="order_items")


class Payment(Base):
    """Payment records for orders (supports split payments)."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    amount = Column(Integer, nullable=False)  # Amount in paise
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    order = relationship("Order", back_populates="payments")
