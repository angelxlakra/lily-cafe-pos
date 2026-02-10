from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import json
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text, extract

from app.core.config import settings
from app.models.models import Order, OrderItem, Payment, PaymentMethod, OrderStatus, MenuItem, Category
from app.models.inventory_models import InventoryItem, InventoryCategory, InventoryTransaction, TransactionType
from app.models.cash_models import DailyCashCounter


# ============================================================================
# Helper Functions
# ============================================================================


def to_ist_timestamp(column):
    """
    Convert a UTC timestamp column to IST (Asia/Kolkata) timezone.
    Returns a SQLAlchemy expression for use in queries.

    Usage: extract('hour', to_ist_timestamp(Order.created_at))

    Supports both PostgreSQL and SQLite.
    """
    # IST is UTC+5:30, which is +330 minutes
    # For SQLite, use datetime function with timezone offset
    # For PostgreSQL, use AT TIME ZONE
    # Since we're using SQLite in development, we'll use SQLite syntax
    return text(f"datetime({column.key}, '+330 minutes')")


def get_time_filter(start_date: Optional[datetime], end_date: Optional[datetime]):
    """Create time filter for queries."""
    filters = []

    if start_date:
        filters.append(Order.created_at >= start_date)
    if end_date:
        filters.append(Order.created_at <= end_date)

    return filters


def paise_to_rupees(paise: int) -> float:
    """Pass through paise as is (for frontend formatting)."""
    return float(paise)


def calculate_quartiles(values):
    """Calculate quartiles for box plots."""
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
