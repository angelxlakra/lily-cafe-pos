# backend/tests/test_printer_gst.py
"""Tests for GST line rendering on the printed ESC/POS receipt."""

from datetime import datetime

import pytest

from app.core import settings_store
from app.models.models import Order, OrderItem, OrderStatus
from app.utils import printer as printer_module


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Reset the settings cache after each test to prevent cross-test pollution."""
    yield
    settings_store._cache = {}


class FakePrinter:
    """Minimal ESC/POS printer double that records every printed line."""

    def __init__(self):
        self.lines: list[str] = []

    def set(self, *args, **kwargs):
        pass

    def text(self, value):
        self.lines.append(value)

    def cut(self):
        pass

    def close(self):
        pass


def make_order(subtotal: int = 150000, total_amount: int = 157500) -> Order:
    """Build an in-memory order (no DB) for exercising print_receipt()."""
    order = Order(
        id=1,
        order_number="ORD-20260101-0001",
        table_number=1,
        customer_name=None,
        status=OrderStatus.PAID,
        subtotal=subtotal,
        gst_amount=total_amount - subtotal,
        total_amount=total_amount,
        created_at=datetime(2026, 1, 1, 12, 0),
    )
    order.order_items = [
        OrderItem(
            id=1,
            order_id=1,
            menu_item_id=1,
            menu_item_name="Chicken Ramen",
            quantity=1,
            unit_price=subtotal,
            subtotal=subtotal,
        ),
    ]
    return order


@pytest.fixture
def fake_printer(monkeypatch):
    """Route print_receipt() to a FakePrinter instead of real hardware."""
    printer = FakePrinter()
    monkeypatch.setattr(printer_module, "get_printer", lambda: printer)
    monkeypatch.setattr(printer_module.settings, "PRINTER_ENABLED", True)
    return printer


# ============================================================================
# Tests
# ============================================================================

def test_print_receipt_omits_gst_lines_when_rate_is_zero(fake_printer):
    """When app.gst_rate is 0, the receipt has no CGST/SGST lines at all."""
    settings_store._cache = dict(settings_store.DEFAULTS)
    settings_store._cache["app.gst_rate"] = "0"

    order = make_order(subtotal=150000, total_amount=150000)
    assert printer_module.print_receipt(order) is True

    printed = "".join(fake_printer.lines)
    assert "CGST" not in printed
    assert "SGST" not in printed


def test_print_receipt_includes_gst_lines_when_rate_is_nonzero(fake_printer):
    """When app.gst_rate is nonzero, the receipt still shows the CGST/SGST breakdown."""
    settings_store._cache = dict(settings_store.DEFAULTS)
    settings_store._cache["app.gst_rate"] = "5.0"

    order = make_order(subtotal=150000, total_amount=157500)
    assert printer_module.print_receipt(order) is True

    printed = "".join(fake_printer.lines)
    assert "CGST" in printed
    assert "SGST" in printed
