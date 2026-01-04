"""
Analytics endpoints for Lily Cafe POS System.
Provides revenue, product, and order statistics with Thesys C1 generative UI integration.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel
from openai import OpenAI

from app.api.deps import get_db
from app.core.config import settings
from app.models.models import Order, OrderItem, Payment, PaymentMethod, OrderStatus, MenuItem

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


class C1QueryRequest(BaseModel):
    """Request for Thesys C1 conversational query."""
    prompt: str
    c1_response: Optional[str] = ""


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

    # Revenue trend (daily aggregation)
    revenue_trend = []
    if start_date and end_date:
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

    # Peak hours (orders by hour of day)
    from sqlalchemy import extract
    peak_hours_query = db.query(
        extract('hour', Order.created_at).label('hour'),
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


# ============================================================================
# Thesys C1 Conversational Query Endpoint
# ============================================================================


@router.post("/query")
async def conversational_query(
    request: C1QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Thesys C1 conversational analytics query endpoint.

    Accepts natural language queries and generates dynamic UI visualizations.
    Example queries:
    - "Show me sales for the last 7 days"
    - "What are the top 5 selling products this month?"
    - "Compare revenue from last week vs this week"
    """
    try:
        client = get_c1_client()

        # Prepare system context with available data
        system_message = """You are an analytics assistant for Lily Cafe POS system.
You generate UI widgets and visualizations for restaurant analytics.

Available data endpoints:
- Revenue analytics: total revenue, orders, payment methods, trends
- Product performance: top products, revenue by category
- Order statistics: order counts, average values, peak hours

When users ask questions, generate appropriate charts, tables, or cards to visualize the data.
Use interactive components like line charts for trends, bar charts for comparisons, and tables for detailed lists."""

        # Make API call to Thesys C1
        completion = client.chat.completions.create(
            model="c1-model-name",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": request.prompt}
            ],
        )

        assistant_response = completion.choices[0].message
        return {"content": assistant_response.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Thesys C1: {str(e)}")
