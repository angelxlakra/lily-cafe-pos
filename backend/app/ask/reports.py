"""The fixed catalogue of reports a question can resolve to.

Every report is computed by code from the analytics queries the POS already
has. The model only ever picks one of these by id; it never sees this file's
functions and cannot invent a report. Descriptions are written for the
model — they say what question each report answers.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.ask.periods import NamedPeriod, ResolvedPeriod
from app.crud import crud_analytics as tools
from app.crud.crud_analytics import get_time_filter, to_ist_timestamp
from app.mcp.units import normalize_money
from app.models.models import Order, OrderStatus


class Comparison(StrEnum):
    TODAY_VS_YESTERDAY = "today_vs_yesterday"
    THIS_WEEK_VS_LAST_WEEK = "this_week_vs_last_week"
    THIS_MONTH_VS_LAST_MONTH = "this_month_vs_last_month"


@dataclass(frozen=True)
class ReportContext:
    period: ResolvedPeriod | None
    dish: str | None
    comparison: Comparison | None
    limit: int


RunFn = Callable[[Session, ReportContext], dict]


@dataclass(frozen=True)
class Report:
    id: str
    title: str
    description: str  # for the model: what question this answers
    run: RunFn
    period: Literal["required", "none", "single_day"] = "required"
    default_period: NamedPeriod | None = None
    needs_dish: bool = False
    needs_comparison: bool = False


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _ranged(tool_name: str, fn, *, limit: bool = False) -> RunFn:
    """Wrap an analytics tool that takes start_date/end_date."""

    def run(db: Session, ctx: ReportContext) -> dict:
        kwargs = {"start_date": ctx.period.start_iso, "end_date": ctx.period.end_iso}
        if limit:
            kwargs["limit"] = ctx.limit
        return normalize_money(json.loads(fn(db, **kwargs)), tool_name)

    return run


def _dish_details(db: Session, ctx: ReportContext) -> dict:
    payload = tools.get_menu_item_details_tool(
        db,
        item_name=ctx.dish,
        start_date=ctx.period.start_iso,
        end_date=ctx.period.end_iso,
    )
    return normalize_money(json.loads(payload), "get_menu_item_details")


def _cash_counter(db: Session, ctx: ReportContext) -> dict:
    payload = tools.get_cash_counter_status_tool(db, date=ctx.period.start_day.isoformat())
    return normalize_money(json.loads(payload), "get_cash_counter_status")


def _inventory_status(db: Session, ctx: ReportContext) -> dict:
    return normalize_money(json.loads(tools.get_inventory_status_tool(db)), "get_inventory_status")


def _compare(db: Session, ctx: ReportContext) -> dict:
    payload = tools.get_time_comparison_tool(db, period=ctx.comparison.value)
    return normalize_money(json.loads(payload), "get_time_comparison")


def _best_days(db: Session, ctx: ReportContext) -> dict:
    """Revenue per IST calendar day, with the best and worst days picked out."""
    rows = (
        db.query(
            func.date(to_ist_timestamp(Order.created_at)).label("day"),
            func.sum(Order.total_amount).label("revenue_paise"),
            func.count(Order.id).label("orders"),
        )
        .filter(
            and_(
                Order.status == OrderStatus.PAID,
                *get_time_filter(ctx.period.start_utc, ctx.period.end_utc),
            )
        )
        .group_by("day")
        .order_by(func.sum(Order.total_amount).desc())
        .all()
    )
    days = [
        {
            "date": str(row.day),
            "revenue_rupees": round((row.revenue_paise or 0) / 100, 2),
            "orders": int(row.orders),
        }
        for row in rows
    ]
    total = sum(d["revenue_rupees"] for d in days)
    return {
        "days": days,
        "best_day": days[0] if days else None,
        "worst_day": days[-1] if days else None,
        "trading_days": len(days),
        "average_daily_revenue_rupees": round(total / len(days), 2) if days else 0,
    }


def _period_summary(db: Session, ctx: ReportContext) -> dict:
    """Everything about a period on one page, built from the other reports."""
    return {
        "sales": REPORTS["sales_summary"].run(db, ctx),
        "orders": REPORTS["orders_summary"].run(db, ctx),
        "top_items": REPORTS["top_items"].run(db, ctx),
        "categories": REPORTS["category_performance"].run(db, ctx),
        "payments": REPORTS["payment_methods"].run(db, ctx),
        "peak_hours": REPORTS["peak_hours"].run(db, ctx),
        "best_days": _best_days(db, ctx),
    }


# ----------------------------------------------------------------------
# The catalogue
# ----------------------------------------------------------------------

_ALL: list[Report] = [
    Report(
        id="sales_summary",
        title="Sales",
        description="Total revenue, number of paid orders, average order value, and revenue split by cash/UPI/card. The default for 'how were sales' or 'how much did we make'.",
        run=_ranged("get_revenue_data", tools.get_revenue_data_tool),
        default_period=NamedPeriod.TODAY,
    ),
    Report(
        id="period_summary",
        title="Full performance summary",
        description="Everything about a period on one page: sales, orders, top items, categories, payment split, peak hours, best and worst days. Use when asked for 'all details', 'full report' or 'everything about' a month or period.",
        run=_period_summary,
        default_period=NamedPeriod.THIS_MONTH,
    ),
    Report(
        id="top_items",
        title="Best selling items",
        description="Menu items ranked by quantity sold, with revenue for each. Use for 'best selling', 'which dish performed best', 'what sells most'.",
        run=_ranged("get_product_data", tools.get_product_data_tool, limit=True),
        default_period=NamedPeriod.THIS_MONTH,
    ),
    Report(
        id="dish_details",
        title="Dish performance",
        description="One specific dish: quantity sold, revenue, how often it was ordered, current price. Use when the question names a particular dish. Put the dish exactly as the owner said it.",
        run=_dish_details,
        default_period=NamedPeriod.THIS_MONTH,
        needs_dish=True,
    ),
    Report(
        id="best_days",
        title="Revenue by day",
        description="Revenue for every trading day in the period, with the highest and lowest revenue days. Use for 'best day', 'highest revenue day', 'worst day', 'daily sales'.",
        run=_best_days,
        default_period=NamedPeriod.THIS_MONTH,
    ),
    Report(
        id="category_performance",
        title="Category performance",
        description="Every menu category: revenue, share of revenue, orders, top item. Use for 'how are beverages doing', 'which category', 'category breakdown'.",
        run=_ranged("get_category_performance", tools.get_category_performance_tool),
        default_period=NamedPeriod.THIS_MONTH,
    ),
    Report(
        id="orders_summary",
        title="Orders",
        description="Order counts by status (total, active, completed) and average order value. Use for 'how many orders'.",
        run=_ranged("get_order_stats", tools.get_order_stats_tool),
        default_period=NamedPeriod.TODAY,
    ),
    Report(
        id="peak_hours",
        title="Peak hours",
        description="Orders and revenue by hour of day, with the busiest and slowest hours. Use for 'busiest time', 'peak hours', 'when are we busy', staffing questions.",
        run=_ranged("get_peak_hours_detailed", tools.get_peak_hours_detailed_tool),
        default_period=NamedPeriod.LAST_30_DAYS,
    ),
    Report(
        id="payment_methods",
        title="Payment methods",
        description="Cash vs UPI vs card: transaction counts, amounts, share of revenue. Use for 'how do customers pay', 'UPI vs cash'.",
        run=_ranged("get_payment_method_trends", tools.get_payment_method_trends_tool),
        default_period=NamedPeriod.THIS_MONTH,
    ),
    Report(
        id="cancellations",
        title="Cancellations",
        description="Cancelled orders: count, cancellation rate, revenue lost, which tables cancel most.",
        run=_ranged("get_cancellation_analysis", tools.get_cancellation_analysis_tool),
        default_period=NamedPeriod.THIS_MONTH,
    ),
    Report(
        id="parcel_vs_dinein",
        title="Parcel vs dine-in",
        description="Takeaway (parcel) versus dine-in: orders, revenue, average order value, share.",
        run=_ranged("get_parcel_vs_dinein", tools.get_parcel_vs_dinein_tool),
        default_period=NamedPeriod.THIS_MONTH,
    ),
    Report(
        id="veg_vs_nonveg",
        title="Veg vs non-veg",
        description="Vegetarian versus non-vegetarian sales: revenue, quantity, share.",
        run=_ranged("get_vegetarian_vs_nonveg", tools.get_vegetarian_vs_nonveg_tool),
        default_period=NamedPeriod.THIS_MONTH,
    ),
    Report(
        id="beverage_vs_food",
        title="Beverages vs food",
        description="Beverage versus food sales: revenue, quantity, share.",
        run=_ranged("get_beverage_vs_food", tools.get_beverage_vs_food_tool),
        default_period=NamedPeriod.THIS_MONTH,
    ),
    Report(
        id="table_performance",
        title="Table performance",
        description="Revenue and orders per table, busiest and highest-earning tables.",
        run=_ranged("get_table_performance", tools.get_table_performance_tool),
        default_period=NamedPeriod.THIS_MONTH,
    ),
    Report(
        id="gst",
        title="GST collected",
        description="GST/tax collected: total revenue, revenue before GST, GST amount, effective rate. Use for 'tax', 'GST'.",
        run=_ranged("get_gst_breakdown", tools.get_gst_breakdown_tool),
        default_period=NamedPeriod.THIS_MONTH,
    ),
    Report(
        id="financial_summary",
        title="Financial summary",
        description="Gross revenue, GST, net revenue, inventory purchase costs, estimated gross profit and margin. Use for 'profit', 'margin', 'financials'.",
        run=_ranged("get_financial_summary", tools.get_financial_summary_tool),
        default_period=NamedPeriod.THIS_MONTH,
    ),
    Report(
        id="compare_periods",
        title="Period comparison",
        description="This period versus the previous one — revenue, orders, average order value, with the change. Only three comparisons exist: today vs yesterday, this week vs last week, this month vs last month. Use for 'compared to', 'better than last', 'growth', 'trend'.",
        run=_compare,
        period="none",
        needs_comparison=True,
    ),
    Report(
        id="inventory_status",
        title="Stock levels",
        description="Current stock of every item, which are below reorder threshold, out-of-stock count, total stock value. Use for 'low stock', 'what to reorder', 'inventory'. Has no period — it is always right now.",
        run=_inventory_status,
        period="none",
    ),
    Report(
        id="inventory_usage",
        title="Stock usage",
        description="Stock consumed over a period: most used items, value purchased, value used, waste.",
        run=_ranged("get_inventory_usage_trends", tools.get_inventory_usage_trends_tool, limit=True),
        default_period=NamedPeriod.LAST_30_DAYS,
    ),
    Report(
        id="cash_counter",
        title="Cash counter",
        description="Cash reconciliation for one day: opening and closing balance, expected closing, variance, denominations, who opened and closed. Takes a single day.",
        run=_cash_counter,
        period="single_day",
        default_period=NamedPeriod.TODAY,
    ),
]

REPORTS: dict[str, Report] = {report.id: report for report in _ALL}
REPORT_IDS: tuple[str, ...] = tuple(REPORTS)


def catalogue_for_prompt() -> str:
    """The report list as the model sees it."""
    lines = []
    for report in _ALL:
        needs = []
        if report.period == "required":
            needs.append("period")
        elif report.period == "single_day":
            needs.append("a single day")
        if report.needs_dish:
            needs.append("dish")
        if report.needs_comparison:
            needs.append("comparison")
        suffix = f" [takes: {', '.join(needs)}]" if needs else " [takes: nothing]"
        lines.append(f"- {report.id}: {report.description}{suffix}")
    return "\n".join(lines)
