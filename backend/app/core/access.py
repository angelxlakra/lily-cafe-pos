"""
Role-based access rules for Lily Cafe POS System.

Two roles exist (see ``schemas.UserRole``):

- ``owner``  — full access, including past-day data and anything that changes
               money, the menu, or an already-generated bill.
- ``admin``  — the reception/counter login. Runs the day: takes orders, bills
               them, prints receipts. Restricted to *today* and cannot
               retroactively change a bill.

The helpers here express those rules in one place so endpoints stay readable
and the rules cannot drift apart between modules.
"""

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app import schemas
from app.core import business_time
from app.models import models


def is_owner(user: Optional[schemas.TokenData]) -> bool:
    """True if the authenticated user holds the owner role."""
    return user is not None and user.role == schemas.UserRole.OWNER


def business_today() -> date:
    """
    The current business day: the IST calendar date (see ``business_time``).
    """
    return business_time.business_today()


def require_owner(user: schemas.TokenData, action: str) -> None:
    """
    Raise 403 unless the user is the owner.

    Args:
        user: The authenticated user.
        action: Short description used in the error message, e.g.
            "edit a bill that has already been generated".
    """
    if not is_owner(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Owner login required to {action}.",
        )


def restrict_history_range(
    user: schemas.TokenData,
    start_date: Optional[str],
    end_date: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    """
    Clamp an order-history date range according to the user's role.

    Owners may request any range. Admins may only ever see the current day —
    an explicit request for any other date is rejected with 403 rather than
    silently narrowed, so the UI can show a clear message.

    Returns:
        The (start_date, end_date) to query with. For the owner these are
        passed through unchanged (including None, meaning "no limit").
    """
    today_str = business_today().isoformat()

    if is_owner(user):
        return start_date, end_date

    # Admin: no range given means "today".
    if start_date is None and end_date is None:
        return today_str, today_str

    requested_start = start_date or end_date
    requested_end = end_date or start_date

    if requested_start != today_str or requested_end != today_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Owner login required to view order history for previous days. "
                "The admin login can only see today's orders."
            ),
        )

    return today_str, today_str


def order_business_date(order: models.Order) -> Optional[date]:
    """
    The business day an order belongs to.

    Read from the order number (``ORD-YYYYMMDD-####``), which is stamped with
    the IST business date at creation time. Falls back to ``created_at``
    (stored as naive UTC, converted to IST) when the order number is not in
    the expected format.
    """
    try:
        return datetime.strptime(order.order_number.split("-")[1], "%Y%m%d").date()
    except (AttributeError, IndexError, ValueError):
        if not order.created_at:
            return None
        return (
            order.created_at.replace(tzinfo=timezone.utc)
            .astimezone(business_time.IST)
            .date()
        )


def require_order_visible(user: schemas.TokenData, order: models.Order) -> None:
    """Raise 403 if an admin tries to reach an order from a previous day."""
    if is_owner(user):
        return

    order_date = order_business_date(order)
    if order_date is not None and order_date != business_today():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Owner login required to view orders from previous days."
            ),
        )
