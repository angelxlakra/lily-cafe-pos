"""
Thermal printer utility for direct ESC/POS printing.
Supports Windows (Win32Raw), USB, and Serial connections.
"""

import logging
from typing import Optional
from datetime import datetime

from app.core.config import settings
from app.models import models

logger = logging.getLogger(__name__)


def get_printer():
    """
    Get printer instance based on configuration.

    Returns:
        Printer instance or None if printer not enabled/configured

    Raises:
        ImportError: If python-escpos not installed
        ValueError: If printer configuration is invalid
        Exception: If printer connection fails
    """
    if not settings.PRINTER_ENABLED:
        logger.info("Printer is disabled in configuration")
        return None

    if not settings.PRINTER_TYPE:
        logger.warning("PRINTER_ENABLED is true but PRINTER_TYPE not set")
        return None

    try:
        from escpos.printer import Win32Raw, Usb, Serial
    except ImportError as e:
        logger.error("python-escpos library not installed. Run: uv add python-escpos")
        raise ImportError("python-escpos library not available") from e

    printer_type = settings.PRINTER_TYPE.lower()

    try:
        if printer_type == "win32":
            # Windows printer using Win32Raw
            if not settings.PRINTER_NAME:
                raise ValueError("PRINTER_NAME must be set for win32 printer type")
            logger.info(f"Connecting to Windows printer: {settings.PRINTER_NAME}")
            return Win32Raw(settings.PRINTER_NAME)

        elif printer_type == "usb":
            # USB printer
            if not settings.PRINTER_VENDOR_ID or not settings.PRINTER_PRODUCT_ID:
                raise ValueError("PRINTER_VENDOR_ID and PRINTER_PRODUCT_ID must be set for usb printer type")

            # Convert hex strings to integers
            vendor_id = int(settings.PRINTER_VENDOR_ID, 16) if isinstance(settings.PRINTER_VENDOR_ID, str) else settings.PRINTER_VENDOR_ID
            product_id = int(settings.PRINTER_PRODUCT_ID, 16) if isinstance(settings.PRINTER_PRODUCT_ID, str) else settings.PRINTER_PRODUCT_ID

            logger.info(f"Connecting to USB printer: VID={hex(vendor_id)}, PID={hex(product_id)}")
            return Usb(vendor_id, product_id)

        elif printer_type == "serial":
            # Serial port printer
            if not settings.PRINTER_PORT:
                raise ValueError("PRINTER_PORT must be set for serial printer type")
            logger.info(f"Connecting to serial printer: {settings.PRINTER_PORT} @ {settings.PRINTER_BAUDRATE} baud")
            return Serial(settings.PRINTER_PORT, baudrate=settings.PRINTER_BAUDRATE)

        else:
            raise ValueError(f"Invalid PRINTER_TYPE: {settings.PRINTER_TYPE}. Must be 'win32', 'usb', or 'serial'")

    except Exception as e:
        logger.error(f"Failed to connect to printer: {e}")
        raise


def format_currency(amount_in_paise: int) -> str:
    """Format currency for printing."""
    rupees = amount_in_paise / 100
    return f"Rs.{rupees:.2f}"


def print_receipt(order: models.Order) -> bool:
    """
    Print receipt directly to thermal printer using ESC/POS commands.

    Args:
        order: Order model instance with order details

    Returns:
        True if printing succeeded, False otherwise
    """
    if not settings.PRINTER_ENABLED:
        logger.info("Printer disabled - skipping print")
        return False

    printer = None
    try:
        printer = get_printer()
        if not printer:
            logger.warning("No printer configured")
            return False

        # Get paper width from settings
        paper_size = settings.RECEIPT_PAPER_SIZE
        is_58mm = paper_size == "58mm"

        # Initialize printer
        printer.set(align='center', bold=True, width=2, height=2)

        # ============================================================================
        # HEADER SECTION
        # ============================================================================

        printer.text("LILY\n")
        printer.set(align='center', bold=True, width=1, height=1)
        printer.text(f"{settings.RESTAURANT_NAME.replace('Lily ', '')}\n")
        printer.set(align='center', bold=False)
        printer.text(f"{settings.RESTAURANT_ADDRESS_LINE1}\n")
        printer.text(f"{settings.RESTAURANT_ADDRESS_LINE2}\n")

        if is_58mm:
            # Stack contact info for narrow paper
            printer.text(f"Tel: {settings.RESTAURANT_PHONE}\n")
            printer.text(f"{settings.RESTAURANT_EMAIL}\n")
        else:
            # Side by side for wider paper
            printer.text(f"Tel: {settings.RESTAURANT_PHONE} | {settings.RESTAURANT_EMAIL}\n")

        printer.text(f"GSTIN: {settings.RESTAURANT_GSTIN}\n")
        printer.text("\n")

        # Separator
        printer.set(align='center')
        printer.text("=" * (32 if is_58mm else 42) + "\n")
        printer.text("\n")

        # ============================================================================
        # ORDER INFORMATION
        # ============================================================================

        printer.set(align='left', bold=True)
        printer.text(f"Order No: {order.order_number}\n")
        printer.set(bold=False)

        # Format date/time
        from app.utils.pdf_generator import convert_to_local_timezone
        local_time = convert_to_local_timezone(order.created_at)
        printer.text(f"Date: {local_time.strftime('%d-%m-%Y %I:%M %p')}\n")

        if order.customer_name:
            printer.text(f"Customer: {order.customer_name}\n")

        printer.text("\n")

        # Table number (prominent)
        printer.set(align='center', bold=True, width=2, height=1)
        printer.text(f"Table {order.table_number}\n")
        printer.set(align='left', bold=False, width=1, height=1)
        printer.text("\n")

        # Separator
        printer.text("-" * (32 if is_58mm else 42) + "\n")

        # ============================================================================
        # ITEMS SECTION
        # ============================================================================

        printer.set(bold=True)
        if is_58mm:
            printer.text(f"{'Item':<20} {'Amt':>11}\n")
        else:
            printer.text(f"{'Item':<28} {'Amount':>13}\n")
        printer.set(bold=False)
        printer.text("-" * (32 if is_58mm else 42) + "\n")

        for item in order.order_items:
            # Item name with quantity
            item_text = f"{item.quantity}x {item.menu_item_name}"
            if len(item_text) > (20 if is_58mm else 28):
                item_text = item_text[:(17 if is_58mm else 25)] + "..."

            amount_text = format_currency(item.subtotal)

            if is_58mm:
                printer.text(f"{item_text:<20} {amount_text:>11}\n")
                printer.text(f"  @ {format_currency(item.unit_price)}\n")
            else:
                printer.text(f"{item_text:<28} {amount_text:>13}\n")
                printer.text(f"   @ {format_currency(item.unit_price)}\n")

        printer.text("-" * (32 if is_58mm else 42) + "\n")

        # ============================================================================
        # TOTALS SECTION
        # ============================================================================

        # Subtotal
        subtotal_text = format_currency(order.subtotal)
        if is_58mm:
            printer.text(f"{'Subtotal:':<20} {subtotal_text:>11}\n")
        else:
            printer.text(f"{'Subtotal:':<28} {subtotal_text:>13}\n")

        # GST breakdown
        half_gst_rate = settings.GST_RATE / 2
        cgst_amount = order.gst_amount // 2
        sgst_amount = order.gst_amount - cgst_amount

        cgst_text = format_currency(cgst_amount)
        sgst_text = format_currency(sgst_amount)

        if is_58mm:
            printer.text(f"CGST ({half_gst_rate}%): {cgst_text:>11}\n")
            printer.text(f"SGST ({half_gst_rate}%): {sgst_text:>11}\n")
        else:
            printer.text(f"{'CGST (' + str(half_gst_rate) + '%):':<28} {cgst_text:>13}\n")
            printer.text(f"{'SGST (' + str(half_gst_rate) + '%):':<28} {sgst_text:>13}\n")

        printer.text("-" * (32 if is_58mm else 42) + "\n")

        # Total (prominent)
        total_text = format_currency(order.total_amount)
        printer.set(bold=True, width=1, height=2)
        if is_58mm:
            printer.text(f"{'TOTAL:':<20} {total_text:>11}\n")
        else:
            printer.text(f"{'TOTAL:':<28} {total_text:>13}\n")
        printer.set(bold=False, width=1, height=1)

        printer.text("\n")

        # ============================================================================
        # FOOTER SECTION
        # ============================================================================

        printer.set(align='center')
        printer.text("=" * (32 if is_58mm else 42) + "\n")
        printer.text("\n")
        printer.text("Thank you for visiting!\n")
        printer.text("#withlovefrommary\n")
        printer.text("\n\n")

        # Cut paper (if supported)
        try:
            printer.cut()
        except:
            # Some printers don't support cut, that's okay
            printer.text("\n\n\n")

        logger.info(f"Successfully printed receipt for order {order.order_number}")
        return True

    except Exception as e:
        logger.error(f"Failed to print receipt for order {order.order_number if order else 'unknown'}: {e}")
        return False

    finally:
        # Close printer connection
        if printer:
            try:
                printer.close()
            except:
                pass


def print_order_chit(order: models.Order) -> bool:
    """
    Print a simple order chit (kitchen ticket) when order is saved.

    Minimal design with:
    - Large table number
    - Order items with quantities
    - Amounts
    - Space for handwritten notes

    No branding, no GST breakdown - just essentials for kitchen/waiters.

    Args:
        order: Order model instance with order details

    Returns:
        True if printing succeeded, False otherwise
    """
    if not settings.PRINTER_ENABLED:
        logger.info("Printer disabled - skipping order chit print")
        return False

    printer = None
    try:
        printer = get_printer()
        if not printer:
            logger.warning("No printer configured")
            return False

        # Get paper width from settings
        paper_size = settings.RECEIPT_PAPER_SIZE
        is_58mm = paper_size == "58mm"

        # ============================================================================
        # HEADER - Maximum Size Table Number
        # ============================================================================

        printer.set(align='center', bold=True, width=8, height=8)
        printer.text(f"TABLE {order.table_number}\n")
        printer.set(align='center', bold=False, width=1, height=1)
        printer.text("\n")

        # Order info
        from app.utils.pdf_generator import convert_to_local_timezone
        local_time = convert_to_local_timezone(order.created_at)
        printer.text(f"Order: {order.order_number}\n")
        printer.text(f"Time: {local_time.strftime('%I:%M %p')}\n")

        if order.customer_name:
            printer.text(f"Name: {order.customer_name}\n")

        printer.text("\n")

        # Separator
        printer.set(align='center')
        printer.text("=" * (32 if is_58mm else 42) + "\n")
        printer.text("\n")

        # ============================================================================
        # ITEMS SECTION - Large, readable text (no prices)
        # ============================================================================

        printer.set(align='left', bold=True, width=1, height=2)

        for item in order.order_items:
            # Item with large quantity (no price)
            printer.text(f"{item.quantity}x {item.menu_item_name}\n")
            printer.text("\n")

        # Reset to normal
        printer.set(bold=False, width=1, height=1)

        # Separator
        printer.set(align='center')
        printer.text("=" * (32 if is_58mm else 42) + "\n")
        printer.text("\n")

        # ============================================================================
        # NOTES SECTION - Space for handwritten notes
        # ============================================================================

        printer.set(align='left')
        printer.text("-" * (32 if is_58mm else 42) + "\n")
        printer.text("NOTES:\n")
        printer.text("\n")
        printer.text("\n")
        printer.text("\n")
        printer.text("\n")
        printer.text("\n")
        printer.text("-" * (32 if is_58mm else 42) + "\n")
        printer.text("\n\n")

        # Cut paper (if supported)
        try:
            printer.cut()
        except:
            # Some printers don't support cut, that's okay
            printer.text("\n\n\n")

        logger.info(f"Successfully printed order chit for table {order.table_number}")
        return True

    except Exception as e:
        logger.error(f"Failed to print order chit for order {order.order_number if order else 'unknown'}: {e}")
        return False

    finally:
        # Close printer connection
        if printer:
            try:
                printer.close()
            except:
                pass


def test_printer() -> bool:
    """
    Test printer connection by printing a test receipt.

    Returns:
        True if test succeeded, False otherwise
    """
    if not settings.PRINTER_ENABLED:
        logger.info("Printer is disabled")
        return False

    printer = None
    try:
        printer = get_printer()
        if not printer:
            logger.warning("No printer configured")
            return False

        # Print test page
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text("TEST RECEIPT\n")
        printer.set(bold=False, width=1, height=1)
        printer.text("\n")
        printer.text(f"{settings.RESTAURANT_NAME}\n")
        printer.text("\n")
        printer.text("Printer Test Successful!\n")
        printer.text(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        printer.text("\n")
        printer.text("=" * 42 + "\n")
        printer.text("\n\n")

        try:
            printer.cut()
        except:
            printer.text("\n\n\n")

        logger.info("Printer test successful")
        return True

    except Exception as e:
        logger.error(f"Printer test failed: {e}")
        return False

    finally:
        if printer:
            try:
                printer.close()
            except:
                pass
