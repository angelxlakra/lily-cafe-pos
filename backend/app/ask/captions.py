"""One-sentence captions for each report, written by code from its own numbers.

The caption is the "answer" an owner reads before the card. Every figure in
it is copied from the computed report data — nothing here derives a number
the report did not already contain — so it can never disagree with the card
beneath it.
"""

from decimal import ROUND_HALF_UP, Decimal
from collections.abc import Callable
from typing import Any

Data = dict[str, Any]


def caption_for(report_id: str, data: Data, period_label: str | None, dish: str | None) -> str | None:
    writer = _WRITERS.get(report_id)
    if writer is None:
        return None
    try:
        return writer(data, period_label or "", dish)
    except (KeyError, TypeError, IndexError, ZeroDivisionError):
        # A caption is a nicety; the card still shows. Never fail the answer.
        return None


# ----------------------------------------------------------------------
# Formatting
# ----------------------------------------------------------------------


def rupees(value: Any) -> str:
    if value is None:
        return "—"
    return "₹" + _indian_grouping(_round_half_away(float(value)))


def _round_half_away(value: float) -> int:
    """Round like the browser's Intl.NumberFormat (half away from zero).

    Python's round() is half-to-even: 7654.5 → 7654, while the card beneath
    the caption shows 7,655. The two must never disagree.
    """
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _indian_grouping(amount: int) -> str:
    sign = "-" if amount < 0 else ""
    digits = str(abs(amount))
    if len(digits) <= 3:
        return sign + digits
    head, tail = digits[:-3], digits[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return sign + ",".join(parts) + "," + tail


def count(value: Any, noun: str) -> str:
    n = int(value or 0)
    return f"{n:,} {noun}{'' if n == 1 else 's'}"


def pct(value: Any) -> str:
    return f"{_round_half_away(float(value or 0))}%"


def day(iso: str) -> str:
    from datetime import date

    d = date.fromisoformat(iso)
    return f"{d:%a %-d %b}"


def during(period_label: str) -> str:
    """The period as a natural phrase to append to a sentence.

    The card shows the exact dates, so this drops them for named periods:
    "Last week, 7–13 Sep 2026" → " last week"; "September so far, 1–20 Sep
    2026" → " so far in September"; "August 2026" → " in August 2026".
    """
    if not period_label or period_label == "All time":
        return ""
    head = period_label.split(",")[0].strip()
    lowered = head[:1].lower() + head[1:]
    if head.startswith(("Today", "Yesterday", "This week", "Last week", "This month", "Last month")):
        return f" {lowered}"
    if head.startswith("Last ") and head.endswith(" days"):
        return f" in the {lowered}"
    if head.endswith(" so far"):
        return f" so far in {head[: -len(' so far')]}"
    if " – " in head:
        a, b = head.split(" – ", 1)
        return f" between {a} and {b}"
    if head[:3] in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
        return f" on {head}"
    return f" in {head}"


# ----------------------------------------------------------------------
# Writers
# ----------------------------------------------------------------------


def _sales(d: Data, p: str, _: str | None) -> str:
    if not d.get("total_orders"):
        return f"No paid orders{during(p)}."
    methods = d.get("revenue_by_payment_method") or {}
    top = max(methods, key=methods.get) if methods else None
    top_note = f", mostly {_method(top)}" if top and methods[top] > 0 else ""
    return (
        f"{rupees(d['total_revenue_rupees'])} from {count(d['total_orders'], 'paid order')}{during(p)}"
        f" — {rupees(d['average_order_value_rupees'])} per order{top_note}."
    )


def _method(key: str, capital: bool = False) -> str:
    if key == "upi":
        return "UPI"
    name = {"cash": "cash", "card": "card"}.get(key, key)
    return name.capitalize() if capital else name


def _top_items(d: Data, p: str, _: str | None) -> str:
    items = d.get("top_products") or []
    if not items:
        return f"Nothing was sold{during(p)}."
    first = items[0]
    line = f"{first['name']} sold best{during(p)}: {count(first['quantity_sold'], 'portion')} for {rupees(first['revenue_rupees'])}"
    if len(items) > 1:
        line += f", ahead of {items[1]['name']} ({count(items[1]['quantity_sold'], 'portion')})"
    return line + "."


def _dish(d: Data, p: str, dish: str | None) -> str:
    if d.get("error"):
        return str(d["error"])
    perf = d.get("performance") or {}
    name = d.get("item_name") or dish or "This dish"
    if not perf.get("quantity_sold"):
        return f"{name} did not sell{during(p)}."
    return (
        f"{name} sold {count(perf['quantity_sold'], 'portion')} across {count(perf['order_count'], 'order')}{during(p)}"
        f", bringing in {rupees(perf['revenue_rupees'])} at {rupees(d.get('current_price_rupees'))} each."
    )


def _best_days(d: Data, p: str, _: str | None) -> str:
    best, worst = d.get("best_day"), d.get("worst_day")
    if not best:
        return f"No sales{during(p)}."
    line = f"Best day{during(p)} was {day(best['date'])} at {rupees(best['revenue_rupees'])}"
    if worst and worst["date"] != best["date"]:
        line += f"; the quietest was {day(worst['date'])} at {rupees(worst['revenue_rupees'])}"
    return line + f". Average {rupees(d['average_daily_revenue_rupees'])} a day over {count(d['trading_days'], 'trading day')}."


def _categories(d: Data, p: str, _: str | None) -> str:
    cats = d.get("categories") or []
    if not cats:
        return f"No sales{during(p)}."
    top = cats[0]
    line = f"{top['name']} led{during(p)} with {rupees(top['revenue_rupees'])}, {pct(top['revenue_percentage'])} of revenue"
    if len(cats) > 1:
        line += f"; {cats[1]['name']} was next at {pct(cats[1]['revenue_percentage'])}"
    return line + "."


def _orders(d: Data, p: str, _: str | None) -> str:
    total = d.get("total_orders") or 0
    if not total:
        return f"No orders{during(p)}."
    line = f"{count(total, 'order')}{during(p)}: {int(d.get('completed_orders') or 0):,} paid"
    if d.get("active_orders"):
        line += f", {count(d['active_orders'], 'still open')}"
    return line + f". {rupees(d['average_order_value_rupees'])} per paid order."


def _peak_hours(d: Data, p: str, _: str | None) -> str:
    peak = d.get("peak_hours") or []
    if not peak:
        return f"No orders{during(p)}."
    busiest = peak[0]
    line = f"Busiest at {busiest['hour_label']}{during(p)}, with {count(busiest['order_count'], 'order')}"
    if len(peak) > 1:
        line += f", then {peak[1]['hour_label']}"
    slow = d.get("slowest_hours") or []
    if slow:
        line += f". Quietest at {slow[0]['hour_label']}"
    return line + "."


def _payments(d: Data, p: str, _: str | None) -> str:
    methods = d.get("payment_methods") or {}
    live = {k: v for k, v in methods.items() if (v.get("total_amount_rupees") or 0) > 0}
    if not live:
        return f"No payments{during(p)}."
    ranked = sorted(live.items(), key=lambda kv: kv[1]["total_amount_rupees"], reverse=True)
    top_key, top = ranked[0]
    line = f"{_method(top_key, capital=True)} covered {pct(top['percentage_revenue'])} of {rupees(d['total_revenue_rupees'])}{during(p)}"
    if len(ranked) > 1:
        line += f", {_method(ranked[1][0])} {pct(ranked[1][1]['percentage_revenue'])}"
    return line + "."


def _cancellations(d: Data, p: str, _: str | None) -> str:
    n = d.get("total_canceled_orders") or 0
    if not n:
        return f"No cancellations{during(p)}."
    return (
        f"{count(n, 'order')} cancelled{during(p)} — {pct(d['cancellation_rate'])} of orders, "
        f"{rupees(d['canceled_revenue_lost_rupees'])} of revenue lost."
    )


def _pair(a_key: str, a_label: str, b_key: str, b_label: str) -> Callable[[Data, str, str | None], str]:
    def write(d: Data, p: str, _: str | None) -> str:
        a, b = d.get(a_key) or {}, d.get(b_key) or {}
        a_rev, b_rev = a.get("revenue_rupees") or 0, b.get("revenue_rupees") or 0
        if not a_rev and not b_rev:
            return f"No sales{during(p)}."
        (lead, lead_label), (other, other_label) = (
            ((a, a_label), (b, b_label)) if a_rev >= b_rev else ((b, b_label), (a, a_label))
        )
        return (
            f"{lead_label} brought {pct(lead['revenue_percentage'])} of revenue{during(p)} "
            f"({rupees(lead['revenue_rupees'])}); {other_label.lower()} {pct(other['revenue_percentage'])}."
        )

    return write


def _tables(d: Data, p: str, _: str | None) -> str:
    tables = d.get("tables") or []
    if not tables:
        return f"No table orders{during(p)}."
    return (
        f"Table {d['highest_revenue_table']} earned the most{during(p)}; table {d['busiest_table']} had the most orders. "
        f"{count(d['total_tables_used'], 'table')} used, averaging {rupees(d['avg_revenue_per_table_rupees'])} each."
    )


def _gst(d: Data, p: str, _: str | None) -> str:
    if not d.get("total_revenue_rupees"):
        return f"No sales{during(p)}."
    return (
        f"{rupees(d['gst_amount_rupees'])} GST collected{during(p)} on {rupees(d['total_revenue_rupees'])} "
        f"— {rupees(d['revenue_before_gst_rupees'])} before tax."
    )


def _financial(d: Data, p: str, _: str | None) -> str:
    rev, profit = d.get("revenue") or {}, d.get("estimated_profit") or {}
    if not rev.get("gross_revenue_rupees"):
        return f"No sales{during(p)}."
    costs = (d.get("costs") or {}).get("inventory_purchases_rupees") or 0
    return (
        f"{rupees(rev['gross_revenue_rupees'])} gross{during(p)}, {rupees(rev['net_revenue_rupees'])} after GST. "
        f"Stock purchases {rupees(costs)}, leaving an estimated {rupees(profit['gross_profit_rupees'])} "
        f"({pct(profit['gross_margin_percentage'])} margin)."
    )


def _compare(d: Data, _: str, __: str | None) -> str:
    cur, prev, change = d.get("current") or {}, d.get("previous") or {}, d.get("change") or {}
    delta = change.get("revenue_change_rupees") or 0
    direction = "up" if delta > 0 else "down" if delta < 0 else "level"
    line = f"Revenue is {direction}"
    if delta:
        line += f" {rupees(abs(delta))} ({pct(abs(change.get('revenue_change_percentage') or 0))})"
    line += f": {rupees(cur.get('revenue_rupees'))} against {rupees(prev.get('revenue_rupees'))} before"
    orders_delta = change.get("orders_change") or 0
    if orders_delta:
        line += f", with {abs(int(orders_delta))} {'more' if orders_delta > 0 else 'fewer'} orders"
    return line + "."


def _inventory(d: Data, _: str, __: str | None) -> str:
    low = d.get("low_stock_items") or []
    total = rupees(d.get("total_inventory_value_rupees"))
    if not low:
        return f"Nothing is below its reorder level. Stock on hand is worth {total}."
    names = ", ".join(item["name"] for item in low[:3])
    more = f" and {len(low) - 3} more" if len(low) > 3 else ""
    return f"{count(len(low), 'item')} below reorder level: {names}{more}. Stock on hand is worth {total}."


def _inventory_usage(d: Data, p: str, _: str | None) -> str:
    top = d.get("top_consumed_items") or []
    if not top:
        return f"No stock usage recorded{during(p)}."
    first = top[0]
    line = f"{first['item_name']} was used most{during(p)} ({first['total_usage']:g} {first['unit']})"
    line += f". Purchases {rupees(d['total_purchases_value_rupees'])}, usage {rupees(d['total_usage_value_rupees'])}"
    waste = d.get("waste_adjustments_value_rupees") or 0
    if waste:
        line += f", waste {rupees(waste)}"
    return line + "."


def _cash(d: Data, p: str, _: str | None) -> str:
    if d.get("error"):
        return f"No cash counter was recorded{during(p)}."
    variance = d.get("variance_rupees")
    line = f"Opened at {rupees(d['opening_balance_rupees'])}, {rupees(d['cash_received_today_rupees'])} taken in cash"
    if d.get("closing_balance_rupees") is None:
        return line + ". Not closed yet."
    if not variance:
        return line + f", closed at {rupees(d['closing_balance_rupees'])} — balanced exactly."
    word = "over" if variance > 0 else "short"
    return line + f", closed {rupees(abs(variance))} {word} of the expected {rupees(d['expected_closing_rupees'])}."


def _summary(d: Data, p: str, _: str | None) -> str:
    sales = d.get("sales") or {}
    if not sales.get("total_orders"):
        return f"No sales{during(p)}."
    line = _sales(sales, p, None).rstrip(".")
    items = (d.get("top_items") or {}).get("top_products") or []
    if items:
        line += f". {items[0]['name']} was the best seller"
    best = (d.get("best_days") or {}).get("best_day")
    if best:
        line += f"; the best day was {day(best['date'])} at {rupees(best['revenue_rupees'])}"
    return line + "."


_WRITERS: dict[str, Callable[[Data, str, str | None], str]] = {
    "sales_summary": _sales,
    "period_summary": _summary,
    "top_items": _top_items,
    "dish_details": _dish,
    "best_days": _best_days,
    "category_performance": _categories,
    "orders_summary": _orders,
    "peak_hours": _peak_hours,
    "payment_methods": _payments,
    "cancellations": _cancellations,
    "parcel_vs_dinein": _pair("dine_in", "Dine-in", "parcel", "Parcel"),
    "veg_vs_nonveg": _pair("vegetarian", "Veg", "non_vegetarian", "Non-veg"),
    "beverage_vs_food": _pair("food", "Food", "beverages", "Beverages"),
    "table_performance": _tables,
    "gst": _gst,
    "financial_summary": _financial,
    "compare_periods": _compare,
    "inventory_status": _inventory,
    "inventory_usage": _inventory_usage,
    "cash_counter": _cash,
}
