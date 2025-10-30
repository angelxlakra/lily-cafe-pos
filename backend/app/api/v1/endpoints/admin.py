"""
Admin-only endpoints for Lily Cafe POS System.
"""

from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.models.models import OrderStatus
from app.core.config import settings
from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Get dashboard statistics (admin only)."""
    today = date.today()

    # Today's stats
    today_orders = crud.get_orders(db, today_only=True)
    today_revenue = sum(
        order.total_amount
        for order in today_orders
        if order.status == OrderStatus.COMPLETED
    )
    active_orders = crud.get_orders(db, status=OrderStatus.ACTIVE)

    return {
        "today_orders": len(today_orders),
        "today_revenue": today_revenue,  # In paise
        "active_orders": len(active_orders),
        "total_tables": settings.MAX_TABLES,
    }
