"""
Test script to generate receipts with multiple items.
"""

from io import BytesIO
from datetime import datetime
from pathlib import Path

from app.utils.pdf_generator import generate_receipt
from app.models.models import Order, OrderItem, Payment, PaymentMethod, OrderStatus


def create_large_order():
    """Create a mock order with many items."""
    order = Order(
        id=1,
        order_number="ORD-20251104-100500",
        table_number=12,
        customer_name="John Doe",
        status=OrderStatus.PAID,
        subtotal=72000,  # ₹720.00 in paise
        gst_amount=3600,  # ₹36.00 in paise (5%)
        total_amount=75600,  # ₹756.00 in paise
        created_at=datetime.now(),
    )

    # Add many order items
    order.order_items = [
        OrderItem(
            id=1,
            order_id=1,
            menu_item_id=1,
            menu_item_name="Masala Dosa",
            quantity=2,
            unit_price=8000,  # ₹80.00
            subtotal=16000,
        ),
        OrderItem(
            id=2,
            order_id=1,
            menu_item_id=2,
            menu_item_name="Plain Dosa",
            quantity=1,
            unit_price=6000,  # ₹60.00
            subtotal=6000,
        ),
        OrderItem(
            id=3,
            order_id=1,
            menu_item_id=3,
            menu_item_name="Idli Sambar",
            quantity=3,
            unit_price=5000,  # ₹50.00
            subtotal=15000,
        ),
        OrderItem(
            id=4,
            order_id=1,
            menu_item_id=4,
            menu_item_name="Chicken Ramen",
            quantity=1,
            unit_price=30000,  # ₹300.00
            subtotal=30000,
        ),
        OrderItem(
            id=5,
            order_id=1,
            menu_item_id=5,
            menu_item_name="Filter Coffee",
            quantity=4,
            unit_price=3000,  # ₹30.00
            subtotal=12000,
        ),
        OrderItem(
            id=6,
            order_id=1,
            menu_item_id=6,
            menu_item_name="Vada",
            quantity=2,
            unit_price=4000,  # ₹40.00
            subtotal=8000,
        ),
    ]

    # Add payments (split payment)
    order.payments = [
        Payment(
            id=1,
            order_id=1,
            payment_method=PaymentMethod.CASH,
            amount=40000,  # ₹400.00
        ),
        Payment(
            id=2,
            order_id=1,
            payment_method=PaymentMethod.UPI,
            amount=35600,  # ₹356.00
        ),
    ]

    return order


def main():
    """Generate test receipts with multiple items."""
    print("=" * 60)
    print("Multi-Item Receipt Test")
    print("=" * 60)
    print()

    order = create_large_order()
    print(f"Created test order: {order.order_number}")
    print(f"Table: {order.table_number}")
    print(f"Customer: {order.customer_name}")
    print(f"Total: ₹{order.total_amount / 100:.2f}")
    print(f"Items: {len(order.order_items)}")
    print(f"Payments: {len(order.payments)}")
    print()

    # Create output directory
    output_dir = Path(__file__).parent / "test_receipts"
    output_dir.mkdir(exist_ok=True)

    # Generate 80mm receipt
    print("Generating 80mm receipt with multiple items...")
    buffer_80mm = BytesIO()
    try:
        generate_receipt(order, buffer_80mm, paper_size="80mm")
        output_path_80mm = output_dir / f"receipt_80mm_multi_{order.order_number}.pdf"
        with open(output_path_80mm, "wb") as f:
            f.write(buffer_80mm.getvalue())
        print(f"✓ 80mm receipt saved to: {output_path_80mm}")
    except Exception as e:
        print(f"✗ Error generating 80mm receipt: {e}")
        import traceback
        traceback.print_exc()

    print()

    # Generate 58mm receipt
    print("Generating 58mm receipt with multiple items...")
    buffer_58mm = BytesIO()
    try:
        generate_receipt(order, buffer_58mm, paper_size="58mm")
        output_path_58mm = output_dir / f"receipt_58mm_multi_{order.order_number}.pdf"
        with open(output_path_58mm, "wb") as f:
            f.write(buffer_58mm.getvalue())
        print(f"✓ 58mm receipt saved to: {output_path_58mm}")
    except Exception as e:
        print(f"✗ Error generating 58mm receipt: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 60)
    print("Multi-item test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
