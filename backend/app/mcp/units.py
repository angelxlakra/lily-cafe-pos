"""Money normalization for the MCP tool layer.

The analytics tools in app.crud.crud_analytics name their monetary fields
`*_rupees`, but paise_to_rupees() is a pass-through — those values are paise.
The POS frontend relies on that and divides by 100 when it renders, so the
tools cannot be changed without breaking it. MCP clients are third-party
assistants with no such convention, so the conversion happens here.

Some `*_rupees` fields really are rupees: they come from Numeric columns
(inventory cost_per_unit, cash counter balances) rather than paise integers.
Those are listed per tool in ALREADY_RUPEES and pass through untouched.
"""

from typing import Any

# Fields that are already rupees and must NOT be divided, keyed by tool name.
# Everything else ending in `_rupees` is paise. Verified against each call site
# of paise_to_rupees() in app/crud/crud_analytics.py.
ALREADY_RUPEES: dict[str, frozenset[str]] = {
    # InventoryItem.cost_per_unit / current_quantity are Numeric(10, 2) rupees.
    "get_inventory_status": frozenset(
        {"value_rupees", "total_inventory_value_rupees"}
    ),
    "get_inventory_usage_trends": frozenset(
        {
            "total_purchases_value_rupees",
            "total_usage_value_rupees",
            "waste_adjustments_value_rupees",
        }
    ),
    # DailyCashCounter balances are Numeric(10, 2) rupees, but
    # cash_received_today_rupees is summed from Payment.amount, so it is paise.
    "get_cash_counter_status": frozenset(
        {
            "opening_balance_rupees",
            "closing_balance_rupees",
            "expected_closing_rupees",
            "variance_rupees",
        }
    ),
    "get_financial_summary": frozenset({"inventory_purchases_rupees"}),
}

# Maps whose *values* are paise while their keys are payment method names
# ("cash", "upi", "card") rather than the `_rupees` suffix.
_PAISE_VALUED_MAPS = frozenset({"revenue_by_payment_method"})


def _to_rupees(value: Any) -> Any:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    return round(value / 100, 2)


def normalize_money(payload: Any, tool_name: str) -> Any:
    """Convert a tool's paise-denominated fields to rupees."""
    return _walk(payload, ALREADY_RUPEES.get(tool_name, frozenset()))


def _walk(node: Any, exempt: frozenset[str]) -> Any:
    if isinstance(node, dict):
        result = {}
        for key, value in node.items():
            if key in _PAISE_VALUED_MAPS and isinstance(value, dict):
                result[key] = {k: _to_rupees(v) for k, v in value.items()}
            elif key.endswith("_rupees") and key not in exempt:
                result[key] = _to_rupees(value)
            else:
                result[key] = _walk(value, exempt)
        return result
    if isinstance(node, list):
        return [_walk(item, exempt) for item in node]
    return node
