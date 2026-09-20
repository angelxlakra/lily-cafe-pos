"""
Analytics endpoints for Lily Cafe POS System.
Provides revenue, product, and order statistics.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel

from app.api.deps import get_db, get_current_owner, get_current_user
from app.core import access, business_day
from app.models.models import Order, OrderItem, Payment, PaymentMethod, OrderStatus, MenuItem
from app import schemas
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
from app.schemas.analytics_schemas import (
    TimeRange,
    RevenueData,
    ProductPerformance,
    OrderStatistics,
    HeatmapPoint,
    HeatmapData,
    CalendarHeatmapPoint,
    CalendarHeatmapData,
)
from app.crud.crud_analytics import (
    get_product_data_tool,
    get_order_stats_tool,
    get_inventory_status_tool,
    get_category_performance_tool,
    get_payment_method_trends_tool,
    to_ist_timestamp,
    get_time_filter,
    paise_to_rupees,
    calculate_quartiles
)

router = APIRouter()


# ============================================================================
# Analytics Endpoints
# ============================================================================


@router.get("/revenue", response_model=RevenueData)
def get_revenue_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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


# ============================================================
# Dish Frequency ("Tools" page) - how many times each dish was
# ordered within a date interval, optionally filtered to a set
# of dishes, sorted in descending order of quantity.
# ============================================================

class DishCountRow(BaseModel):
    menu_item_id: Optional[int] = None
    name: str
    quantity: int          # total plates/units served (sum of OrderItem.quantity)
    times_ordered: int     # number of distinct orders containing this dish


class DishFrequencyResponse(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    paid_only: bool
    rows: List[DishCountRow]


def _ist_day_to_utc_bounds(start: Optional[str], end: Optional[str]):
    """Interpret start/end as local business days (YYYY-MM-DD, in the
    configured timezone) and return naive-UTC datetime bounds suitable for
    comparing against Order.created_at. Either bound may be None
    (open-ended). Uses app.core.business_day so analytics and order
    filtering agree on what a day is."""
    from datetime import date as _date

    start_dt = None
    end_dt = None
    if start:
        start_dt, _ = business_day.business_day_utc_bounds(_date.fromisoformat(start))
    if end:
        _, end_exclusive = business_day.business_day_utc_bounds(_date.fromisoformat(end))
        end_dt = end_exclusive - timedelta(microseconds=1)
    return start_dt, end_dt


@router.get("/dish-frequency", response_model=DishFrequencyResponse)
def get_dish_frequency(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    menu_item_ids: Optional[List[int]] = Query(default=None),
    paid_only: bool = False,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_user),
):
    """
    Count how many times each dish was ordered within a date interval.

    - **start_date / end_date**: IST calendar days (YYYY-MM-DD), inclusive. Omit for all-time.
    - **menu_item_ids**: optional list of dish ids to restrict to. Selected dishes
      with no orders in the interval are returned with a count of 0.
    - **paid_only**: when true, count only paid orders; otherwise count all
      orders except canceled ones.

    Rows are sorted in descending order of total quantity.
    """

    # Same role rule as order history: the admin login sees today only, so the
    # dish report cannot be used to read what was sold on a previous day.
    start_date, end_date = access.restrict_history_range(
        current_user, start_date, end_date
    )
    try:
        start_dt, end_dt = _ist_day_to_utc_bounds(start_date, end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in YYYY-MM-DD format")

    filters = []
    if start_dt is not None:
        filters.append(Order.created_at >= start_dt)
    if end_dt is not None:
        filters.append(Order.created_at <= end_dt)

    if paid_only:
        filters.append(Order.status == OrderStatus.PAID)
    else:
        filters.append(Order.status != OrderStatus.CANCELED)

    if menu_item_ids:
        filters.append(OrderItem.menu_item_id.in_(menu_item_ids))

    rows_query = (
        db.query(
            OrderItem.menu_item_id.label("menu_item_id"),
            OrderItem.menu_item_name.label("name"),
            func.sum(OrderItem.quantity).label("quantity"),
            func.count(func.distinct(OrderItem.order_id)).label("times_ordered"),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .filter(and_(*filters))
        .group_by(OrderItem.menu_item_id, OrderItem.menu_item_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .all()
    )

    rows = [
        DishCountRow(
            menu_item_id=menu_item_id,
            name=name,
            quantity=int(quantity or 0),
            times_ordered=int(times_ordered or 0),
        )
        for menu_item_id, name, quantity, times_ordered in rows_query
    ]

    # Include explicitly-selected dishes that had no orders, as zero rows.
    if menu_item_ids:
        present_ids = {r.menu_item_id for r in rows}
        missing_ids = [i for i in menu_item_ids if i not in present_ids]
        if missing_ids:
            missing_items = (
                db.query(MenuItem.id, MenuItem.name)
                .filter(MenuItem.id.in_(missing_ids))
                .all()
            )
            for item_id, name in missing_items:
                rows.append(
                    DishCountRow(menu_item_id=item_id, name=name, quantity=0, times_ordered=0)
                )

    return DishFrequencyResponse(
        start_date=start_date,
        end_date=end_date,
        paid_only=paid_only,
        rows=rows,
    )


@router.get("/orders", response_model=OrderStatistics)
def get_order_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
):
    """Get detailed category performance."""
    result_json = get_category_performance_tool(db, start_date, end_date)
    return json.loads(result_json)


@router.get("/inventory-valuation", response_model=InventoryStatusResponse)
def get_inventory_valuation(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
):
    """Get inventory status and valuation."""
    result_json = get_inventory_status_tool(db)
    return json.loads(result_json)


@router.get("/product-performance-detailed", response_model=ProductPerformanceDetailedResponse)
def get_detailed_product_performance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
):
    """Get payment method trends."""
    result_json = get_payment_method_trends_tool(db, start_date, end_date)
    return json.loads(result_json)


@router.get("/order-stats-detailed", response_model=OrderStatsDetailedResponse)
def get_detailed_order_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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




@router.get("/order-value-distribution", response_model=OrderValueDistributionResponse)
def get_order_value_distribution(
    group_by: str = "day_of_week", # day_of_week, payment_method
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
