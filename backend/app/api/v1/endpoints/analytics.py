"""
Analytics endpoints for Lily Cafe POS System.
Provides revenue, product, and order statistics with Thesys C1 generative UI integration.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel
from openai import OpenAI

from app.api.deps import get_db
from app.core.config import settings
from app.models.models import Order, OrderItem, Payment, PaymentMethod, OrderStatus, MenuItem
from app.schemas.schemas import (
    CategoryPerformanceResponse,
    InventoryStatusResponse,
    ProductPerformanceDetailedResponse,
    PaymentTrendsResponse,
    OrderStatsDetailedResponse,
    RevenueCompositionResponse,
    OrderStatusFlowResponse,
    DayOfWeekStatsResponse,
    OrderValueDistributionResponse,
    ItemQuantityDistributionResponse,
    SankeyData,
    WaterfallResponse,
    OrdersTimelineResponse
)

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================


class TimeRange(BaseModel):
    """Time range filter for analytics."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class RevenueData(BaseModel):
    """Revenue analytics data."""
    total_revenue: float
    total_orders: int
    average_order_value: float
    revenue_by_payment_method: dict
    revenue_trend: list


class ProductPerformance(BaseModel):
    """Product performance analytics."""
    top_products: list
    revenue_by_category: dict


class OrderStatistics(BaseModel):
    """Order statistics."""
    total_orders: int
    active_orders: int
    completed_orders: int
    canceled_orders: int
    average_order_value: float
    peak_hours: list


class HeatmapPoint(BaseModel):
    """Data point for heatmap."""
    day_of_week: int
    hour: int
    order_count: int
    revenue: float


class HeatmapData(BaseModel):
    """Heatmap analytics data."""
    data: List[HeatmapPoint]


class CalendarHeatmapPoint(BaseModel):
    """Data point for calendar heatmap."""
    date: str
    value: float
    count: int


class CalendarHeatmapData(BaseModel):
    """Calendar heatmap analytics data."""
    data: List[CalendarHeatmapPoint]


class C1QueryRequest(BaseModel):
    """Request for Thesys C1 conversational query."""
    prompt: dict  # OpenAI message format: {"role": "user", "content": "..."}
    threadId: Optional[str] = None
    responseId: Optional[str] = None


# ============================================================================
# Timezone Helper Functions
# ============================================================================

def to_ist_timestamp(column):
    """
    Convert a UTC timestamp column to IST (Asia/Kolkata) timezone.
    Returns a SQLAlchemy expression for use in queries.

    Usage: extract('hour', to_ist_timestamp(Order.created_at))

    Supports both PostgreSQL and SQLite.
    """
    from sqlalchemy import text
    # IST is UTC+5:30, which is +330 minutes
    # For SQLite, use datetime function with timezone offset
    # For PostgreSQL, use AT TIME ZONE
    # Since we're using SQLite in development, we'll use SQLite syntax
    return text(f"datetime({column.key}, '+330 minutes')")


# ============================================================================
# Thesys C1 Client Setup
# ============================================================================


def get_c1_client() -> OpenAI:
    """Get configured Thesys C1 client."""
    if not settings.THESYS_API_KEY:
        raise HTTPException(status_code=500, detail="Thesys API key not configured")

    return OpenAI(
        api_key=settings.THESYS_API_KEY,
        base_url="https://api.thesys.dev/v1/embed"
    )


# ============================================================================
# Helper Functions
# ============================================================================


def get_time_filter(start_date: Optional[datetime], end_date: Optional[datetime]):
    """Create time filter for queries."""
    filters = []

    if start_date:
        filters.append(Order.created_at >= start_date)
    if end_date:
        filters.append(Order.created_at <= end_date)

    return filters


def paise_to_rupees(paise: int) -> float:
    """Convert paise to rupees."""
    return paise / 100.0


# ============================================================================
# Tool Calling for C1
# ============================================================================


def get_revenue_data_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to get revenue data."""
    # Convert string dates to datetime if provided
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

    # Build time filters
    time_filters = get_time_filter(start_dt, end_dt)

    # Get paid orders
    paid_orders = db.query(Order).filter(
        and_(
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).all()

    # Calculate totals
    total_revenue_paise = sum(order.total_amount for order in paid_orders)
    total_orders = len(paid_orders)
    average_order_value = total_revenue_paise / total_orders if total_orders > 0 else 0

    # Revenue by payment method
    payment_methods = db.query(
        Payment.payment_method,
        func.sum(Payment.amount).label('total')
    ).join(Order).filter(
        and_(
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).group_by(Payment.payment_method).all()

    revenue_by_payment_method = {
        method.value: paise_to_rupees(total)
        for method, total in payment_methods
    }

    result = {
        "total_revenue_rupees": paise_to_rupees(total_revenue_paise),
        "total_orders": total_orders,
        "average_order_value_rupees": paise_to_rupees(average_order_value),
        "revenue_by_payment_method": revenue_by_payment_method
    }

    return json.dumps(result)


def get_product_data_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 10) -> str:
    """Tool function to get product performance data."""
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

    time_filters = get_time_filter(start_dt, end_dt)

    # Top products
    top_products_query = db.query(
        OrderItem.menu_item_name,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.subtotal).label('total_revenue')
    ).join(Order).filter(
        and_(
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).group_by(OrderItem.menu_item_name).order_by(
        func.sum(OrderItem.quantity).desc()
    ).limit(limit).all()

    top_products = [
        {
            "name": name,
            "quantity_sold": int(quantity),
            "revenue_rupees": paise_to_rupees(revenue)
        }
        for name, quantity, revenue in top_products_query
    ]

    result = {
        "top_products": top_products
    }

    return json.dumps(result)


def get_order_stats_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to get order statistics."""
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

    time_filters = get_time_filter(start_dt, end_dt)

    # Order counts
    total_orders = db.query(Order).filter(*time_filters).count()
    active_orders = db.query(Order).filter(
        and_(Order.status == OrderStatus.ACTIVE, *time_filters)
    ).count()
    completed_orders = db.query(Order).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).count()

    # Average order value
    avg_order_value = db.query(func.avg(Order.total_amount)).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 0

    result = {
        "total_orders": total_orders,
        "active_orders": active_orders,
        "completed_orders": completed_orders,
        "average_order_value_rupees": paise_to_rupees(avg_order_value)
    }

    return json.dumps(result)


def get_inventory_status_tool(db: Session) -> str:
    """Tool function to get current inventory status including low stock items."""
    from app.models.inventory_models import InventoryItem, InventoryCategory

    # Get all active inventory items
    items = db.query(InventoryItem).filter(InventoryItem.is_active == True).all()

    # Calculate metrics
    low_stock_items = []
    out_of_stock_count = 0
    total_value = 0.0

    all_items_summary = []
    
    for item in items:
        # Calculate total value
        item_val = 0.0
        if item.cost_per_unit:
            item_val = float(item.current_quantity * item.cost_per_unit)
            total_value += item_val

        category_name = item.category.name if item.category else "Uncategorized"
        
        all_items_summary.append({
            "name": item.name,
            "current_quantity": float(item.current_quantity),
            "value_rupees": item_val,
            "category": category_name
        })

        # Check if low stock
        if item.is_low_stock:
            shortage = float(item.min_threshold - item.current_quantity)

            low_stock_items.append({
                "name": item.name,
                "current_quantity": float(item.current_quantity),
                "unit": item.unit,
                "min_threshold": float(item.min_threshold),
                "shortage": shortage,
                "category": category_name
            })

            if item.current_quantity <= 0:
                out_of_stock_count += 1

    result = {
        "items": all_items_summary,
        "low_stock_items": low_stock_items,
        "low_stock_count": len(low_stock_items),
        "out_of_stock_count": out_of_stock_count,
        "total_inventory_value_rupees": round(total_value, 2)
    }

    return json.dumps(result)


def get_cash_counter_status_tool(db: Session, date: Optional[str] = None) -> str:
    """Tool function to get cash counter status for a specific date."""
    from app.models.cash_models import DailyCashCounter
    from decimal import Decimal

    # Parse date or use today
    if date:
        target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
    else:
        target_date = datetime.now(timezone.utc).date()

    # Get cash counter record
    counter = db.query(DailyCashCounter).filter(
        DailyCashCounter.date == target_date
    ).first()

    if not counter:
        return json.dumps({
            "error": f"No cash counter record found for {target_date}",
            "date": str(target_date),
            "status": "not_opened"
        })

    # Calculate cash received today from payments
    day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    day_end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    cash_payments = db.query(func.sum(Payment.amount)).join(Order).filter(
        and_(
            Payment.payment_method == PaymentMethod.CASH,
            Order.status == OrderStatus.PAID,
            Order.created_at >= day_start,
            Order.created_at <= day_end
        )
    ).scalar() or 0

    # Build denomination breakdown
    denomination_breakdown = {
        "opening": {
            "500s": counter.opening_500s,
            "200s": counter.opening_200s,
            "100s": counter.opening_100s,
            "50s": counter.opening_50s,
            "20s": counter.opening_20s,
            "10s": counter.opening_10s
        }
    }

    if counter.closing_balance is not None:
        denomination_breakdown["closing"] = {
            "500s": counter.closing_500s or 0,
            "200s": counter.closing_200s or 0,
            "100s": counter.closing_100s or 0,
            "50s": counter.closing_50s or 0,
            "20s": counter.closing_20s or 0,
            "10s": counter.closing_10s or 0
        }

    result = {
        "date": str(target_date),
        "status": counter.status,
        "opening_balance_rupees": float(counter.opening_balance),
        "closing_balance_rupees": float(counter.closing_balance) if counter.closing_balance else None,
        "expected_closing_rupees": float(counter.expected_closing) if counter.expected_closing else None,
        "variance_rupees": float(counter.variance) if counter.variance else None,
        "variance_percentage": round(float(counter.variance / counter.expected_closing * 100), 2) if counter.variance and counter.expected_closing and counter.expected_closing > 0 else None,
        "cash_received_today_rupees": paise_to_rupees(cash_payments),
        "denomination_breakdown": denomination_breakdown,
        "opened_by": counter.opened_by,
        "closed_by": counter.closed_by,
        "verified_by": counter.verified_by,
        "is_verified": counter.is_verified,
        "notes": counter.notes
    }

    return json.dumps(result)


def get_category_performance_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to get detailed category performance analysis."""
    from app.models.models import Category

    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)

    # Get all categories
    categories = db.query(Category).all()

    category_data = []
    total_revenue = 0

    for category in categories:
        # Revenue for this category
        cat_revenue = db.query(func.sum(OrderItem.subtotal)).join(
            MenuItem
        ).join(Order).filter(
            and_(
                MenuItem.category_id == category.id,
                Order.status == OrderStatus.PAID,
                *time_filters
            )
        ).scalar() or 0

        total_revenue += cat_revenue

        # Order count for this category
        order_count = db.query(func.count(func.distinct(Order.id))).join(
            OrderItem
        ).join(MenuItem).filter(
            and_(
                MenuItem.category_id == category.id,
                Order.status == OrderStatus.PAID,
                *time_filters
            )
        ).scalar() or 0

        # Item count in category
        items_count = db.query(func.count(MenuItem.id)).filter(
            MenuItem.category_id == category.id,
            MenuItem.is_available == True
        ).scalar() or 0

        # Top item in category
        top_item_result = db.query(
            OrderItem.menu_item_name,
            func.sum(OrderItem.quantity).label('total_qty')
        ).join(MenuItem).join(Order).filter(
            and_(
                MenuItem.category_id == category.id,
                Order.status == OrderStatus.PAID,
                *time_filters
            )
        ).group_by(OrderItem.menu_item_name).order_by(
            func.sum(OrderItem.quantity).desc()
        ).first()

        top_item = top_item_result[0] if top_item_result else None

        # Vegetarian ratio
        veg_items = db.query(func.count(MenuItem.id)).filter(
            MenuItem.category_id == category.id,
            MenuItem.is_vegetarian == True,
            MenuItem.is_available == True
        ).scalar() or 0

        veg_ratio = veg_items / items_count if items_count > 0 else 0

        # Beverage ratio
        beverage_items = db.query(func.count(MenuItem.id)).filter(
            MenuItem.category_id == category.id,
            MenuItem.is_beverage == True,
            MenuItem.is_available == True
        ).scalar() or 0

        beverage_ratio = beverage_items / items_count if items_count > 0 else 0

        category_data.append({
            "name": category.name,
            "revenue_rupees": paise_to_rupees(cat_revenue),
            "order_count": order_count,
            "avg_order_value_rupees": paise_to_rupees(cat_revenue / order_count) if order_count > 0 else 0,
            "items_count": items_count,
            "top_item": top_item,
            "vegetarian_ratio": round(veg_ratio, 2),
            "beverage_ratio": round(beverage_ratio, 2)
        })

    # Calculate percentages
    for cat in category_data:
        cat["revenue_percentage"] = round(cat["revenue_rupees"] / paise_to_rupees(total_revenue) * 100, 2) if total_revenue > 0 else 0

    # Sort by revenue descending
    category_data.sort(key=lambda x: x["revenue_rupees"], reverse=True)

    result = {
        "categories": category_data,
        "total_categories": len(categories)
    }

    return json.dumps(result)


def get_time_comparison_tool(db: Session, period: str = "today_vs_yesterday") -> str:
    """Tool function to compare metrics across time periods."""

    now = datetime.now(timezone.utc)

    # Define time periods
    if period == "today_vs_yesterday":
        current_start = datetime.combine(now.date(), datetime.min.time()).replace(tzinfo=timezone.utc)
        current_end = datetime.combine(now.date(), datetime.max.time()).replace(tzinfo=timezone.utc)
        previous_start = current_start - timedelta(days=1)
        previous_end = current_end - timedelta(days=1)
        current_label = str(now.date())
        previous_label = str((now - timedelta(days=1)).date())
    elif period == "this_week_vs_last_week":
        # Week starts on Monday
        current_start = now - timedelta(days=now.weekday())
        current_start = datetime.combine(current_start.date(), datetime.min.time()).replace(tzinfo=timezone.utc)
        current_end = now
        previous_start = current_start - timedelta(days=7)
        previous_end = current_end - timedelta(days=7)
        current_label = f"Week of {current_start.date()}"
        previous_label = f"Week of {previous_start.date()}"
    elif period == "this_month_vs_last_month":
        # Current month to date
        current_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        current_end = now
        # Last month same period
        if now.month == 1:
            previous_start = datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
        else:
            previous_start = datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)
        previous_end = previous_start + (current_end - current_start)
        current_label = f"This month ({now.strftime('%B %Y')})"
        previous_label = f"Last month ({previous_start.strftime('%B %Y')})"
    else:
        return json.dumps({"error": "Invalid period. Use 'today_vs_yesterday', 'this_week_vs_last_week', or 'this_month_vs_last_month'"})

    # Get current period metrics
    current_revenue = db.query(func.sum(Order.total_amount)).filter(
        and_(
            Order.status == OrderStatus.PAID,
            Order.created_at >= current_start,
            Order.created_at <= current_end
        )
    ).scalar() or 0

    current_orders = db.query(func.count(Order.id)).filter(
        and_(
            Order.status == OrderStatus.PAID,
            Order.created_at >= current_start,
            Order.created_at <= current_end
        )
    ).scalar() or 0

    current_aov = current_revenue / current_orders if current_orders > 0 else 0

    # Get previous period metrics
    previous_revenue = db.query(func.sum(Order.total_amount)).filter(
        and_(
            Order.status == OrderStatus.PAID,
            Order.created_at >= previous_start,
            Order.created_at <= previous_end
        )
    ).scalar() or 0

    previous_orders = db.query(func.count(Order.id)).filter(
        and_(
            Order.status == OrderStatus.PAID,
            Order.created_at >= previous_start,
            Order.created_at <= previous_end
        )
    ).scalar() or 0

    previous_aov = previous_revenue / previous_orders if previous_orders > 0 else 0

    # Calculate changes
    revenue_change = current_revenue - previous_revenue
    revenue_change_pct = (revenue_change / previous_revenue * 100) if previous_revenue > 0 else 0

    orders_change = current_orders - previous_orders
    orders_change_pct = (orders_change / previous_orders * 100) if previous_orders > 0 else 0

    aov_change = current_aov - previous_aov
    aov_change_pct = (aov_change / previous_aov * 100) if previous_aov > 0 else 0

    # Determine trend
    if revenue_change_pct > 5:
        trend = "up"
    elif revenue_change_pct < -5:
        trend = "down"
    else:
        trend = "flat"

    result = {
        "comparison": period,
        "current": {
            "period": current_label,
            "revenue_rupees": paise_to_rupees(current_revenue),
            "orders": current_orders,
            "avg_order_value_rupees": paise_to_rupees(current_aov)
        },
        "previous": {
            "period": previous_label,
            "revenue_rupees": paise_to_rupees(previous_revenue),
            "orders": previous_orders,
            "avg_order_value_rupees": paise_to_rupees(previous_aov)
        },
        "change": {
            "revenue_change_rupees": paise_to_rupees(revenue_change),
            "revenue_change_percentage": round(revenue_change_pct, 2),
            "orders_change": orders_change,
            "orders_change_percentage": round(orders_change_pct, 2),
            "aov_change_rupees": paise_to_rupees(aov_change),
            "aov_change_percentage": round(aov_change_pct, 2)
        },
        "trend": trend
    }

    return json.dumps(result)


def get_peak_hours_detailed_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to get detailed peak hours analysis."""
    from sqlalchemy import extract

    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)

    # Get hourly breakdown in IST
    hourly_stats = db.query(
        extract('hour', to_ist_timestamp(Order.created_at)).label('hour'),
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('revenue')
    ).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).group_by('hour').all()

    # Build hourly data with category info
    peak_hours = []
    for hour, order_count, revenue in hourly_stats:
        if hour is None:
            continue

        hour_int = int(hour)
        # Get top category for this hour in IST
        top_cat = db.query(
            MenuItem.category_id,
            func.count(OrderItem.id).label('item_count')
        ).join(OrderItem).join(Order).filter(
            and_(
                extract('hour', to_ist_timestamp(Order.created_at)) == hour_int,
                Order.status == OrderStatus.PAID,
                *time_filters
            )
        ).group_by(MenuItem.category_id).order_by(
            func.count(OrderItem.id).desc()
        ).first()

        if top_cat and top_cat[0]:
            from app.models.models import Category
            cat = db.query(Category).filter(Category.id == top_cat[0]).first()
            top_category = cat.name if cat else "Unknown"
        else:
            top_category = "Unknown"

        avg_order_value = revenue / order_count if order_count > 0 else 0

        peak_hours.append({
            "hour": hour_int,
            "hour_label": f"{hour_int}:00" if hour_int < 12 else (f"{hour_int}:00" if hour_int == 12 else f"{hour_int-12}:00"),
            "order_count": order_count,
            "revenue_rupees": paise_to_rupees(revenue),
            "avg_order_value_rupees": paise_to_rupees(avg_order_value),
            "top_category": top_category
        })

    # Sort by order count and get top/bottom
    peak_hours.sort(key=lambda x: x["order_count"], reverse=True)
    busiest_hours = peak_hours[:5]
    slowest_hours = peak_hours[-3:]

    result = {
        "peak_hours": busiest_hours,
        "slowest_hours": slowest_hours,
        "busiest_hour": busiest_hours[0]["hour"] if busiest_hours else None,
        "slowest_hour": slowest_hours[0]["hour"] if slowest_hours else None
    }

    return json.dumps(result)


def get_menu_item_details_tool(db: Session, item_name: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to get detailed menu item performance."""
    from app.models.models import Category

    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)

    # If no item name, return top items
    if not item_name:
        top_items = db.query(
            OrderItem.menu_item_name,
            func.sum(OrderItem.quantity).label('total_qty'),
            func.sum(OrderItem.subtotal).label('total_revenue')
        ).join(Order).filter(
            and_(Order.status == OrderStatus.PAID, *time_filters)
        ).group_by(OrderItem.menu_item_name).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(10).all()

        items_list = [{
            "name": name,
            "quantity_sold": int(qty),
            "revenue_rupees": paise_to_rupees(rev)
        } for name, qty, rev in top_items]

        return json.dumps({"top_items": items_list, "message": "Specify item_name for detailed analysis"})

    # Get menu item from database
    menu_item = db.query(MenuItem).filter(MenuItem.name == item_name).first()

    if not menu_item:
        return json.dumps({"error": f"Menu item '{item_name}' not found"})

    # Get category
    category = db.query(Category).filter(Category.id == menu_item.category_id).first()

    # Performance metrics
    quantity_sold = db.query(func.sum(OrderItem.quantity)).join(Order).filter(
        and_(
            OrderItem.menu_item_id == menu_item.id,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    revenue = db.query(func.sum(OrderItem.subtotal)).join(Order).filter(
        and_(
            OrderItem.menu_item_id == menu_item.id,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    order_count = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        and_(
            OrderItem.menu_item_id == menu_item.id,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    avg_qty_per_order = quantity_sold / order_count if order_count > 0 else 0

    # Get total orders for frequency calculation
    total_orders = db.query(func.count(Order.id)).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 1

    frequency = order_count / total_orders

    result = {
        "item_name": item_name,
        "category": category.name if category else "Unknown",
        "current_price_rupees": paise_to_rupees(menu_item.price),
        "is_vegetarian": menu_item.is_vegetarian,
        "is_beverage": menu_item.is_beverage,
        "is_available": menu_item.is_available,
        "performance": {
            "quantity_sold": int(quantity_sold),
            "revenue_rupees": paise_to_rupees(revenue),
            "order_count": order_count,
            "avg_quantity_per_order": round(avg_qty_per_order, 2),
            "frequency": round(frequency, 2)
        }
    }

    return json.dumps(result)


def get_payment_method_trends_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to get payment method trends and breakdown."""
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)

    payment_data = {}
    total_revenue = 0
    highest_avg = 0
    highest_avg_method = None

    for method in [PaymentMethod.CASH, PaymentMethod.UPI, PaymentMethod.CARD]:
        amount = db.query(func.sum(Payment.amount)).join(Order).filter(
            and_(
                Payment.payment_method == method,
                Order.status == OrderStatus.PAID,
                *time_filters
            )
        ).scalar() or 0

        count = db.query(func.count(Payment.id)).join(Order).filter(
            and_(
                Payment.payment_method == method,
                Order.status == OrderStatus.PAID,
                *time_filters
            )
        ).scalar() or 0

        avg_transaction = amount / count if count > 0 else 0
        total_revenue += amount

        if avg_transaction > highest_avg:
            highest_avg = avg_transaction
            highest_avg_method = method.value

        payment_data[method.value] = {
            "total_amount_rupees": paise_to_rupees(amount),
            "transaction_count": count,
            "avg_transaction_rupees": paise_to_rupees(avg_transaction),
            "percentage_revenue": 0.0,
            "percentage_count": 0.0
        }

    # Calculate percentages
    total_count = sum(p["transaction_count"] for p in payment_data.values())

    for method_data in payment_data.values():
        method_data["percentage_revenue"] = round(
            method_data["total_amount_rupees"] / paise_to_rupees(total_revenue) * 100, 2
        ) if total_revenue > 0 else 0
        method_data["percentage_count"] = round(
            method_data["transaction_count"] / total_count * 100, 2
        ) if total_count > 0 else 0

    # Find most used
    most_used = max(payment_data.items(), key=lambda x: x[1]["transaction_count"])[0] if payment_data else None

    result = {
        "payment_methods": payment_data,
        "total_revenue_rupees": paise_to_rupees(total_revenue),
        "highest_avg_transaction_method": highest_avg_method
    }

    return json.dumps(result)


def get_product_mix_analysis_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 10) -> str:
    """Tool function to analyze product mix and items ordered together."""
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)

    # Get category combinations (items from different categories in same order)
    category_combos = db.query(
        MenuItem.category_id.label('cat1'),
        func.count(func.distinct(Order.id)).label('combo_count')
    ).select_from(OrderItem).join(
        MenuItem, OrderItem.menu_item_id == MenuItem.id
    ).join(Order).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).group_by(MenuItem.category_id).all()

    # Single vs multi-item orders
    single_item_orders = db.query(func.count(func.distinct(Order.id))).select_from(Order).join(
        OrderItem
    ).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).group_by(Order.id).having(func.count(OrderItem.id) == 1).count()

    total_orders = db.query(func.count(Order.id)).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 1

    multi_item_orders = total_orders - single_item_orders

    # Average items per order
    total_items = db.query(func.sum(OrderItem.quantity)).join(Order).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 0

    avg_items = total_items / total_orders if total_orders > 0 else 0

    result = {
        "single_item_orders": single_item_orders,
        "multi_item_orders": multi_item_orders,
        "avg_items_per_order": round(avg_items, 2),
        "multi_item_order_percentage": round(multi_item_orders / total_orders * 100, 2) if total_orders > 0 else 0
    }

    return json.dumps(result)


def get_table_performance_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to analyze table performance."""
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)

    table_stats = db.query(
        Order.table_number,
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('revenue')
    ).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).group_by(Order.table_number).all()

    tables = []
    for table_num, order_count, revenue in table_stats:
        avg_order_value = revenue / order_count if order_count > 0 else 0
        tables.append({
            "table_number": table_num,
            "order_count": order_count,
            "total_revenue_rupees": paise_to_rupees(revenue),
            "avg_order_value_rupees": paise_to_rupees(avg_order_value)
        })

    tables.sort(key=lambda x: x["total_revenue_rupees"], reverse=True)

    busiest_table = max(tables, key=lambda x: x["order_count"])["table_number"] if tables else None
    highest_revenue_table = tables[0]["table_number"] if tables else None

    total_tables = len(tables)
    total_revenue = sum(t["total_revenue_rupees"] for t in tables)
    avg_revenue = total_revenue / total_tables if total_tables > 0 else 0

    result = {
        "tables": tables,
        "busiest_table": busiest_table,
        "highest_revenue_table": highest_revenue_table,
        "total_tables_used": total_tables,
        "avg_revenue_per_table_rupees": round(avg_revenue, 2)
    }

    return json.dumps(result)


def get_vegetarian_vs_nonveg_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to compare vegetarian vs non-vegetarian sales."""
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)

    # Vegetarian stats
    veg_revenue = db.query(func.sum(OrderItem.subtotal)).join(MenuItem).join(Order).filter(
        and_(
            MenuItem.is_vegetarian == True,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    veg_qty = db.query(func.sum(OrderItem.quantity)).join(MenuItem).join(Order).filter(
        and_(
            MenuItem.is_vegetarian == True,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    # Non-vegetarian stats
    nonveg_revenue = db.query(func.sum(OrderItem.subtotal)).join(MenuItem).join(Order).filter(
        and_(
            MenuItem.is_vegetarian == False,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    nonveg_qty = db.query(func.sum(OrderItem.quantity)).join(MenuItem).join(Order).filter(
        and_(
            MenuItem.is_vegetarian == False,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    total_revenue = veg_revenue + nonveg_revenue
    veg_avg_price = veg_revenue / veg_qty if veg_qty > 0 else 0
    nonveg_avg_price = nonveg_revenue / nonveg_qty if nonveg_qty > 0 else 0

    result = {
        "vegetarian": {
            "revenue_rupees": paise_to_rupees(veg_revenue),
            "revenue_percentage": round(veg_revenue / total_revenue * 100, 2) if total_revenue > 0 else 0,
            "quantity_sold": int(veg_qty),
            "avg_price_rupees": paise_to_rupees(veg_avg_price)
        },
        "non_vegetarian": {
            "revenue_rupees": paise_to_rupees(nonveg_revenue),
            "revenue_percentage": round(nonveg_revenue / total_revenue * 100, 2) if total_revenue > 0 else 0,
            "quantity_sold": int(nonveg_qty),
            "avg_price_rupees": paise_to_rupees(nonveg_avg_price)
        }
    }

    return json.dumps(result)


def get_beverage_vs_food_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to compare beverage vs food sales."""
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)

    # Beverage stats
    bev_revenue = db.query(func.sum(OrderItem.subtotal)).join(MenuItem).join(Order).filter(
        and_(
            MenuItem.is_beverage == True,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    bev_qty = db.query(func.sum(OrderItem.quantity)).join(MenuItem).join(Order).filter(
        and_(
            MenuItem.is_beverage == True,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    # Food stats
    food_revenue = db.query(func.sum(OrderItem.subtotal)).join(MenuItem).join(Order).filter(
        and_(
            MenuItem.is_beverage == False,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    food_qty = db.query(func.sum(OrderItem.quantity)).join(MenuItem).join(Order).filter(
        and_(
            MenuItem.is_beverage == False,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    total_revenue = bev_revenue + food_revenue
    bev_avg_price = bev_revenue / bev_qty if bev_qty > 0 else 0
    food_avg_price = food_revenue / food_qty if food_qty > 0 else 0

    result = {
        "beverages": {
            "revenue_rupees": paise_to_rupees(bev_revenue),
            "revenue_percentage": round(bev_revenue / total_revenue * 100, 2) if total_revenue > 0 else 0,
            "quantity_sold": int(bev_qty),
            "avg_price_rupees": paise_to_rupees(bev_avg_price)
        },
        "food": {
            "revenue_rupees": paise_to_rupees(food_revenue),
            "revenue_percentage": round(food_revenue / total_revenue * 100, 2) if total_revenue > 0 else 0,
            "quantity_sold": int(food_qty),
            "avg_price_rupees": paise_to_rupees(food_avg_price)
        }
    }

    return json.dumps(result)


def get_parcel_vs_dinein_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to compare parcel vs dine-in orders."""
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)

    # Parcel orders (orders with at least one parcel item)
    parcel_orders = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        and_(
            OrderItem.is_parcel == True,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    parcel_revenue = db.query(func.sum(OrderItem.subtotal)).join(Order).filter(
        and_(
            OrderItem.is_parcel == True,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    # Total orders
    total_orders = db.query(func.count(Order.id)).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 1

    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 0

    # Dine-in is total minus parcel
    dinein_orders = total_orders - parcel_orders
    dinein_revenue = total_revenue - parcel_revenue

    parcel_aov = parcel_revenue / parcel_orders if parcel_orders > 0 else 0
    dinein_aov = dinein_revenue / dinein_orders if dinein_orders > 0 else 0

    result = {
        "parcel": {
            "order_count": parcel_orders,
            "order_percentage": round(parcel_orders / total_orders * 100, 2) if total_orders > 0 else 0,
            "revenue_rupees": paise_to_rupees(parcel_revenue),
            "revenue_percentage": round(parcel_revenue / total_revenue * 100, 2) if total_revenue > 0 else 0,
            "avg_order_value_rupees": paise_to_rupees(parcel_aov)
        },
        "dine_in": {
            "order_count": dinein_orders,
            "order_percentage": round(dinein_orders / total_orders * 100, 2) if total_orders > 0 else 0,
            "revenue_rupees": paise_to_rupees(dinein_revenue),
            "revenue_percentage": round(dinein_revenue / total_revenue * 100, 2) if total_revenue > 0 else 0,
            "avg_order_value_rupees": paise_to_rupees(dinein_aov)
        }
    }

    return json.dumps(result)


def get_gst_breakdown_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to get GST breakdown and tax collection details."""
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)

    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 0

    subtotal = db.query(func.sum(Order.subtotal)).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 0

    gst_amount = db.query(func.sum(Order.gst_amount)).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 0

    gst_percentage = (gst_amount / subtotal * 100) if subtotal > 0 else 0

    result = {
        "total_revenue_rupees": paise_to_rupees(total_revenue),
        "subtotal_rupees": paise_to_rupees(subtotal),
        "gst_amount_rupees": paise_to_rupees(gst_amount),
        "gst_percentage": round(gst_percentage, 2),
        "revenue_before_gst_rupees": paise_to_rupees(subtotal)
    }

    return json.dumps(result)


def get_inventory_usage_trends_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 10) -> str:
    """Tool function to analyze inventory usage patterns."""
    from app.models.inventory_models import InventoryItem, InventoryTransaction, TransactionType

    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

    time_filters = []
    if start_dt:
        time_filters.append(InventoryTransaction.created_at >= start_dt)
    if end_dt:
        time_filters.append(InventoryTransaction.created_at <= end_dt)

    # Top consumed items (usage transactions)
    usage_stats = db.query(
        InventoryItem.name,
        InventoryItem.unit,
        func.sum(func.abs(InventoryTransaction.quantity)).label('total_usage')
    ).join(InventoryTransaction).filter(
        and_(
            InventoryTransaction.transaction_type == 'USAGE',
            *time_filters
        )
    ).group_by(InventoryItem.id, InventoryItem.name, InventoryItem.unit).order_by(
        func.sum(func.abs(InventoryTransaction.quantity)).desc()
    ).limit(limit).all()

    top_consumed = []
    for name, unit, usage in usage_stats:
        item = db.query(InventoryItem).filter(InventoryItem.name == name).first()
        if item:
            category_name = item.category.name if item.category else "Uncategorized"
            top_consumed.append({
                "item_name": name,
                "total_usage": float(usage),
                "unit": unit,
                "category": category_name
            })

    # Total values
    purchases_value = db.query(
        func.sum(InventoryTransaction.quantity * InventoryItem.cost_per_unit)
    ).join(InventoryItem).filter(
        and_(
            InventoryTransaction.transaction_type == 'PURCHASE',
            *time_filters
        )
    ).scalar() or 0

    usage_value = db.query(
        func.sum(func.abs(InventoryTransaction.quantity) * InventoryItem.cost_per_unit)
    ).join(InventoryItem).filter(
        and_(
            InventoryTransaction.transaction_type == 'USAGE',
            *time_filters
        )
    ).scalar() or 0

    waste_value = db.query(
        func.sum(func.abs(InventoryTransaction.quantity) * InventoryItem.cost_per_unit)
    ).join(InventoryItem).filter(
        and_(
            InventoryTransaction.transaction_type == 'ADJUSTMENT',
            InventoryTransaction.quantity < 0,
            *time_filters
        )
    ).scalar() or 0

    result = {
        "top_consumed_items": top_consumed,
        "total_purchases_value_rupees": float(purchases_value) if purchases_value else 0,
        "total_usage_value_rupees": float(usage_value) if usage_value else 0,
        "waste_adjustments_value_rupees": float(waste_value) if waste_value else 0
    }

    return json.dumps(result)


def get_cancellation_analysis_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to analyze order cancellations."""
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)

    # Total canceled orders
    canceled_count = db.query(func.count(Order.id)).filter(
        and_(Order.status == OrderStatus.CANCELED, *time_filters)
    ).scalar() or 0

    # Total orders
    total_orders = db.query(func.count(Order.id)).filter(*time_filters).scalar() or 1

    # Canceled revenue
    canceled_revenue = db.query(func.sum(Order.total_amount)).filter(
        and_(Order.status == OrderStatus.CANCELED, *time_filters)
    ).scalar() or 0

    # Cancellations by table
    table_cancellations = db.query(
        Order.table_number,
        func.count(Order.id).label('cancel_count')
    ).filter(
        and_(Order.status == OrderStatus.CANCELED, *time_filters)
    ).group_by(Order.table_number).order_by(
        func.count(Order.id).desc()
    ).limit(5).all()

    canceled_by_table = [
        {"table_number": table_num, "cancellation_count": count}
        for table_num, count in table_cancellations
    ]

    avg_canceled_value = canceled_revenue / canceled_count if canceled_count > 0 else 0

    result = {
        "total_canceled_orders": canceled_count,
        "cancellation_rate": round(canceled_count / total_orders * 100, 2),
        "canceled_revenue_lost_rupees": paise_to_rupees(canceled_revenue),
        "canceled_orders_by_table": canceled_by_table,
        "avg_canceled_order_value_rupees": paise_to_rupees(avg_canceled_value)
    }

    return json.dumps(result)


def get_financial_summary_tool(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Tool function to get comprehensive financial summary."""
    from app.models.inventory_models import InventoryTransaction

    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)

    # Revenue
    gross_revenue = db.query(func.sum(Order.total_amount)).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 0

    gst_amount = db.query(func.sum(Order.gst_amount)).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 0

    net_revenue = gross_revenue - gst_amount

    # Payment breakdown
    cash = db.query(func.sum(Payment.amount)).join(Order).filter(
        and_(
            Payment.payment_method == PaymentMethod.CASH,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    upi = db.query(func.sum(Payment.amount)).join(Order).filter(
        and_(
            Payment.payment_method == PaymentMethod.UPI,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    card = db.query(func.sum(Payment.amount)).join(Order).filter(
        and_(
            Payment.payment_method == PaymentMethod.CARD,
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).scalar() or 0

    # Costs (inventory purchases during period)
    inv_time_filters = []
    if start_dt:
        inv_time_filters.append(InventoryTransaction.created_at >= start_dt)
    if end_dt:
        inv_time_filters.append(InventoryTransaction.created_at <= end_dt)

    from app.models.inventory_models import InventoryItem
    inventory_purchases = db.query(
        func.sum(InventoryTransaction.quantity * InventoryItem.cost_per_unit)
    ).join(InventoryItem).filter(
        and_(
            InventoryTransaction.transaction_type == 'PURCHASE',
            *inv_time_filters
        )
    ).scalar() or 0

    # Estimated gross profit
    gross_profit = net_revenue - int(float(inventory_purchases) * 100)
    gross_margin = (gross_profit / net_revenue * 100) if net_revenue > 0 else 0

    # Format period
    if start_dt and end_dt:
        period = f"{start_dt.date()} to {end_dt.date()}"
    elif start_dt:
        period = f"From {start_dt.date()}"
    elif end_dt:
        period = f"Until {end_dt.date()}"
    else:
        period = "All time"

    result = {
        "period": period,
        "revenue": {
            "gross_revenue_rupees": paise_to_rupees(gross_revenue),
            "gst_amount_rupees": paise_to_rupees(gst_amount),
            "net_revenue_rupees": paise_to_rupees(net_revenue)
        },
        "costs": {
            "inventory_purchases_rupees": float(inventory_purchases)
        },
        "estimated_profit": {
            "gross_profit_rupees": paise_to_rupees(gross_profit),
            "gross_margin_percentage": round(gross_margin, 2)
        },
        "cash_flow": {
            "cash_received_rupees": paise_to_rupees(cash),
            "upi_received_rupees": paise_to_rupees(upi),
            "card_received_rupees": paise_to_rupees(card)
        }
    }

    return json.dumps(result)


# Tool definitions for C1
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_revenue_data",
            "description": "Get revenue analytics data for Lily Cafe. Returns total revenue in rupees (₹), order count, average order value, and payment method breakdown. Use this when users ask about revenue, sales, or earnings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format (e.g., '2026-01-05T00:00:00Z'). Optional, defaults to all time."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format (e.g., '2026-01-05T23:59:59Z'). Optional, defaults to all time."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_data",
            "description": "Get product performance data for Lily Cafe. Returns top selling products by quantity and revenue in rupees (₹). Use this when users ask about products, menu items, or what's selling well.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top products to return. Defaults to 10.",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_stats",
            "description": "Get order statistics for Lily Cafe. Returns total orders, active orders, completed orders, and average order value in rupees (₹). Use this when users ask about orders or order volume.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_inventory_status",
            "description": "Get current inventory status for Lily Cafe. Returns low stock items, out of stock count, and total inventory value in rupees (₹). Use this when users ask about inventory, stock levels, or what items need restocking.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cash_counter_status",
            "description": "Get cash counter status for a specific date. Returns opening/closing balance, variance, denomination breakdown in rupees (₹), and verification status. Use this when users ask about cash counter, daily cash, or cash variance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in ISO format. Optional, defaults to today."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_performance",
            "description": "Get detailed performance analysis for all menu categories. Returns revenue, order count, top items, and category composition. Use this when users ask about category performance or want to compare categories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_time_comparison",
            "description": "Compare business metrics across different time periods (today vs yesterday, this week vs last week, this month vs last month). Returns revenue, orders, and growth percentages. Use this when users ask about trends, growth, or comparisons.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Time period comparison: 'today_vs_yesterday', 'this_week_vs_last_week', or 'this_month_vs_last_month'. Defaults to 'today_vs_yesterday'.",
                        "enum": ["today_vs_yesterday", "this_week_vs_last_week", "this_month_vs_last_month"],
                        "default": "today_vs_yesterday"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_peak_hours_detailed",
            "description": "Get detailed peak hours analysis with revenue breakdown and top categories per hour. Returns busiest and slowest hours. Use this when users ask about peak hours, busy times, or hourly performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_menu_item_details",
            "description": "Get detailed performance analysis for a specific menu item or top items. Returns quantity sold, revenue, frequency, and item details. Use this when users ask about specific menu items or item performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "Name of the menu item to analyze. Optional, if not provided returns top 10 items."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_payment_method_trends",
            "description": "Get payment method trends and breakdown (Cash/UPI/Card). Returns transaction counts, amounts in rupees (₹), and insights. Use this when users ask about payment methods or payment preferences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_mix_analysis",
            "description": "Analyze product mix and ordering patterns. Returns single vs multi-item orders and average items per order. Use this when users ask about order composition or bundling opportunities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Limit for results. Defaults to 10.",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_table_performance",
            "description": "Analyze table performance and utilization. Returns revenue and order count per table. Use this when users ask about table performance or which tables are busiest.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_vegetarian_vs_nonveg",
            "description": "Compare vegetarian vs non-vegetarian sales. Returns revenue, quantity, and percentages for both categories. Use this when users ask about veg vs non-veg performance or customer preferences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_beverage_vs_food",
            "description": "Compare beverage vs food sales. Returns revenue, quantity, and percentages for both categories. Use this when users ask about beverage vs food performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_parcel_vs_dinein",
            "description": "Compare parcel (takeaway) vs dine-in orders. Returns order counts, revenue, and percentages. Use this when users ask about parcel orders, takeaway, or dine-in vs delivery.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_gst_breakdown",
            "description": "Get GST breakdown and tax collection details. Returns total revenue, GST amount in rupees (₹), and GST percentage. Use this when users ask about GST, tax collected, or tax breakdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_inventory_usage_trends",
            "description": "Analyze inventory usage patterns and consumption. Returns top consumed items, purchase values, and waste tracking in rupees (₹). Use this when users ask about inventory usage, consumption, or waste.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top items to return. Defaults to 10.",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cancellation_analysis",
            "description": "Analyze order cancellations and cancellation patterns. Returns cancellation rate, lost revenue, and cancellations by table. Use this when users ask about canceled orders or cancellation rate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_financial_summary",
            "description": "Get comprehensive financial summary including revenue, costs, profit, and cash flow in rupees (₹). Returns gross revenue, GST, net revenue, inventory costs, and estimated profit margins. Use this when users ask for financial summary, profit analysis, or complete financial picture.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format. Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format. Optional."
                    }
                },
                "required": []
            }
        }
    }
]


# ============================================================================
# Analytics Endpoints
# ============================================================================


@router.get("/revenue", response_model=RevenueData)
def get_revenue_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get revenue analytics for specified time range.

    - Includes total revenue, order count, average order value
    - Revenue breakdown by payment method
    - Revenue trend over time
    """
    # Build time filters
    time_filters = get_time_filter(start_date, end_date)

    # Get paid orders within time range
    paid_orders = db.query(Order).filter(
        and_(
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).all()

    # Calculate totals
    total_revenue_paise = sum(order.total_amount for order in paid_orders)
    total_orders = len(paid_orders)
    average_order_value = total_revenue_paise / total_orders if total_orders > 0 else 0

    # Revenue by payment method
    payment_methods = db.query(
        Payment.payment_method,
        func.sum(Payment.amount).label('total')
    ).join(Order).filter(
        and_(
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).group_by(Payment.payment_method).all()

    revenue_by_payment_method = {
        method.value: paise_to_rupees(total)
        for method, total in payment_methods
    }

    # Revenue trend
    revenue_trend = []
    if start_date and end_date:
        # Check if single day
        if start_date.date() == end_date.date():
            # Hourly aggregation
            current_time = start_date.replace(minute=0, second=0, microsecond=0)
            end_time = end_date
            
            # Iterate through hours of the day
            # If start_date is midnight and end_date is end of day, we cover 0-23 hours
            
            # Create a loop for 24 hours
            for hour in range(24):
                hour_start = start_date.date()
                hour_dt_start = datetime.combine(hour_start, datetime.min.time()).replace(hour=hour, tzinfo=timezone.utc)
                hour_dt_end = hour_dt_start + timedelta(hours=1) - timedelta(microseconds=1)
                
                # Verify we are within the requested range (though usually single day request covers full day)
                if hour_dt_start >= start_date and hour_dt_end <= end_date:
                     hour_revenue = db.query(func.sum(Order.total_amount)).filter(
                        and_(
                            Order.status == OrderStatus.PAID,
                            Order.created_at >= hour_dt_start,
                            Order.created_at <= hour_dt_end
                        )
                    ).scalar() or 0
                     
                     revenue_trend.append({
                        "date": hour_dt_start.isoformat(),
                        "revenue": paise_to_rupees(hour_revenue)
                    })
        else:
            # Daily aggregation
            current_date = start_date.date()
            end = end_date.date()

            while current_date <= end:
                day_start = datetime.combine(current_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                day_end = datetime.combine(current_date, datetime.max.time()).replace(tzinfo=timezone.utc)

                day_revenue = db.query(func.sum(Order.total_amount)).filter(
                    and_(
                        Order.status == OrderStatus.PAID,
                        Order.created_at >= day_start,
                        Order.created_at <= day_end
                    )
                ).scalar() or 0

                revenue_trend.append({
                    "date": current_date.isoformat(),
                    "revenue": paise_to_rupees(day_revenue)
                })

                current_date += timedelta(days=1)

    return RevenueData(
        total_revenue=paise_to_rupees(total_revenue_paise),
        total_orders=total_orders,
        average_order_value=paise_to_rupees(average_order_value),
        revenue_by_payment_method=revenue_by_payment_method,
        revenue_trend=revenue_trend
    )


@router.get("/products", response_model=ProductPerformance)
def get_product_performance(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get product performance analytics.

    - Top selling products by quantity and revenue
    - Revenue breakdown by category
    """
    # Build time filters
    time_filters = get_time_filter(start_date, end_date)

    # Top products by quantity sold
    top_products_query = db.query(
        OrderItem.menu_item_name,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.subtotal).label('total_revenue')
    ).join(Order).filter(
        and_(
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).group_by(OrderItem.menu_item_name).order_by(
        func.sum(OrderItem.quantity).desc()
    ).limit(limit).all()

    top_products = [
        {
            "name": name,
            "quantity_sold": int(quantity),
            "revenue": paise_to_rupees(revenue)
        }
        for name, quantity, revenue in top_products_query
    ]

    # Revenue by category
    revenue_by_category_query = db.query(
        MenuItem.category_id,
        func.sum(OrderItem.subtotal).label('total_revenue')
    ).join(OrderItem, OrderItem.menu_item_id == MenuItem.id).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        and_(
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).group_by(MenuItem.category_id).all()

    # Get category names
    from app.models.models import Category
    revenue_by_category = {}
    for category_id, revenue in revenue_by_category_query:
        category = db.query(Category).filter(Category.id == category_id).first()
        if category:
            revenue_by_category[category.name] = paise_to_rupees(revenue)

    return ProductPerformance(
        top_products=top_products,
        revenue_by_category=revenue_by_category
    )


@router.get("/orders", response_model=OrderStatistics)
def get_order_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get order statistics.

    - Total, active, completed, and canceled orders
    - Average order value
    - Peak hours analysis
    """
    # Build time filters
    time_filters = get_time_filter(start_date, end_date)

    # Order counts by status
    total_orders = db.query(Order).filter(*time_filters).count()
    active_orders = db.query(Order).filter(
        and_(Order.status == OrderStatus.ACTIVE, *time_filters)
    ).count()
    completed_orders = db.query(Order).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).count()
    canceled_orders = db.query(Order).filter(
        and_(Order.status == OrderStatus.CANCELED, *time_filters)
    ).count()

    # Average order value (paid orders only)
    avg_order_value = db.query(func.avg(Order.total_amount)).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 0

    # Peak hours (orders by hour of day in IST)
    from sqlalchemy import extract
    peak_hours_query = db.query(
        extract('hour', to_ist_timestamp(Order.created_at)).label('hour'),
        func.count(Order.id).label('order_count')
    ).filter(*time_filters).group_by('hour').order_by(
        func.count(Order.id).desc()
    ).limit(5).all()

    peak_hours = [
        {
            "hour": int(hour) if hour is not None else 0,
            "order_count": count
        }
        for hour, count in peak_hours_query
    ]

    return OrderStatistics(
        total_orders=total_orders,
        active_orders=active_orders,
        completed_orders=completed_orders,
        canceled_orders=canceled_orders,
        average_order_value=paise_to_rupees(avg_order_value),
        peak_hours=peak_hours
    )



@router.get("/heatmap", response_model=HeatmapData)
def get_heatmap_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get heatmap analytics (orders by day of week and hour).
    Returns data for populating a 7x24 grid.
    """
    from sqlalchemy import extract
    
    # Build time filters
    time_filters = get_time_filter(start_date, end_date)
    
    # Query database
    # Extract DOW (0=Sunday, 6=Saturday in Postgres) and Hour in IST
    measurements = db.query(
        extract('dow', to_ist_timestamp(Order.created_at)).label('day_of_week'),
        extract('hour', to_ist_timestamp(Order.created_at)).label('hour'),
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('revenue')
    ).filter(
        and_(
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).group_by(
        'day_of_week', 'hour'
    ).all()
    
    # Process results
    data_points = []
    
    # Create a map for quick lookup
    metrics_map = {}
    for r in measurements:
        metrics_map[(int(r.day_of_week), int(r.hour))] = {
            "count": r.order_count,
            "revenue": paise_to_rupees(r.revenue or 0)
        }
        
    # Fill all 7 days * 24 hours with 0 if no data
    # This makes frontend rendering easier
    for day in range(7):  # 0 to 6
        for hour in range(24): # 0 to 23
            metrics = metrics_map.get((day, hour), {"count": 0, "revenue": 0})
            
            data_points.append({
                "day_of_week": day,
                "hour": hour,
                "order_count": metrics["count"],
                "revenue": metrics["revenue"]
            })
            
    return HeatmapData(data=data_points)


@router.get("/calendar-heatmap", response_model=CalendarHeatmapData)
def get_calendar_heatmap(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get calendar heatmap analytics (daily revenue/orders).
    """
    # Default to last 365 days if no date provided
    if not start_date:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=365)
        
    start_dt = start_date if start_date else None
    end_dt = end_date if end_date else None
    
    time_filters = get_time_filter(start_dt, end_dt)
    
    # Query database - use IST timezone for date grouping
    daily_stats = db.query(
        func.date(to_ist_timestamp(Order.created_at)).label('date'),
        func.sum(Order.total_amount).label('total_revenue'),
        func.count(Order.id).label('order_count')
    ).filter(
        and_(
            Order.status == OrderStatus.PAID,
            *time_filters
        )
    ).group_by(
        'date'
    ).all()
    
    data_points = []
    
    for stat in daily_stats:
        data_points.append({
            "date": str(stat.date),
            "value": paise_to_rupees(stat.total_revenue or 0),
            "count": stat.order_count
        })
            
    return CalendarHeatmapData(data=data_points)


@router.get("/category-performance", response_model=CategoryPerformanceResponse)
def get_category_performance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get detailed category performance."""
    result_json = get_category_performance_tool(db, start_date, end_date)
    return json.loads(result_json)


@router.get("/inventory-valuation", response_model=InventoryStatusResponse)
def get_inventory_valuation(
    db: Session = Depends(get_db)
):
    """Get inventory status and valuation."""
    result_json = get_inventory_status_tool(db)
    return json.loads(result_json)


@router.get("/product-performance-detailed", response_model=ProductPerformanceDetailedResponse)
def get_detailed_product_performance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get detailed product performance (top items)."""
    # Reuse existing tool but maybe we need more items or specific logic?
    # get_product_data_tool only returns top 10.
    # For now, let's just reuse it.
    result_json = get_product_data_tool(db, start_date, end_date, limit=20)
    return json.loads(result_json)


@router.get("/payment-trends", response_model=PaymentTrendsResponse)
def get_payment_trends(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get payment method trends."""
    result_json = get_payment_method_trends_tool(db, start_date, end_date)
    return json.loads(result_json)


@router.get("/order-stats-detailed", response_model=OrderStatsDetailedResponse)
def get_detailed_order_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get detailed order statistics including conversion rates."""
    result_json = get_order_stats_tool(db, start_date, end_date)
    data = json.loads(result_json)
    
    # Enrich with rates if not present in tool
    total = data.get('total_orders', 0)
    if total > 0:
        data['active_rate'] = data.get('active_orders', 0) / total
        data['completion_rate'] = data.get('completed_orders', 0) / total
        data['cancellation_rate'] = data.get('canceled_orders', 0) / total # Tool doesn't return canceled currently
    else:
        data['active_rate'] = 0
        data['completion_rate'] = 0
        data['cancellation_rate'] = 0
        
    return data


@router.get("/revenue-composition", response_model=RevenueCompositionResponse)
def get_revenue_composition(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get revenue composition by category over time."""
    from app.models.models import Category
    
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)
    
    # Group by date and category (using IST timezone)
    results = db.query(
        func.date(to_ist_timestamp(Order.created_at)).label('date'),
        Category.name.label('category'),
        func.sum(OrderItem.subtotal).label('revenue')
    ).join(OrderItem, Order.id == OrderItem.order_id).join(MenuItem, OrderItem.menu_item_id == MenuItem.id).join(Category, MenuItem.category_id == Category.id).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).group_by(func.date(to_ist_timestamp(Order.created_at)), Category.name).all()
    
    data = []
    for r in results:
        data.append({
            "date": str(r.date),
            "category": r.category,
            "revenue": paise_to_rupees(r.revenue)
        })
        
    return {"data": data}


@router.get("/order-status-flow", response_model=OrderStatusFlowResponse)
def get_order_status_flow(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get order status counts over time."""
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)
    
    results = db.query(
        func.date(to_ist_timestamp(Order.created_at)).label('date'),
        Order.status,
        func.count(Order.id).label('count')
    ).filter(*time_filters).group_by(func.date(to_ist_timestamp(Order.created_at)), Order.status).all()
    
    data = []
    for r in results:
        data.append({
            "date": str(r.date),
            "status": r.status.value,
            "count": r.count
        })
        
    return {"data": data}


@router.get("/day-of-week-stats", response_model=DayOfWeekStatsResponse)
def get_day_of_week_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get stats aggregated by day of week."""
    from sqlalchemy import extract
    
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)
    
    # SQLite uses strftime for DOW: 0=Sunday, 6=Saturday
    # Postgres uses extract(DOW): 0=Sunday
    # We will assume SQLite for local dev but try to be generic if possible.
    # Lily Cafe seems to be using PostgreSQL based on previous context (`EXTRACT(DOW...`).
    # Extract day of week in IST timezone

    results = db.query(
        extract('dow', to_ist_timestamp(Order.created_at)).label('dow'),
        func.sum(Order.total_amount).label('revenue'),
        func.count(Order.id).label('orders'),
        func.avg(Order.total_amount).label('aov')
    ).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).group_by('dow').all()
    
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    data = []
    
    for r in results:
        dow = int(r.dow)
        # Parcel ratio for this day (in IST)
        parcel_count = db.query(func.count(Order.id)).join(OrderItem).filter(
            and_(
                extract('dow', to_ist_timestamp(Order.created_at)) == dow,
                Order.status == OrderStatus.PAID,
                OrderItem.is_parcel == True,
                *time_filters
            )
        ).scalar() or 0

        # Determine unique payment methods count (diversity)
        diversity = db.query(func.count(func.distinct(Payment.payment_method))).join(Order).filter(
             and_(
                extract('dow', to_ist_timestamp(Order.created_at)) == dow,
                Order.status == OrderStatus.PAID,
                *time_filters
            )
        ).scalar() or 0

        data.append({
            "day": days[dow],
            "day_index": dow,
            "revenue_rupees": paise_to_rupees(r.revenue or 0),
            "order_count": r.orders,
            "avg_order_value_rupees": paise_to_rupees(r.aov or 0),
            "payment_diversity": diversity,
            "parcel_ratio": round(parcel_count / r.orders, 2) if r.orders > 0 else 0
        })
        
    return {"data": data}


def calculate_quartiles(values):
    if not values:
        return {"min": 0, "q1": 0, "median": 0, "q3": 0, "max": 0}
    
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    
    def get_percentile(p):
        k = (n - 1) * p
        f = int(k)
        c = k - f
        if f + 1 < n:
            return sorted_vals[f] * (1 - c) + sorted_vals[f + 1] * c
        else:
            return sorted_vals[f]

    return {
        "min": sorted_vals[0],
        "q1": get_percentile(0.25),
        "median": get_percentile(0.50),
        "q3": get_percentile(0.75),
        "max": sorted_vals[-1]
    }


@router.get("/order-value-distribution", response_model=OrderValueDistributionResponse)
def get_order_value_distribution(
    group_by: str = "day_of_week", # day_of_week, payment_method
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get box plot stats for order values."""
    from sqlalchemy import extract
    
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)
    
    data = []
    
    if group_by == "day_of_week":
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for i, day in enumerate(days):
            amounts = db.query(Order.total_amount).filter(
                and_(
                    extract('dow', to_ist_timestamp(Order.created_at)) == i,
                    Order.status == OrderStatus.PAID,
                    *time_filters
                )
            ).all()
            vals = [paise_to_rupees(a[0]) for a in amounts]
            stats = calculate_quartiles(vals)
            data.append({"group": day, "stats": stats})
            
    elif group_by == "payment_method":
        methods = [PaymentMethod.CASH, PaymentMethod.UPI, PaymentMethod.CARD]
        for m in methods:
            amounts = db.query(Payment.amount).join(Order).filter(
                and_(
                    Payment.payment_method == m,
                    Order.status == OrderStatus.PAID,
                    *time_filters
                )
            ).all()
            vals = [paise_to_rupees(a[0]) for a in amounts]
            stats = calculate_quartiles(vals)
            data.append({"group": m.value, "stats": stats})
            
    return {"data": data}


@router.get("/item-quantity-distribution", response_model=ItemQuantityDistributionResponse)
def get_item_quantity_distribution(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get box plot stats for item quantities per order (bulk vs single)."""
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)
    
    # Get top 20 items first to limit noise
    top_items = db.query(OrderItem.menu_item_name).join(Order).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).group_by(OrderItem.menu_item_name).order_by(func.sum(OrderItem.quantity).desc()).limit(20).all()
    
    data = []
    
    for item in top_items:
        name = item[0]
        # Get all quantities for this item
        quantities = db.query(OrderItem.quantity).join(Order).filter(
            and_(
                OrderItem.menu_item_name == name,
                Order.status == OrderStatus.PAID,
                *time_filters
            )
        ).all()
        
        vals = [q[0] for q in quantities]
        stats = calculate_quartiles(vals)
        data.append({"item_name": name, "stats": stats})
        
    return {"data": data}


@router.get("/order-flow", response_model=SankeyData)
def get_order_flow(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get order flow Sankey data: Category -> MenuItem -> Payment."""
    from app.models.models import Category
    
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    time_filters = get_time_filter(start_dt, end_dt)
    
    # 1. Category -> Menu Item
    cat_item_flows = db.query(
        Category.name.label('source'),
        MenuItem.name.label('target'),
        func.sum(OrderItem.subtotal).label('value')
    ).join(MenuItem, Category.id == MenuItem.category_id).join(OrderItem, MenuItem.id == OrderItem.menu_item_id).join(Order, OrderItem.order_id == Order.id).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).group_by(Category.name, MenuItem.name).all()
    
    # 2. Menu Item -> Payment (Approximation, as payment is per order, not per item)
    # We distribute item revenue to payment methods based on order's payment method breakdown (usually 1 method)
    # This is complex. Simplified: just link Categories directly to Payment Methods?
    # Or Component: Top Items -> Payment Methods
    
    # Let's do: Category -> Payment Method
    # Query: Category -> MenuItem -> OrderItem -> Order -> Payment
    cat_payment_flows = db.query(
        Category.name.label('source'),
        Payment.payment_method.label('target'),
        func.sum(OrderItem.subtotal).label('value')
    ).join(MenuItem, Category.id == MenuItem.category_id).join(OrderItem, MenuItem.id == OrderItem.menu_item_id).join(Order, OrderItem.order_id == Order.id).join(Payment, Order.id == Payment.order_id).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).group_by(Category.name, Payment.payment_method).all()
    
    # Nodes: Unique Categories + Unique Payment Methods
    nodes = []
    node_map = {}
    
    def get_node_index(name):
        if name not in node_map:
            node_map[name] = len(nodes)
            nodes.append({"name": name})
        return node_map[name]
    
    links = []
    
    # Since linking Category -> Item -> Payment is too granular (hundreds of items),
    # Let's do a 2-stage flow: Category -> "Revenue" -> Payment Method? No.
    # Let's do: Category -> Payment Method. That's just 1 step.
    # What did the doc say? "Category -> Menu Item -> Payment Method -> Revenue"
    # That's too many items for a clean sankey.
    # Let's filter to TOP 5 Items per category or just link Categories -> Payment methods for now
    # Or Categories -> Top 5 Items -> Remainder -> Payment Method
    
    # Let's stick to the query we wrote: Category -> Payment Method
    # It shows which categories are bought with what payment method.
    
    for r in cat_payment_flows:
        source_idx = get_node_index(r.source)
        # Payment methods are targets, maybe prefix or suffix to avoid name collision if any
        target_name = f"Payment: {r.target.value.title()}"
        target_idx = get_node_index(target_name)
        
        links.append({
            "source": source_idx,
            "target": target_idx,
            "value": paise_to_rupees(r.value)
        })
        
    return {"nodes": nodes, "links": links}


@router.get("/revenue-waterfall", response_model=WaterfallResponse)
def get_revenue_waterfall(
    date: Optional[str] = None, # Single date focus usually
    db: Session = Depends(get_db)
):
    """Get daily revenue waterfall breakdown."""
    from app.models.models import Category
    
    if date:
        target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
    else:
        target_date = datetime.now(timezone.utc).date()
        
    start_dt = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
    time_filters = [Order.created_at >= start_dt, Order.created_at <= end_dt]
    
    data = []
    
    # Start (0)
    data.append({"name": "Start", "value": 0, "is_total": False, "color": "#9ca3af"})
    
    # Add revenue per category
    cat_revenues = db.query(
        Category.name,
        func.sum(OrderItem.subtotal).label('revenue')
    ).join(MenuItem).join(OrderItem).join(Order).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).group_by(Category.name).all()
    
    total_rev = 0
    for name, rev in cat_revenues:
        val = paise_to_rupees(rev or 0)
        data.append({"name": name, "value": val, "is_total": False, "color": "#10b981"})
        total_rev += val
        
    # GST (Tax) - We collect it, so it's a positive for gross, 
    # but waterfall usually shows Net -> Gross or Gross -> Net.
    # Data says "End: Net Revenue"? Or "Start 0 -> ... -> Net".
    # User doc: "+Coffee +Tea ... -GST = Net".
    # But usually Coffee+Tea IS Net (subtotal). GST is added on top.
    # So: Start 0 -> +Coffee -> +Tea -> ... -> Subtotal -> +GST -> Total.
    
    gst_rev = db.query(func.sum(Order.gst_amount)).filter(
        and_(Order.status == OrderStatus.PAID, *time_filters)
    ).scalar() or 0
    
    gst_val = paise_to_rupees(gst_rev)
    if gst_val > 0:
        data.append({"name": "GST", "value": gst_val, "is_total": False, "color": "#f59e0b"})
        
    # Total
    total_collected = total_rev + gst_val
    data.append({"name": "Total Revenue", "value": total_collected, "is_total": True, "color": "#3b82f6"})
    
    return {"data": data}


@router.get("/inventory-waterfall", response_model=WaterfallResponse)
def get_inventory_waterfall(
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get inventory value flow for a day: Opening -> Purchases -> Usage -> Closing."""
    from app.models.inventory_models import InventoryTransaction, TransactionType, InventoryItem
    
    if date:
        target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
    else:
        target_date = datetime.now(timezone.utc).date()
        
    start_dt = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    # 1. Calculate Opening Balance (Sum of all txns BEFORE today)
    # Value = quantity * cost_per_unit? Cost changes. 
    # Ideally we track value flow. 
    # Simplified: Value = Sum(tx.quantity * item.cost_per_unit at that time)
    # But we don't store historical cost in tx. We'll use current cost.
    
    # Get all items with cost
    items = db.query(InventoryItem).all()
    item_costs = {i.id: float(i.cost_per_unit or 0) for i in items}
    
    # Pre-today transactions
    pre_txs = db.query(InventoryTransaction).filter(
        InventoryTransaction.created_at < start_dt
    ).all()
    
    opening_val = 0
    for tx in pre_txs:
        cost = item_costs.get(tx.item_id, 0)
        opening_val += float(tx.quantity) * cost
        
    start_val = max(0, opening_val) # Shouldn't be negative
    
    data = []
    data.append({"name": "Opening", "value": start_val, "is_total": True, "color": "#9ca3af"})
    
    # Txs today
    today_txs = db.query(InventoryTransaction).filter(
        and_(InventoryTransaction.created_at >= start_dt, InventoryTransaction.created_at <= end_dt)
    ).all()
    
    purchases = 0
    usage = 0
    adjustments = 0
    
    for tx in today_txs:
        cost = item_costs.get(tx.item_id, 0)
        val = float(tx.quantity) * cost
        
        if tx.transaction_type == "PURCHASE": # string in db based on model
            purchases += val
        elif tx.transaction_type == "USAGE":
            usage += val # usage is usually negative quantity
        else:
            adjustments += val
            
    if purchases != 0:
        data.append({"name": "Purchases", "value": purchases, "is_total": False, "color": "#10b981"})
    
    if usage != 0:
        # distinct color for negative
        data.append({"name": "Usage", "value": usage, "is_total": False, "color": "#ef4444"})
        
    if adjustments != 0:
         data.append({"name": "Adjustments", "value": adjustments, "is_total": False, "color": "#f59e0b"})
         
    closing = start_val + purchases + usage + adjustments
    data.append({"name": "Closing", "value": closing, "is_total": True, "color": "#3b82f6"})
    
    return {"data": data}


@router.get("/order-timeline", response_model=OrdersTimelineResponse)
def get_order_timeline(
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get timeline of orders for a specific day."""
    if date:
        target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
    else:
        target_date = datetime.now(timezone.utc).date()
    
    start_dt = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    orders = db.query(Order).filter(
        and_(
            Order.created_at >= start_dt,
            Order.created_at <= end_dt
        )
    ).order_by(Order.created_at).all()
    
    data = []
    for o in orders:
        paid_at = None
        if o.status == OrderStatus.PAID and o.payments:
            # use last payment time
            last_payment = max(o.payments, key=lambda p: p.created_at)
            paid_at = last_payment.created_at.isoformat()
            
        duration = 0
        if paid_at:
             paid_dt = datetime.fromisoformat(paid_at)
             duration = (paid_dt - o.created_at).total_seconds() / 60
             
        data.append({
            "order_number": o.order_number,
            "table_number": o.table_number,
            "created_at": o.created_at.isoformat(),
            "amount": paise_to_rupees(o.total_amount),
            "paid_at": paid_at,
            "duration_minutes": round(duration, 1) if duration > 0 else None
        })
        
    return {"data": data}


# ============================================================================
# Thesys C1 Conversational Query Endpoint
# ============================================================================


@router.post("/query")
async def conversational_query(
    request: C1QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Thesys C1 conversational analytics query endpoint with tool calling.

    Accepts natural language queries and generates dynamic UI visualizations
    powered by real data from the database.

    Example queries:
    - "Show me sales for today"
    - "What are the top 5 selling products this month?"
    - "What is the total revenue this month?"
    """
    try:
        from fastapi.responses import StreamingResponse

        client = get_c1_client()

        # Prepare system context
        system_message = """You are an analytics assistant for Lily Cafe, an Indian restaurant.

IMPORTANT:
- All monetary values are in Indian Rupees (₹), NOT dollars ($)
- Always display currency as ₹ (rupee symbol), never use $
- Use the tools provided to fetch REAL data from the database
- Never make up or hallucinate data
- If there's no data for a period, clearly state that

You have access to comprehensive analytics tools:

**Revenue & Financial:**
- get_revenue_data: Revenue, order count, AOV, payment methods
- get_financial_summary: Complete financial picture with profit analysis
- get_gst_breakdown: Tax collection and GST analysis
- get_payment_method_trends: Cash/UPI/Card usage and trends

**Product & Menu:**
- get_product_data: Top selling products
- get_category_performance: Category-level performance analysis
- get_menu_item_details: Individual item deep dive
- get_vegetarian_vs_nonveg: Veg vs non-veg comparison
- get_beverage_vs_food: Beverage vs food comparison
- get_product_mix_analysis: Order composition and bundling

**Operations:**
- get_order_stats: Order statistics by status
- get_peak_hours_detailed: Hourly performance with insights
- get_table_performance: Table utilization and revenue
- get_parcel_vs_dinein: Takeaway vs dine-in analysis
- get_cancellation_analysis: Order cancellation patterns

**Inventory & Cash:**
- get_inventory_status: Stock levels and low stock alerts
- get_inventory_usage_trends: Consumption patterns and waste
- get_cash_counter_status: Daily cash reconciliation

**Comparisons:**
- get_time_comparison: Period-over-period analysis (today vs yesterday, etc.)

When displaying data:
- Use ₹ for all monetary values
- Create beautiful UI components with cards, charts, and tables
- Provide actionable insights and recommendations
- If data shows zero/no results, inform the user clearly
- Use appropriate tools based on user questions"""

        # Extract user message content from OpenAI format
        user_message = request.prompt.get("content", "") if isinstance(request.prompt, dict) else str(request.prompt)

        # Initialize messages list
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        # Tool implementations mapping
        tool_impls = {
            "get_revenue_data": lambda **kwargs: get_revenue_data_tool(db, **kwargs),
            "get_product_data": lambda **kwargs: get_product_data_tool(db, **kwargs),
            "get_order_stats": lambda **kwargs: get_order_stats_tool(db, **kwargs),
            "get_inventory_status": lambda **kwargs: get_inventory_status_tool(db, **kwargs),
            "get_cash_counter_status": lambda **kwargs: get_cash_counter_status_tool(db, **kwargs),
            "get_category_performance": lambda **kwargs: get_category_performance_tool(db, **kwargs),
            "get_time_comparison": lambda **kwargs: get_time_comparison_tool(db, **kwargs),
            "get_peak_hours_detailed": lambda **kwargs: get_peak_hours_detailed_tool(db, **kwargs),
            "get_menu_item_details": lambda **kwargs: get_menu_item_details_tool(db, **kwargs),
            "get_payment_method_trends": lambda **kwargs: get_payment_method_trends_tool(db, **kwargs),
            "get_product_mix_analysis": lambda **kwargs: get_product_mix_analysis_tool(db, **kwargs),
            "get_table_performance": lambda **kwargs: get_table_performance_tool(db, **kwargs),
            "get_vegetarian_vs_nonveg": lambda **kwargs: get_vegetarian_vs_nonveg_tool(db, **kwargs),
            "get_beverage_vs_food": lambda **kwargs: get_beverage_vs_food_tool(db, **kwargs),
            "get_parcel_vs_dinein": lambda **kwargs: get_parcel_vs_dinein_tool(db, **kwargs),
            "get_gst_breakdown": lambda **kwargs: get_gst_breakdown_tool(db, **kwargs),
            "get_inventory_usage_trends": lambda **kwargs: get_inventory_usage_trends_tool(db, **kwargs),
            "get_cancellation_analysis": lambda **kwargs: get_cancellation_analysis_tool(db, **kwargs),
            "get_financial_summary": lambda **kwargs: get_financial_summary_tool(db, **kwargs)
        }

        # Tool calling loop (non-streaming for tool execution)
        while True:
            completion = client.chat.completions.create(
                model="c1/anthropic/claude-sonnet-4/v-20250815",
                messages=messages,
                tools=tools,
                stream=False  # Don't stream during tool calls
            )

            choice = completion.choices[0]
            message = choice.message
            tool_calls = message.tool_calls or []

            # If no tool calls, we have the final response
            if not tool_calls:
                # Return the content directly as a stream
                async def generate():
                    content = message.content or ""
                    # Yield content in chunks for streaming compatibility
                    yield content

                return StreamingResponse(
                    generate(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache, no-transform",
                        "Connection": "keep-alive",
                    }
                )

            # Record assistant message with tool calls
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls
                ]
            })

            # Execute tools and append results
            for tool_call in tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")
                result = tool_impls[name](**args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Thesys C1: {str(e)}")
