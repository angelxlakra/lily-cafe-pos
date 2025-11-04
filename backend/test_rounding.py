"""
Test script to verify bill rounding functionality.
"""

from app.utils.rounding import round_down_to_rupee, round_to_nearest_rupee, calculate_rounding_adjustment


def test_rounding():
    """Test various rounding scenarios."""
    print("=" * 60)
    print("Bill Rounding Test")
    print("=" * 60)
    print()

    test_cases = [
        ("₹157.00", 15700),
        ("₹157.25", 15725),
        ("₹157.49", 15749),
        ("₹157.50", 15750),
        ("₹157.51", 15751),
        ("₹157.75", 15775),
        ("₹157.99", 15799),
        ("₹1575.00", 157500),
        ("₹1575.49", 157549),
        ("₹1575.50", 157550),
        ("₹1575.99", 157599),
    ]

    print(f"{'Original':<15} {'Rounded Down':<15} {'Standard Round':<15} {'Adjustment':<15}")
    print("-" * 60)

    for label, amount_paise in test_cases:
        rounded_down = round_down_to_rupee(amount_paise)
        rounded_standard = round_to_nearest_rupee(amount_paise)
        adjustment = calculate_rounding_adjustment(amount_paise, rounded_down)

        print(
            f"{label:<15} "
            f"₹{rounded_down/100:.2f}:<15 "
            f"₹{rounded_standard/100:.2f}:<15 "
            f"{adjustment/100:+.2f}"
        )

    print()
    print("=" * 60)
    print("Real-world example:")
    print("=" * 60)
    print()

    # Example: 5x Chicken Ramen @ ₹300 = ₹1500
    # Subtotal: ₹1500.00
    # GST (5%): ₹75.00
    # Total before rounding: ₹1575.00
    # Total after rounding down: ₹1575.00 (no change since already a whole rupee)

    subtotal = 150000  # ₹1500 in paise
    gst_rate = 5.0
    gst_amount = int(subtotal * gst_rate / 100)
    total_before_rounding = subtotal + gst_amount
    total_after_rounding = round_down_to_rupee(total_before_rounding)

    print(f"Subtotal:              ₹{subtotal/100:.2f}")
    print(f"GST ({gst_rate}%):          ₹{gst_amount/100:.2f}")
    print(f"Total (before round):  ₹{total_before_rounding/100:.2f}")
    print(f"Total (after round):   ₹{total_after_rounding/100:.2f}")
    print(f"Customer saves:        ₹{(total_before_rounding - total_after_rounding)/100:.2f}")
    print()

    # Another example with decimals
    print("Example with decimals:")
    print("-" * 60)
    subtotal2 = 149900  # ₹1499 in paise
    gst_amount2 = int(subtotal2 * gst_rate / 100)  # ₹74.95 = 7495 paise
    total_before2 = subtotal2 + gst_amount2
    total_after2 = round_down_to_rupee(total_before2)

    print(f"Subtotal:              ₹{subtotal2/100:.2f}")
    print(f"GST ({gst_rate}%):          ₹{gst_amount2/100:.2f}")
    print(f"Total (before round):  ₹{total_before2/100:.2f}")
    print(f"Total (after round):   ₹{total_after2/100:.2f}")
    print(f"Customer saves:        ₹{(total_before2 - total_after2)/100:.2f}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    test_rounding()
