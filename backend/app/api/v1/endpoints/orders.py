"""
Order and payment endpoints for Lily Cafe POS System.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app import schemas, crud
from app.models.models import OrderStatus
from app.api.deps import get_db, get_current_user
from app.utils.pdf_generator import generate_receipt

router = APIRouter()


# ============================================================================
# Order Routes
# ============================================================================


@router.get("/active", response_model=List[schemas.Order])
def list_active_orders(db: Session = Depends(get_db)):
    """
    Get all active (unpaid) orders.

    This endpoint is used by waiters to see all ongoing orders across all tables.
    """
    return crud.get_orders(db, status=OrderStatus.ACTIVE)


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
    """Update an order (e.g., change status, customer name)."""
    updated_order = crud.update_order(db, order_id, order)
    if not updated_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated_order


@router.put("/{order_id}", response_model=schemas.Order)
def admin_edit_order(
    order_id: int,
    order_update: schemas.OrderItemsUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Admin endpoint to edit order items and recalculate totals.

    Requires authentication. Replaces all items in the order.
    Used to fix order mistakes or handle customer change requests.
    """
    try:
        updated_order = crud.admin_edit_order(db, order_id, order_update)
        if not updated_order:
            raise HTTPException(status_code=404, detail="Order not found")
        return updated_order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{order_id}")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Admin endpoint to cancel an order (soft delete).

    Requires authentication. Sets order status to CANCELED.
    Canceled orders remain in database for record keeping.
    Cannot cancel orders that have already been paid.
    """
    try:
        canceled_order = crud.cancel_order(db, order_id)
        if not canceled_order:
            raise HTTPException(status_code=404, detail="Order not found")
        return {"message": "Order canceled successfully", "order_id": order_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{order_id}/payments", response_model=List[schemas.Payment])
def get_order_payments(order_id: int, db: Session = Depends(get_db)):
    """Get all payments for an order."""
    return crud.get_payments_for_order(db, order_id)


@router.post(
    "/{order_id}/payments/batch", 
    response_model=List[schemas.Payment],
    status_code=status.HTTP_201_CREATED
)
def create_payments_batch(
    order_id: int,
    payment_batch: schemas.PaymentBatchCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add multiple payments to an order at once (split payment support).

      This endpoint is preferred for completing orders with split payments as it:
      - Validates total payments equal order total before creating any payments
      - Creates all payments atomically (all-or-nothing)
      - Automatically marks order as paid when complete

      Requires authentication (admin/cashier only).

      Example request:
      {
          "payments": [
              {"payment_method": "upi", "amount": 20000},
              {"payment_method": "cash", "amount": 3600}
          ]
      }
    """

    try:
        return crud.create_payments_batch(db, order_id, payment_batch.payments)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{order_id}/receipt")
def generate_receipt_endpoint(
    order_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate and return a PDF receipt for a paid order.

      Returns:
          PDF file formatted for 80mm thermal printer

      The receipt includes:
      - Restaurant details and GSTIN
      - Order number, table, date/time
      - All items with quantities and prices
      - Subtotal, GST breakdown, total
      - Payment methods used

    Note: This endpoint does NOT require authentication so waiters
    can print receipts without admin login.
    """

    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PAID:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate receipt for unpaid order"
        )

    if not order.payments:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate receipt - no payment found!"
        )
    
    pdf_buffer = BytesIO()
    generate_receipt(order, pdf_buffer)
    pdf_buffer.seek(0)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=receipt-{order.order_number}.pdf"
        }
    )





