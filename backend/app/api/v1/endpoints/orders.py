"""
Order and payment endpoints for Lily Cafe POS System.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app import schemas, crud
from app.models.models import OrderStatus
from app.api.deps import get_db, get_current_user
from app.utils.pdf_generator import generate_receipt
from app.utils.printer import print_receipt, print_order_chit
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


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


@router.get("/history", response_model=List[schemas.Order])
def get_order_history(
    date: Optional[str] = None,
    status: Optional[OrderStatus] = None,
    db: Session = Depends(get_db),
):
    """
    Get order history with optional date filtering.

    Query parameters:
    - date: Filter by date in YYYY-MM-DD format (e.g., "2024-11-01")
    - status: Filter by order status (active, paid, canceled)

    Returns:
        List of orders matching the filter criteria.
        By default, returns paid orders from the specified date.
    """
    try:
        # If no status specified, only return paid orders (completed transactions)
        # This is the expected behavior for order history
        filter_status = status if status else OrderStatus.PAID

        orders = crud.get_orders(
            db,
            status=filter_status,
            date_str=date,
        )
        return orders
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
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
    """
    Create a new order.

    If PRINTER_ENABLED=true, automatically prints an order chit (kitchen ticket)
    with table number, items, and space for handwritten notes.

    NOTE: When updating an existing order (adding items to a table with active order),
    only the NEW items are printed on the chit, not the previous items.
    """
    try:
        # create_order returns (order, new_items_only)
        new_order, new_items = crud.create_order(db, order)

        # Auto-print order chit if printer is enabled
        # Only print NEW items (not items that were already in the order)
        if settings.PRINTER_ENABLED:
            try:
                chit_printed = print_order_chit(new_order, items_to_print=new_items)
                if chit_printed:
                    logger.info(f"Order chit printed for table {new_order.table_number} ({len(new_items)} new items)")
                else:
                    logger.warning(f"Failed to print order chit for table {new_order.table_number}")
            except Exception as e:
                # Log error but don't fail the order creation
                logger.error(f"Error printing order chit: {e}")

        return new_order
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
# Order Item Routes (for marking items as served)
# ============================================================================


@router.patch("/{order_id}/items/{item_id}/served")
def update_item_served_status(
    order_id: int,
    item_id: int,
    quantity_to_serve: int,
    db: Session = Depends(get_db),
):
    """
    Update the served quantity of an order item.

    Used by admin to track how many items have been served to customers.
    Supports partial serving (e.g., serving 2 out of 5 items).

    Args:
        order_id: The order ID
        item_id: The order item ID
        quantity_to_serve: Number of items to mark as served (adds to current quantity_served)

    Returns:
        Success message with updated item info
    """
    try:
        updated_item = crud.update_order_item_served_quantity(db, order_id, item_id, quantity_to_serve)
        if not updated_item:
            raise HTTPException(status_code=404, detail="Order item not found")
        return {
            "message": "Item served quantity updated successfully",
            "item_id": item_id,
            "quantity_served": updated_item.quantity_served,
            "is_served": updated_item.is_served
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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


@router.put(
    "/{order_id}/payments",
    response_model=List[schemas.Payment],
)
def update_order_payments(
    order_id: int,
    payment_batch: schemas.PaymentBatchCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Replace all payments for an order (edit payment methods).

    This endpoint allows editing payment methods for already-paid orders.
    Useful for correcting payment method errors in order history.

    - Deletes all existing payments
    - Creates new payments with provided methods
    - Validates total matches order total
    - Requires authentication (admin only)

    Example request:
    {
        "payments": [
            {"payment_method": "cash", "amount": 23600}
        ]
    }
    """
    try:
        return crud.replace_order_payments(db, order_id, payment_batch.payments)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{order_id}/receipt")
def generate_receipt_endpoint(
    order_id: int,
    auto_print: bool = False,
    db: Session = Depends(get_db)
):
    """
    Generate and return a PDF receipt for a paid order.

      Query Parameters:
          auto_print: If true, automatically print to configured thermal printer (default: false)

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

    When auto_print=true:
    - Requires PRINTER_ENABLED=true in .env
    - Requires valid printer configuration (PRINTER_TYPE, etc.)
    - Will attempt to print to thermal printer automatically
    - PDF is still returned regardless of print success/failure
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

    # Auto-print if requested and printer is enabled
    if auto_print and settings.PRINTER_ENABLED:
        try:
            print_success = print_receipt(order)
            if print_success:
                print("✓ Receipt printed successfully")
            else:
                print("⚠ Print attempt failed - check printer configuration")
        except Exception as e:
            # Log error but don't fail the request - still return PDF
            print(f"⚠ Print error: {e}")

    # Generate PDF (always return PDF regardless of print status)
    pdf_buffer = BytesIO()
    # Use configured paper size (either "58mm" or "80mm")
    paper_size = settings.RECEIPT_PAPER_SIZE
    if paper_size not in ["58mm", "80mm"]:
        paper_size = "80mm"  # Default to 80mm if invalid
    generate_receipt(order, pdf_buffer, paper_size=paper_size)
    pdf_buffer.seek(0)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=receipt-{order.order_number}.pdf"
        }
    )





