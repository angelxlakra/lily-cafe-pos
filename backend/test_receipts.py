"""
Test script to generate sample receipts in both 58mm and 80mm formats.
This script creates test receipts without requiring the server to be running.
"""

from io import BytesIO
from datetime import datetime
from pathlib import Path

from app.utils.pdf_generator import generate_receipt
from app.models.models import Order, OrderItem, Payment, PaymentMethod, OrderStatus


def create_test_order():
    """Create a mock order for testing with real-world data."""
    # Create a mock order matching the screenshot
    order = Order(
        id=1,
        order_number="ORD-20251102-0003",
        table_number=8,
        customer_name=None,  # No customer name
        status=OrderStatus.PAID,
        subtotal=150000,  # ₹1500.00 in paise
        gst_amount=7500,   # ₹75.00 in paise (5% total: 2.5% CGST + 2.5% SGST)
        total_amount=157500,  # ₹1575.00 in paise
        created_at=datetime(2025, 11, 2, 8, 26),  # 02-11-2025 08:26 AM
    )

    # Add order items
    order.order_items = [
        OrderItem(
            id=1,
            order_id=1,
            menu_item_id=1,
            menu_item_name="Chicken Ramen",
            quantity=5,
            unit_price=30000,  # ₹300.00 in paise
            subtotal=150000,  # ₹1500.00 in paise
        ),
    ]

    # Add payments
    order.payments = [
        Payment(
            id=1,
            order_id=1,
            payment_method=PaymentMethod.UPI,
            amount=157500,  # ₹1575.00 in paise
        ),
    ]

    return order


def main():
    """Generate test receipts in both formats."""
    print("=" * 60)
    print("Receipt Generation Test")
    print("=" * 60)
    print()

    # Create test order
    order = create_test_order()
    print(f"Created test order: {order.order_number}")
    print(f"Table: {order.table_number}")
    print(f"Total: ₹{order.total_amount / 100:.2f}")
    print(f"Items: {len(order.order_items)}")
    print(f"Payments: {len(order.payments)}")
    print()

    # Create output directory
    output_dir = Path(__file__).parent / "test_receipts"
    output_dir.mkdir(exist_ok=True)

    # Generate 80mm receipt
    print("Generating 80mm receipt...")
    buffer_80mm = BytesIO()
    try:
        generate_receipt(order, buffer_80mm, paper_size="80mm")
        output_path_80mm = output_dir / f"receipt_80mm_{order.order_number}.pdf"
        with open(output_path_80mm, "wb") as f:
            f.write(buffer_80mm.getvalue())
        print(f"✓ 80mm receipt saved to: {output_path_80mm}")
    except Exception as e:
        print(f"✗ Error generating 80mm receipt: {e}")
        import traceback
        traceback.print_exc()

    print()

    # Generate 58mm receipt
    print("Generating 58mm receipt...")
    buffer_58mm = BytesIO()
    try:
        generate_receipt(order, buffer_58mm, paper_size="58mm")
        output_path_58mm = output_dir / f"receipt_58mm_{order.order_number}.pdf"
        with open(output_path_58mm, "wb") as f:
            f.write(buffer_58mm.getvalue())
        print(f"✓ 58mm receipt saved to: {output_path_58mm}")
    except Exception as e:
        print(f"✗ Error generating 58mm receipt: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 60)
    print("Test complete! Check the test_receipts folder for PDFs.")
    print("=" * 60)


if __name__ == "__main__":
    main()
