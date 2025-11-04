"""
Thermal printer utility for direct ESC/POS printing and PDF-based printing.
Supports Windows (Win32Raw), USB, and Serial connections.
Also supports PDF-based printing for better font control.
"""

import logging
import os
import tempfile
import subprocess
import platform
from typing import Optional
from datetime import datetime
from io import BytesIO

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


def print_pdf_to_printer(pdf_path: str, printer_name: str = None) -> bool:
    """
    Print a PDF file to a thermal printer using system commands.

    This function tries multiple methods to print the PDF:
    1. SumatraPDF (Windows) - Best for silent printing
    2. Windows default print command
    3. Linux CUPS (lp command)

    Args:
        pdf_path: Path to the PDF file to print
        printer_name: Name of the printer (uses PRINTER_NAME from settings if not provided)

    Returns:
        True if printing succeeded, False otherwise
    """
    if printer_name is None:
        printer_name = settings.PRINTER_NAME

    if not printer_name:
        logger.error("No printer name configured for PDF printing")
        return False

    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return False

    system = platform.system()

    try:
        if system == "Windows":
            # Method 1: Try SumatraPDF (best for silent printing)
            sumatra_paths = [
                r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
                r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\SumatraPDF\SumatraPDF.exe"),
            ]

            for sumatra_path in sumatra_paths:
                if os.path.exists(sumatra_path):
                    logger.info(f"Printing PDF using SumatraPDF to {printer_name}")
                    result = subprocess.run(
                        [sumatra_path, "-print-to", printer_name, pdf_path],
                        capture_output=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        logger.info("PDF printed successfully via SumatraPDF")
                        return True
                    else:
                        logger.warning(f"SumatraPDF print failed: {result.stderr.decode()}")

            # Method 2: Use Windows shell print command via PowerShell
            logger.info("Trying Windows print command via PowerShell")
            ps_command = f'''
            $printer = Get-Printer -Name "{printer_name}" -ErrorAction SilentlyContinue
            if ($printer) {{
                Start-Process -FilePath "{pdf_path}" -Verb PrintTo -ArgumentList '"{printer_name}"' -WindowStyle Hidden
                exit 0
            }} else {{
                exit 1
            }}
            '''
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0:
                logger.info("PDF sent to printer via PowerShell")
                return True
            else:
                logger.warning(f"PowerShell print failed: {result.stderr.decode()}")

            # Method 3: Use win32print library if available
            try:
                import win32print
                import win32api

                logger.info("Trying win32print library")
                win32api.ShellExecute(
                    0,
                    "printto",
                    pdf_path,
                    f'"{printer_name}"',
                    ".",
                    0
                )
                logger.info("PDF sent to printer via win32print")
                return True
            except ImportError:
                logger.warning("win32print library not available")
            except Exception as e:
                logger.warning(f"win32print failed: {e}")

        elif system == "Linux":
            # Linux: Use CUPS lp command
            logger.info(f"Printing PDF using lp command to {printer_name}")
            result = subprocess.run(
                ["lp", "-d", printer_name, pdf_path],
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0:
                logger.info("PDF printed successfully via lp")
                return True
            else:
                logger.error(f"lp command failed: {result.stderr.decode()}")
                return False

        else:
            logger.error(f"Unsupported operating system for PDF printing: {system}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("Print command timed out")
        return False
    except Exception as e:
        logger.error(f"Failed to print PDF: {e}")
        return False

    # If we got here, all methods failed
    logger.error("All PDF printing methods failed")
    return False


def print_order_chit(order: models.Order) -> bool:
    """
    Print a simple order chit (kitchen ticket) when order is saved.

    Uses PDF-based printing for better font control and larger table numbers.
    Falls back to ESC/POS if PDF printing is not available.

    Minimal design with:
    - Very large table number (72pt font, much larger than ESC/POS 8x limit)
    - Order items with quantities
    - Total amount
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

    # Get paper width from settings
    paper_size = settings.RECEIPT_PAPER_SIZE
    if paper_size not in ["58mm", "80mm"]:
        paper_size = "80mm"  # Default to 80mm if invalid

    temp_pdf_path = None

    try:
        # Method 1: PDF-based printing (preferred for better font control)
        if settings.PRINTER_NAME:  # PDF printing requires printer name
            logger.info("Attempting PDF-based chit printing for better font control")

            # Generate PDF to temporary file
            from app.utils.pdf_generator import generate_order_chit_pdf

            # Create temporary file
            temp_fd, temp_pdf_path = tempfile.mkstemp(suffix=".pdf", prefix="chit_")
            os.close(temp_fd)  # Close the file descriptor

            # Generate the PDF
            with open(temp_pdf_path, "wb") as pdf_file:
                generate_order_chit_pdf(order, pdf_file, paper_size=paper_size)

            # Print the PDF
            print_success = print_pdf_to_printer(temp_pdf_path, settings.PRINTER_NAME)

            if print_success:
                logger.info(f"Successfully printed PDF order chit for table {order.table_number}")
                return True
            else:
                logger.warning("PDF printing failed, falling back to ESC/POS")

        # Method 2: ESC/POS fallback (if PDF printing failed or not configured)
        logger.info("Using ESC/POS fallback for chit printing")
        return _print_order_chit_escpos(order, paper_size)

    except Exception as e:
        logger.error(f"Failed to print order chit for order {order.order_number if order else 'unknown'}: {e}")
        # Try ESC/POS fallback on error
        try:
            logger.info("Attempting ESC/POS fallback after error")
            return _print_order_chit_escpos(order, paper_size)
        except Exception as fallback_error:
            logger.error(f"ESC/POS fallback also failed: {fallback_error}")
            return False

    finally:
        # Clean up temporary file
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary PDF file: {e}")


def _print_order_chit_escpos(order: models.Order, paper_size: str = "80mm") -> bool:
    """
    Print order chit using ESC/POS commands (fallback method).

    This is the original implementation that uses direct ESC/POS commands.
    Limited to 8x font size maximum.

    Args:
        order: Order model instance
        paper_size: Paper size (58mm or 80mm)

    Returns:
        True if printing succeeded, False otherwise
    """
    printer = None
    try:
        printer = get_printer()
        if not printer:
            logger.warning("No printer configured for ESC/POS")
            return False

        is_58mm = paper_size == "58mm"

        # ============================================================================
        # HEADER - Maximum Size Table Number (ESC/POS limit: 8x8)
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
        # ITEMS SECTION - Large, readable text
        # ============================================================================

        printer.set(align='left', bold=True, width=1, height=2)

        for item in order.order_items:
            # Item with large quantity
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

        logger.info(f"Successfully printed ESC/POS order chit for table {order.table_number}")
        return True

    except Exception as e:
        logger.error(f"Failed to print ESC/POS order chit: {e}")
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
