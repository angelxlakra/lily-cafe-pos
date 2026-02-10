from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel

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
