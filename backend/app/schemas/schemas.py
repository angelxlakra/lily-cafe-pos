"""
Pydantic schemas for request/response validation in Lily Cafe POS API.
These schemas define the shape of data sent to and received from the API.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.models import OrderStatus, PaymentMethod


# ============================================================================
# Category Schemas
# ============================================================================


class CategoryBase(BaseModel):
    """Base category schema."""

    name: str = Field(..., min_length=1, max_length=100)


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""

    pass


class Category(CategoryBase):
    """Schema for category responses."""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Menu Item Schemas
# ============================================================================


class MenuItemBase(BaseModel):
    """Base menu item schema."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    price: int = Field(..., gt=0, description="Price in paise (�80 = 8000 paise)")
    category_id: int
    is_vegetarian: bool = True
    is_beverage: bool = False


class MenuItemCreate(MenuItemBase):
    """Schema for creating a new menu item."""

    pass


class MenuItemUpdate(BaseModel):
    """Schema for updating a menu item."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[int] = Field(None, gt=0)
    category_id: Optional[int] = None
    is_vegetarian: Optional[bool] = None
    is_beverage: Optional[bool] = None
    is_available: Optional[bool] = None


class MenuItem(MenuItemBase):
    """Schema for menu item responses."""

    id: int
    is_available: bool
    created_at: datetime
    updated_at: datetime
    category: Category

    class Config:
        from_attributes = True


# ============================================================================
# Order Item Schemas
# ============================================================================


class OrderItemBase(BaseModel):
    """Base order item schema."""

    menu_item_id: int
    quantity: int = Field(..., gt=0)


class OrderItemCreate(OrderItemBase):
    """Schema for creating an order item (user input)."""

    pass


class OrderItem(BaseModel):
    """Schema for order item responses."""

    id: int
    menu_item_id: int
    menu_item_name: str
    quantity: int
    unit_price: int  # In paise
    subtotal: int  # In paise
    is_beverage: bool = False
    is_served: bool = False

    class Config:
        from_attributes = True


# ============================================================================
# Payment Schemas
# ============================================================================


class PaymentCreate(BaseModel):
    """Schema for creating a payment."""

    payment_method: PaymentMethod
    amount: int = Field(..., gt=0, description="Amount in paise")

class PaymentBatchCreate(BaseModel):
    """Schema for creating multiple payments at once (split payment)."""

    payments: List[PaymentCreate] = Field(..., min_length=1)


class Payment(BaseModel):
    """Schema for payment responses."""

    id: int
    payment_method: PaymentMethod
    amount: int  # In paise
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Order Schemas
# ============================================================================


class OrderCreate(BaseModel):
    """Schema for creating a new order."""

    table_number: int = Field(..., ge=1, le=50)
    customer_name: Optional[str] = Field(None, max_length=200)
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderUpdate(BaseModel):
    """Schema for updating an order (status/metadata only)."""

    status: Optional[OrderStatus] = None
    customer_name: Optional[str] = Field(None, max_length=200)


class OrderItemsUpdate(BaseModel):
    """Schema for admin to edit order items (replaces all items)."""

    items: List[OrderItemCreate] = Field(..., min_length=1)
    customer_name: Optional[str] = Field(None, max_length=200)
    table_number: Optional[int] = Field(None, ge=1, le=50, description="Change table number (optional)")


class Order(BaseModel):
    """Schema for order responses."""

    id: int
    order_number: str
    table_number: int
    customer_name: Optional[str]
    subtotal: int  # In paise
    gst_amount: int  # In paise
    total_amount: int  # In paise
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    order_items: List[OrderItem]
    payments: List[Payment]

    class Config:
        from_attributes = True


class OrderSummary(BaseModel):
    """Lightweight order schema for listings."""

    id: int
    order_number: str
    table_number: int
    customer_name: Optional[str]
    total_amount: int
    status: OrderStatus
    created_at: datetime
    item_count: int  # Number of unique items

    class Config:
        from_attributes = True


# ============================================================================
# App Config Schema
# ============================================================================
class AppConfig(BaseModel):
    """Schema for exposing application configuration values."""
    restaurant_name: str
    max_tables: int
    gst_rate: float
    
# ============================================================================
# Authentication Schemas
# ============================================================================


class LoginRequest(BaseModel):
    """Schema for admin login request."""

    username: str
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data."""

    username: Optional[str] = None
