"""
Pydantic schemas for request/response validation in Lily Cafe POS API.
These schemas define the shape of data sent to and received from the API.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
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
    is_parcel: bool = Field(default=False, description="True if this item is for parcel/takeaway")


class OrderItemCreate(OrderItemBase):
    """Schema for creating an order item (user input)."""

    pass


class OrderItem(BaseModel):
    """Schema for order item responses."""

    id: int
    menu_item_id: int
    menu_item_name: str
    quantity: int
    quantity_served: int = 0
    unit_price: int  # In paise
    subtotal: int  # In paise
    is_beverage: bool = False
    is_served: bool = False
    is_parcel: bool = False

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


class PaymentBreakdown(BaseModel):
    cash: int
    upi: int
    card: int


class PaginatedOrders(BaseModel):
    """Schema for paginated order response."""

    items: List[Order]
    total: int
    page: int
    size: int
    pages: int
    total_revenue: Optional[int] = 0
    payment_breakdown: Optional[PaymentBreakdown] = None



# ============================================================================
# App Config Schema
# ============================================================================
class AppConfig(BaseModel):
    """Schema for exposing application configuration values."""
    restaurant_name: str
    max_tables: int
    gst_rate: float


# ============================================================================
# Inventory Category Schemas
# ============================================================================
class InventoryCategoryBase(BaseModel):
    """Base schema for inventory categories."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class InventoryCategoryCreate(InventoryCategoryBase):
    """Schema for creating a new inventory category."""
    pass


class InventoryCategoryUpdate(BaseModel):
    """Schema for updating an inventory category (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class InventoryCategory(InventoryCategoryBase):
    """Schema for inventory category responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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

class HeatmapPoint(BaseModel):
    """Data point for heatmap."""
    day_of_week: int = Field(..., description="0=Sunday, 6=Saturday")
    hour: int = Field(..., ge=0, le=23)
    order_count: int
    revenue: float



class HeatmapResponse(BaseModel):
    """Response generic for heatmap data."""
    data: List[HeatmapPoint]


class CalendarHeatmapPoint(BaseModel):
    """Data point for calendar heatmap."""
    date: str  # YYYY-MM-DD
    value: float
    count: int


class CalendarHeatmapData(BaseModel):
    """Calendar heatmap analytics data."""
    data: List[CalendarHeatmapPoint]


# ============================================================================
# Detailed Analytics Response Schemas
# ============================================================================


class BaseCategoryStat(BaseModel):
    name: str
    revenue_rupees: float
    order_count: int
    avg_order_value_rupees: float
    items_count: int
    top_item: Optional[Any] = None
    vegetarian_ratio: float
    beverage_ratio: float
    revenue_percentage: float


class CategoryPerformanceResponse(BaseModel):
    categories: List[BaseCategoryStat]
    total_categories: int


class LowStockItem(BaseModel):
    name: str
    current_quantity: float
    unit: str
    min_threshold: float
    shortage: float
    category: str


class InventoryItemSummary(BaseModel):
    name: str
    current_quantity: float
    value_rupees: float
    category: str

class InventoryStatusResponse(BaseModel):
    items: List[InventoryItemSummary]
    low_stock_items: List[LowStockItem]
    low_stock_count: int
    out_of_stock_count: int
    total_inventory_value_rupees: float


class ProductPerformanceItem(BaseModel):
    name: str
    quantity_sold: int
    revenue_rupees: float
    order_count: int = 0
    avg_quantity_per_order: float = 0
    frequency: float = 0


class ProductPerformanceDetailedResponse(BaseModel):
    top_products: List[ProductPerformanceItem]


class PaymentMethodStat(BaseModel):
    total_amount_rupees: float
    transaction_count: int
    avg_transaction_rupees: float
    percentage_revenue: float
    percentage_count: float


class PaymentTrendsResponse(BaseModel):
    payment_methods: Dict[str, PaymentMethodStat]
    total_revenue_rupees: float
    highest_avg_transaction_method: Optional[str]


class OrderStatsDetailedResponse(BaseModel):
    total_orders: int
    active_orders: int
    completed_orders: int
    average_order_value_rupees: float
    # conversion_rates for funnel
    active_rate: float
    completion_rate: float
    cancellation_rate: float


class RevenueCompositionItem(BaseModel):
    date: str
    category: str
    revenue: float


class RevenueCompositionResponse(BaseModel):
    data: List[RevenueCompositionItem]


class OrderStatusFlowItem(BaseModel):
    date: str
    status: str
    count: int


class OrderStatusFlowResponse(BaseModel):
    data: List[OrderStatusFlowItem]


class DayOfWeekStat(BaseModel):
    day: str # Mon, Tue...
    day_index: int # 0-6
    revenue_rupees: float
    order_count: int
    avg_order_value_rupees: float
    payment_diversity: int
    parcel_ratio: float


class DayOfWeekStatsResponse(BaseModel):
    data: List[DayOfWeekStat]


class BoxPlotData(BaseModel):
    min: float
    q1: float
    median: float
    q3: float
    max: float


class OrderValueDistributionItem(BaseModel):
    group: str
    stats: BoxPlotData


class OrderValueDistributionResponse(BaseModel):
    data: List[OrderValueDistributionItem]


class ItemQuantityDistributionItem(BaseModel):
    item_name: str
    stats: BoxPlotData


class ItemQuantityDistributionResponse(BaseModel):
    data: List[ItemQuantityDistributionItem]


class SankeyNode(BaseModel):
    name: str

class SankeyLink(BaseModel):
    source: int # index in nodes list
    target: int # index in nodes list
    value: float

class SankeyData(BaseModel):
    nodes: List[SankeyNode]
    links: List[SankeyLink]


class WaterfallItem(BaseModel):
    name: str
    value: float
    is_total: bool = False
    color: Optional[str] = None


class WaterfallResponse(BaseModel):
    data: List[WaterfallItem]


class OrdersTimelineItem(BaseModel):
    order_number: str
    table_number: int
    created_at: str
    amount: float
    paid_at: Optional[str]
    duration_minutes: Optional[float]


class OrdersTimelineResponse(BaseModel):
    data: List[OrdersTimelineItem]
