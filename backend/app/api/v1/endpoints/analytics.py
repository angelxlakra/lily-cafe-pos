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

from app.api.deps import get_db, get_current_owner
from app.core.config import settings
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
    C1QueryRequest
)
from app.crud.crud_analytics import (
    get_revenue_data_tool,
    get_product_data_tool,
    get_order_stats_tool,
    get_inventory_status_tool,
    get_cash_counter_status_tool,
    get_category_performance_tool,
    get_time_comparison_tool,
    get_peak_hours_detailed_tool,
    get_menu_item_details_tool,
    get_payment_method_trends_tool,
    get_product_mix_analysis_tool,
    get_table_performance_tool,
    get_vegetarian_vs_nonveg_tool,
    get_beverage_vs_food_tool,
    get_parcel_vs_dinein_tool,
    get_gst_breakdown_tool,
    get_inventory_usage_trends_tool,
    get_cancellation_analysis_tool,
    get_financial_summary_tool,
    to_ist_timestamp,
    get_time_filter,
    paise_to_rupees,
    calculate_quartiles
)

router = APIRouter()


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


# ============================================================================
# Thesys C1 Conversational Query Endpoint
# ============================================================================


@router.post("/query")
async def conversational_query(
    request: C1QueryRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_owner)
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
- All monetary values provided by tools are in PAISE (1/100th of a Rupee).
- when displaying values to the user, you MUST divide by 100 to convert to Rupees (₹).
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
