"""Tests for the MCP tool layer.

The bulk of these cover money units. The underlying analytics tools label
paise as `*_rupees` (paise_to_rupees is a pass-through), so a regression here
reports ₹45,000 when the cafe took ₹450.
"""

import asyncio
import json
from decimal import Decimal

import pytest

from app.mcp.server import mcp
from app.mcp.units import ALREADY_RUPEES, normalize_money
from app.models.inventory_models import InventoryItem
from app.models.models import (
    Category,
    MenuItem,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentMethod,
)

# ============================================================================
# Unit conversion
# ============================================================================


def test_paise_field_converts_to_rupees():
    assert normalize_money({"total_revenue_rupees": 45000}, "get_revenue_data") == {
        "total_revenue_rupees": 450.0
    }


def test_exempt_field_is_left_alone():
    """Inventory values come from Numeric columns and are already rupees."""
    result = normalize_money(
        {"total_inventory_value_rupees": 450.0}, "get_inventory_status"
    )
    assert result == {"total_inventory_value_rupees": 450.0}


def test_same_field_name_converts_for_a_non_exempt_tool():
    """value_rupees is exempt only for the inventory tool."""
    assert normalize_money({"value_rupees": 45000}, "get_revenue_data") == {
        "value_rupees": 450.0
    }


def test_payment_method_map_values_convert():
    """This map's keys are method names, so the _rupees suffix rule misses it."""
    result = normalize_money(
        {"revenue_by_payment_method": {"cash": 30000, "upi": 15000}},
        "get_revenue_data",
    )
    assert result == {"revenue_by_payment_method": {"cash": 300.0, "upi": 150.0}}


def test_none_and_non_numeric_pass_through():
    payload = {"closing_balance_rupees": None, "period": "All time"}
    assert normalize_money(payload, "get_revenue_data") == payload


def test_counts_and_percentages_are_untouched():
    payload = {
        "total_orders": 45000,
        "gross_margin_percentage": 32.5,
        "is_verified": True,
    }
    assert normalize_money(payload, "get_financial_summary") == payload


def test_nested_structures_convert():
    payload = {
        "revenue": {"gross_revenue_rupees": 100000},
        "top_products": [
            {"name": "Chai", "revenue_rupees": 5000, "quantity_sold": 10},
            {"name": "Dosa", "revenue_rupees": 25000, "quantity_sold": 5},
        ],
    }
    result = normalize_money(payload, "get_product_data")
    assert result["revenue"]["gross_revenue_rupees"] == 1000.0
    assert [p["revenue_rupees"] for p in result["top_products"]] == [50.0, 250.0]
    assert result["top_products"][0]["quantity_sold"] == 10


def test_financial_summary_mixes_units_correctly():
    """Revenue is paise; inventory purchase cost is already rupees."""
    payload = {
        "revenue": {"gross_revenue_rupees": 100000},
        "costs": {"inventory_purchases_rupees": 300.0},
    }
    result = normalize_money(payload, "get_financial_summary")
    assert result["revenue"]["gross_revenue_rupees"] == 1000.0
    assert result["costs"]["inventory_purchases_rupees"] == 300.0


def test_cash_counter_separates_balance_from_takings():
    """Balances are Numeric rupees; cash_received_today is summed paise."""
    payload = {
        "opening_balance_rupees": 500.0,
        "cash_received_today_rupees": 45000,
    }
    result = normalize_money(payload, "get_cash_counter_status")
    assert result["opening_balance_rupees"] == 500.0
    assert result["cash_received_today_rupees"] == 450.0


# ============================================================================
# Tool registration
# ============================================================================


def _tools():
    return asyncio.run(mcp.list_tools())


def test_every_tool_is_read_only():
    for tool in _tools():
        assert tool.annotations is not None, f"{tool.name} has no annotations"
        assert tool.annotations.read_only_hint is True, f"{tool.name} is not read-only"


def test_every_tool_has_a_description():
    for tool in _tools():
        assert tool.description, f"{tool.name} has no description"


def test_exemption_map_refers_to_real_tools():
    """A typo in ALREADY_RUPEES would silently divide a rupee value by 100."""
    registered = {tool.name for tool in _tools()}
    assert set(ALREADY_RUPEES) <= registered


# ============================================================================
# End to end against a seeded database
# ============================================================================


@pytest.fixture
def seeded_mcp(db_session, monkeypatch):
    """Point the MCP layer at the test database and seed one known sale."""
    monkeypatch.setattr(
        "app.mcp.tools.SessionLocal", lambda: db_session, raising=True
    )

    category = Category(name="Beverages")
    db_session.add(category)
    db_session.flush()

    chai = MenuItem(
        name="Masala Chai", price=5000, category_id=category.id, is_beverage=True
    )
    db_session.add(chai)
    db_session.flush()

    # One paid order: ₹450 total (45000 paise), settled in cash.
    order = Order(
        order_number="TEST-001",
        table_number=3,
        subtotal=40000,
        gst_amount=5000,
        total_amount=45000,
        status=OrderStatus.PAID,
    )
    db_session.add(order)
    db_session.flush()

    db_session.add(
        OrderItem(
            order_id=order.id,
            menu_item_id=chai.id,
            menu_item_name=chai.name,
            quantity=8,
            unit_price=5000,
            subtotal=40000,
            is_beverage=True,
        )
    )
    db_session.add(
        Payment(
            order_id=order.id, payment_method=PaymentMethod.CASH, amount=45000
        )
    )

    # ₹300 of stock on hand: 10 units at ₹30 each.
    db_session.add(
        InventoryItem(
            name="Tea leaves",
            unit="kg",
            current_quantity=Decimal("10"),
            min_threshold=Decimal("2"),
            cost_per_unit=Decimal("30"),
        )
    )
    db_session.commit()
    return db_session


def _call(name, **arguments):
    result = asyncio.run(mcp.call_tool(name, arguments))
    assert not result.is_error, result.content
    if result.structured_content is not None:
        return result.structured_content
    return json.loads(result.content[0].text)


def test_every_tool_executes(seeded_mcp):
    """Catches a wrapper passing an argument the analytics function lacks."""
    for tool in _tools():
        result = asyncio.run(mcp.call_tool(tool.name, {}))
        assert not result.is_error, f"{tool.name} failed: {result.content}"


def test_revenue_tool_reports_rupees_not_paise(seeded_mcp):
    data = _call("get_revenue_data")

    assert data["total_revenue_rupees"] == 450.0
    assert data["average_order_value_rupees"] == 450.0
    assert data["revenue_by_payment_method"]["cash"] == 450.0
    assert data["total_orders"] == 1


def test_product_tool_reports_rupees(seeded_mcp):
    data = _call("get_product_data")

    chai = data["top_products"][0]
    assert chai["name"] == "Masala Chai"
    assert chai["quantity_sold"] == 8
    assert chai["revenue_rupees"] == 400.0


def test_inventory_value_is_not_divided(seeded_mcp):
    data = _call("get_inventory_status")

    assert data["total_inventory_value_rupees"] == 300.0
    assert data["items"][0]["value_rupees"] == 300.0


def test_financial_summary_holds_both_unit_families(seeded_mcp):
    data = _call("get_financial_summary")

    assert data["revenue"]["gross_revenue_rupees"] == 450.0
    assert data["revenue"]["gst_amount_rupees"] == 50.0
    assert data["revenue"]["net_revenue_rupees"] == 400.0
    assert data["cash_flow"]["cash_received_rupees"] == 450.0
