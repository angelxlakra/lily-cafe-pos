"""
Utility functions for bill rounding.
Helps avoid paise (decimal) amounts in final bills.
"""


def round_to_nearest_rupee(amount_in_paise: int) -> int:
    """
    Round amount to nearest rupee (standard rounding).

    Args:
        amount_in_paise: Amount in paise (1 rupee = 100 paise)

    Returns:
        Rounded amount in paise (multiple of 100)

    Examples:
        round_to_nearest_rupee(15749) -> 15700  # ₹157.49 -> ₹157
        round_to_nearest_rupee(15750) -> 15800  # ₹157.50 -> ₹158
        round_to_nearest_rupee(15751) -> 15800  # ₹157.51 -> ₹158
    """
    rupees = amount_in_paise / 100
    rounded_rupees = round(rupees)  # Standard rounding: 0.5+ rounds up
    return int(rounded_rupees * 100)


def round_down_to_rupee(amount_in_paise: int) -> int:
    """
    Round down amount to nearest rupee (always in customer's favor).

    Args:
        amount_in_paise: Amount in paise (1 rupee = 100 paise)

    Returns:
        Rounded down amount in paise (multiple of 100)

    Examples:
        round_down_to_rupee(15749) -> 15700  # ₹157.49 -> ₹157
        round_down_to_rupee(15750) -> 15700  # ₹157.50 -> ₹157
        round_down_to_rupee(15799) -> 15700  # ₹157.99 -> ₹157
    """
    rupees = amount_in_paise / 100
    rounded_rupees = int(rupees)  # Floor division
    return int(rounded_rupees * 100)


def calculate_rounding_adjustment(original: int, rounded: int) -> int:
    """
    Calculate the adjustment made by rounding.
    Positive = rounded up, Negative = rounded down

    Args:
        original: Original amount in paise
        rounded: Rounded amount in paise

    Returns:
        Adjustment amount in paise
    """
    return rounded - original
