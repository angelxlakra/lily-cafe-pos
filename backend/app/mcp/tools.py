"""The read-only MCP tools over the cafe's analytics queries.

Wraps the tool functions in app.crud.crud_analytics, which already carry the
SQL. This module adds the MCP tool schemas and converts paise to rupees (see
app.mcp.units) so third-party assistants report correct amounts.
"""

import json
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from app.crud import crud_analytics
from app.db.session import SessionLocal
from app.mcp.units import normalize_money

_READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)


@contextmanager
def _session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run(tool_name: str, fn: Callable[..., str], **kwargs: Any) -> dict:
    with _session() as db:
        payload = json.loads(fn(db, **kwargs))
    return normalize_money(payload, tool_name)


def register_tools(mcp: MCPServer) -> None:
    """Register every cafe analytics tool on the given server."""

    # ============================================================================
    # Revenue & financial
    # ============================================================================


    @mcp.tool(annotations=_READ_ONLY)
    def get_revenue_data(
        start_date: str | None = None, end_date: str | None = None
    ) -> dict:
        """Total revenue, order count, average order value and a breakdown by
        payment method (cash/UPI/card), for paid orders only.

        Dates are ISO 8601 (e.g. '2026-01-05T00:00:00Z'); omit both for all time.
        """
        return _run(
            "get_revenue_data",
            crud_analytics.get_revenue_data_tool,
            start_date=start_date,
            end_date=end_date,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_financial_summary(
        start_date: str | None = None, end_date: str | None = None
    ) -> dict:
        """Full financial picture: gross revenue, GST, net revenue, inventory
        purchase costs, estimated gross profit and margin, and cash received by
        payment method. Use for profit questions or a complete financial overview.
        """
        return _run(
            "get_financial_summary",
            crud_analytics.get_financial_summary_tool,
            start_date=start_date,
            end_date=end_date,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_gst_breakdown(
        start_date: str | None = None, end_date: str | None = None
    ) -> dict:
        """GST collected for the period: total revenue, revenue before GST, the GST
        amount, and the effective GST percentage. Use for tax questions.
        """
        return _run(
            "get_gst_breakdown",
            crud_analytics.get_gst_breakdown_tool,
            start_date=start_date,
            end_date=end_date,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_payment_method_trends(
        start_date: str | None = None, end_date: str | None = None
    ) -> dict:
        """How customers paid: transaction count, total amount, average transaction
        size and share of revenue for each of cash, UPI and card.
        """
        return _run(
            "get_payment_method_trends",
            crud_analytics.get_payment_method_trends_tool,
            start_date=start_date,
            end_date=end_date,
        )


    # ============================================================================
    # Products & menu
    # ============================================================================


    @mcp.tool(annotations=_READ_ONLY)
    def get_product_data(
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 10,
    ) -> dict:
        """Best selling menu items by quantity sold, with revenue for each. Use for
        'what is selling well' and top-seller questions.
        """
        return _run(
            "get_product_data",
            crud_analytics.get_product_data_tool,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_category_performance(
        start_date: str | None = None, end_date: str | None = None
    ) -> dict:
        """Per-category performance: revenue, share of total revenue, order count,
        average order value and the top item in each menu category.
        """
        return _run(
            "get_category_performance",
            crud_analytics.get_category_performance_tool,
            start_date=start_date,
            end_date=end_date,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_menu_item_details(
        item_name: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """Deep dive on one menu item: quantity sold, revenue, how often it was
        ordered, and its current menu price. Omit item_name for the top items.
        """
        return _run(
            "get_menu_item_details",
            crud_analytics.get_menu_item_details_tool,
            item_name=item_name,
            start_date=start_date,
            end_date=end_date,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_vegetarian_vs_nonveg(
        start_date: str | None = None, end_date: str | None = None
    ) -> dict:
        """Vegetarian versus non-vegetarian sales: revenue, quantity, average price
        and the share of the total for each side.
        """
        return _run(
            "get_vegetarian_vs_nonveg",
            crud_analytics.get_vegetarian_vs_nonveg_tool,
            start_date=start_date,
            end_date=end_date,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_beverage_vs_food(
        start_date: str | None = None, end_date: str | None = None
    ) -> dict:
        """Beverage versus food sales: revenue, quantity, average price and the
        share of the total for each side.
        """
        return _run(
            "get_beverage_vs_food",
            crud_analytics.get_beverage_vs_food_tool,
            start_date=start_date,
            end_date=end_date,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_product_mix_analysis(
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 10,
    ) -> dict:
        """Order composition: single-item versus multi-item orders and the average
        number of items per order. Use for bundling and upsell questions.
        """
        return _run(
            "get_product_mix_analysis",
            crud_analytics.get_product_mix_analysis_tool,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )


    # ============================================================================
    # Operations
    # ============================================================================


    @mcp.tool(annotations=_READ_ONLY)
    def get_order_stats(
        start_date: str | None = None, end_date: str | None = None
    ) -> dict:
        """Order counts by status (total, active, completed) and the average order
        value. Use for order volume questions.
        """
        return _run(
            "get_order_stats",
            crud_analytics.get_order_stats_tool,
            start_date=start_date,
            end_date=end_date,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_peak_hours_detailed(
        start_date: str | None = None, end_date: str | None = None
    ) -> dict:
        """Hour-by-hour trade in IST: order count, revenue and average order value
        per hour, plus the busiest and slowest hours. Use for staffing questions.
        """
        return _run(
            "get_peak_hours_detailed",
            crud_analytics.get_peak_hours_detailed_tool,
            start_date=start_date,
            end_date=end_date,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_table_performance(
        start_date: str | None = None, end_date: str | None = None
    ) -> dict:
        """Revenue and order count per table, with the busiest and highest earning
        tables. Use for seating and table utilisation questions.
        """
        return _run(
            "get_table_performance",
            crud_analytics.get_table_performance_tool,
            start_date=start_date,
            end_date=end_date,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_parcel_vs_dinein(
        start_date: str | None = None, end_date: str | None = None
    ) -> dict:
        """Takeaway (parcel) versus dine-in: order count, revenue, average order
        value and the share of the total for each.
        """
        return _run(
            "get_parcel_vs_dinein",
            crud_analytics.get_parcel_vs_dinein_tool,
            start_date=start_date,
            end_date=end_date,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_cancellation_analysis(
        start_date: str | None = None, end_date: str | None = None
    ) -> dict:
        """Cancelled orders: how many, the cancellation rate, revenue lost, the
        average value of a cancelled order, and which tables cancel most.
        """
        return _run(
            "get_cancellation_analysis",
            crud_analytics.get_cancellation_analysis_tool,
            start_date=start_date,
            end_date=end_date,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_time_comparison(
        period: Literal[
            "today_vs_yesterday",
            "this_week_vs_last_week",
            "this_month_vs_last_month",
        ] = "today_vs_yesterday",
    ) -> dict:
        """Compare one period against the one before it — revenue, order count and
        average order value, with the change and percentage change for each. Use
        for trend, growth and 'how are we doing versus' questions.
        """
        return _run(
            "get_time_comparison",
            crud_analytics.get_time_comparison_tool,
            period=period,
        )


    # ============================================================================
    # Inventory & cash
    # ============================================================================


    @mcp.tool(annotations=_READ_ONLY)
    def get_inventory_status() -> dict:
        """Current stock: every active item with its quantity and value, which
        items are below their reorder threshold, how many are out of stock, and
        total inventory value. Use for restocking questions.
        """
        return _run("get_inventory_status", crud_analytics.get_inventory_status_tool)


    @mcp.tool(annotations=_READ_ONLY)
    def get_inventory_usage_trends(
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 10,
    ) -> dict:
        """Stock consumption over a period: the most consumed items, total value
        purchased, total value used, and the value lost to waste adjustments.
        """
        return _run(
            "get_inventory_usage_trends",
            crud_analytics.get_inventory_usage_trends_tool,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )


    @mcp.tool(annotations=_READ_ONLY)
    def get_cash_counter_status(date: str | None = None) -> dict:
        """Cash reconciliation for one day: opening and closing balance, expected
        closing, variance, denomination counts, cash taken that day, and who opened,
        closed and verified it. Date is ISO 8601; omit for today.
        """
        return _run(
            "get_cash_counter_status",
            crud_analytics.get_cash_counter_status_tool,
            date=date,
        )
