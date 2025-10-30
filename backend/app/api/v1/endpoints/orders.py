"""
Order and payment endpoints for Lily Cafe POS System.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas, crud
from app.models.models import OrderStatus
from app.api.deps import get_db

router = APIRouter()


# ============================================================================
# Order Routes
# ============================================================================


@router.get("", response_model=List[schemas.Order])
def list_orders(
    status: Optional[OrderStatus] = None,
    table_number: Optional[int] = None,
    today_only: bool = False,
    db: Session = Depends(get_db),
):
    """
    Get all orders with optional filtering.

    Query parameters:
    - status: Filter by order status (active, completed, cancelled)
    - table_number: Filter by table number
    - today_only: Only show today's orders (default: false)
    """
    return crud.get_orders(
        db, status=status, table_number=table_number, today_only=today_only
    )


@router.get("/{order_id}", response_model=schemas.Order)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get a single order by ID."""
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post(
    "",
    response_model=schemas.Order,
    status_code=status.HTTP_201_CREATED,
)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    """Create a new order."""
    try:
        return crud.create_order(db, order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{order_id}", response_model=schemas.Order)
def update_order(
    order_id: int,
    order: schemas.OrderUpdate,
    db: Session = Depends(get_db),
):
    """Update an order (e.g., change status)."""
    updated_order = crud.update_order(db, order_id, order)
    if not updated_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated_order


@router.get("/table/{table_number}/active", response_model=Optional[schemas.Order])
def get_active_table_order(table_number: int, db: Session = Depends(get_db)):
    """Check if a table has an active order."""
    order = crud.get_active_order_for_table(db, table_number)
    return order


# ============================================================================
# Payment Routes (nested under orders)
# ============================================================================


@router.post(
    "/{order_id}/payments",
    response_model=schemas.Payment,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    order_id: int,
    payment: schemas.PaymentCreate,
    db: Session = Depends(get_db),
):
    """Add a payment to an order."""
    try:
        return crud.create_payment(db, order_id, payment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}/payments", response_model=List[schemas.Payment])
def get_order_payments(order_id: int, db: Session = Depends(get_db)):
    """Get all payments for an order."""
    return crud.get_payments_for_order(db, order_id)
