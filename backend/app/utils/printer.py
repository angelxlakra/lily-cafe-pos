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


# ASCII art for digits 0-9 using hash symbols (for huge, readable table numbers)
ASCII_DIGITS = {
    '0': [
        " ##### ",
        "#     #",
        "#     #",
        "#     #",
        "#     #",
        "#     #",
        " ##### "
    ],
    '1': [
        "   #   ",
        "  ##   ",
        "   #   ",
        "   #   ",
        "   #   ",
        "   #   ",
        " ##### "
    ],
    '2': [
        " ##### ",
        "#     #",
        "      #",
        " ##### ",
        "#      ",
        "#      ",
        "#######"
    ],
    '3': [
        " ##### ",
        "#     #",
        "      #",
        "  #### ",
        "      #",
        "#     #",
        " ##### "
    ],
    '4': [
        "#     #",
        "#     #",
        "#     #",
        "#######",
        "      #",
        "      #",
        "      #"
    ],
    '5': [
        "#######",
        "#      ",
        "#      ",
        "###### ",
        "      #",
        "#     #",
        " ##### "
    ],
    '6': [
        " ##### ",
        "#     #",
        "#      ",
        "###### ",
        "#     #",
        "#     #",
        " ##### "
    ],
    '7': [
        "#######",
        "      #",
        "     # ",
        "    #  ",
        "   #   ",
        "  #    ",
        " #     "
    ],
    '8': [
        " ##### ",
        "#     #",
        "#     #",
        " ##### ",
        "#     #",
        "#     #",
        " ##### "
    ],
    '9': [
        " ##### ",
        "#     #",
        "#     #",
        " ######",
        "      #",
        "#     #",
        " ##### "
    ]
}


def create_ascii_art_number(number: int) -> list:
    """
    Create ASCII art representation of a number using the number itself.

    Example: Number "7" is drawn using multiple "7"s to form the shape of 7.

    Args:
        number: The number to convert (0-99)

    Returns:
        List of strings, each representing one line of the ASCII art
    """
    num_str = str(number)

    # For single digit
    if len(num_str) == 1:
        # Replace '#' with the actual digit to make it self-referential
        digit = num_str[0]
        art = ASCII_DIGITS[digit]
        return [line.replace('#', digit) for line in art]

    # For two digits, combine them side by side
    if len(num_str) == 2:
        digit1_char = num_str[0]
        digit2_char = num_str[1]

        # Get art for each digit and replace # with the actual digit
        digit1_art = [line.replace('#', digit1_char) for line in ASCII_DIGITS[digit1_char]]
        digit2_art = [line.replace('#', digit2_char) for line in ASCII_DIGITS[digit2_char]]

        # Combine side by side with spacing
        combined = []
        for i in range(len(digit1_art)):
            combined.append(digit1_art[i] + "  " + digit2_art[i])

        return combined

    # For 3+ digits, just return the number as is
    return [f"  {num_str}  "]


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


def _auto_print_pdf(pdf_path: str, printer_name: str) -> bool:
    """
    Automatically print a PDF file to the specified printer.
    Tries multiple methods to ensure printing works.

    Args:
        pdf_path: Path to the PDF file
        printer_name: Name of the printer

    Returns:
        True if printing succeeded, False otherwise
    """
    if not printer_name:
        logger.warning("No printer name provided for auto-print")
        return False

    # Method 1: Try GSPrint or Ghostscript (if installed)
    try:
        gsprint_paths = [
            r"C:\Program Files\Ghostgum\gsview\gsprint.exe",
            r"C:\Program Files (x86)\Ghostgum\gsview\gsprint.exe",
        ]
        for gsprint_path in gsprint_paths:
            if os.path.exists(gsprint_path):
                logger.info(f"Trying GSPrint: {gsprint_path}")
                result = subprocess.run(
                    [gsprint_path, "-printer", printer_name, pdf_path],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info("✓ Printed via GSPrint")
                    return True
    except Exception as e:
        logger.debug(f"GSPrint not available: {e}")

    # Method 2: Try Adobe Reader command line (if installed)
    try:
        adobe_paths = [
            r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
            r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
            r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
        ]
        for adobe_path in adobe_paths:
            if os.path.exists(adobe_path):
                logger.info(f"Trying Adobe Reader: {adobe_path}")
                result = subprocess.run(
                    [adobe_path, "/t", pdf_path, printer_name],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info("✓ Printed via Adobe Reader")
                    return True
    except Exception as e:
        logger.debug(f"Adobe Reader not available: {e}")

    # Method 3: Try PowerShell with Out-Printer
    try:
        logger.info("Trying PowerShell Out-Printer")
        ps_command = f'Get-Content "{pdf_path}" -Raw | Out-Printer -Name "{printer_name}"'
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info("✓ Printed via PowerShell")
            return True
    except Exception as e:
        logger.debug(f"PowerShell printing failed: {e}")

    # Method 4: Try using default Windows print handler
    try:
        logger.info("Trying Windows ShellExecute print verb")
        import win32api
        win32api.ShellExecute(
            0,
            "print",
            pdf_path,
            None,
            ".",
            0
        )
        logger.info("✓ Sent to Windows print handler")
        return True
    except Exception as e:
        logger.debug(f"ShellExecute print failed: {e}")

    logger.error("All auto-print methods failed")
    return False


def print_order_chit(order: models.Order, items_to_print: list[models.OrderItem] = None) -> bool:
    """
    Print a simple order chit (kitchen ticket) when order is saved.

    Uses ESC/POS commands for direct thermal printer communication.
    Also saves a PDF copy for records.

    Minimal design with:
    - Large table number
    - Order items with quantities (NO PRICES)
    - Space for handwritten notes

    Args:
        order: Order model instance with order details
        items_to_print: Optional list of specific OrderItems to print.
                       If None, prints all items in the order.
                       Use this to print only NEW items when updating an existing order.

    Returns:
        True if printing succeeded, False otherwise
    """
    if not settings.PRINTER_ENABLED:
        logger.info("Printer disabled - skipping order chit print")
        return False

    # Determine which items to print
    if items_to_print is None:
        items_to_print = order.order_items

    # Get paper width from settings
    paper_size = settings.RECEIPT_PAPER_SIZE
    if paper_size not in ["58mm", "80mm"]:
        paper_size = "80mm"  # Default to 80mm if invalid

    try:
        item_count = len(items_to_print)
        logger.info(f"Generating order chit for table {order.table_number}, order {order.order_number} ({item_count} items)")

        # Separate items into dine-in and parcel
        dine_in_items = [item for item in items_to_print if not item.is_parcel]
        parcel_items = [item for item in items_to_print if item.is_parcel]

        success = True

        # Print dine-in chit if there are dine-in items
        if dine_in_items:
            logger.info(f"Printing dine-in chit for table {order.table_number} ({len(dine_in_items)} items)")
            
            # Generate PDF for records
            try:
                from app.utils.pdf_generator import generate_order_chit_pdf
                chits_dir = os.path.join(os.getcwd(), "chits")
                os.makedirs(chits_dir, exist_ok=True)
                pdf_filename = f"Table_{order.table_number}_{order.order_number}_DINEIN.pdf"
                pdf_path = os.path.join(chits_dir, pdf_filename)

                with open(pdf_path, "wb") as pdf_file:
                    generate_order_chit_pdf(order, pdf_file, paper_size=paper_size, items_to_print=dine_in_items, is_parcel=False)
                logger.info(f"✓ PDF saved to: {pdf_path}")
            except Exception as e:
                logger.warning(f"Failed to save PDF copy: {e}")

            # Print using ESC/POS commands
            if not _print_order_chit_escpos(order, dine_in_items, paper_size, is_parcel=False):
                success = False

        # Print parcel chit if there are parcel items
        if parcel_items:
            logger.info(f"Printing parcel chit for table {order.table_number} ({len(parcel_items)} items)")
            
            # Generate PDF for records
            try:
                from app.utils.pdf_generator import generate_order_chit_pdf
                chits_dir = os.path.join(os.getcwd(), "chits")
                os.makedirs(chits_dir, exist_ok=True)
                pdf_filename = f"Table_{order.table_number}_{order.order_number}_PARCEL.pdf"
                pdf_path = os.path.join(chits_dir, pdf_filename)

                with open(pdf_path, "wb") as pdf_file:
                    generate_order_chit_pdf(order, pdf_file, paper_size=paper_size, items_to_print=parcel_items, is_parcel=True)
                logger.info(f"✓ PDF saved to: {pdf_path}")
            except Exception as e:
                logger.warning(f"Failed to save PDF copy: {e}")

            # Print using ESC/POS commands
            if not _print_order_chit_escpos(order, parcel_items, paper_size, is_parcel=True):
                success = False

        return success

    except Exception as e:
        logger.error(f"Failed to print order chit: {e}", exc_info=True)
        return False


def _print_order_chit_escpos(order: models.Order, items_to_print: list[models.OrderItem], paper_size: str = "80mm", is_parcel: bool = False) -> bool:
    """
    Print order chit using ESC/POS commands.

    Args:
        order: Order model instance
        items_to_print: List of OrderItems to print on the chit
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
        # HEADER - Table Number (LARGE and CLEAR!)
        # ============================================================================

        # Print table number in large, bold text
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text(f"TABLE {order.table_number}\n")

        # Reset to normal
        printer.set(bold=False, width=1, height=1)
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
        # ITEMS SECTION - Large, readable text (NO PRICES)
        # ============================================================================

        for item in items_to_print:
            # Format beverages differently (underlined) to distinguish from food
            if item.is_beverage:
                printer.set(align='left', bold=True, underline=True, width=2, height=2)
            else:
                printer.set(align='left', bold=True, underline=False, width=2, height=2)

            # Item with large quantity (NO PRICE - kitchen doesn't need it)
            printer.text(f"{item.quantity}x {item.menu_item_name}\n")
            printer.text("\n")  # Blank line for spacing

        # Reset to normal
        printer.set(bold=False, underline=False, width=1, height=1)

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
        printer.text("\n")

        # ============================================================================
        # PARCEL IDENTIFIER - Show at bottom if this is a parcel chit
        # ============================================================================
        if is_parcel:
            printer.set(align='center')
            printer.text("=" * (32 if is_58mm else 42) + "\n")
            printer.set(bold=True, width=2, height=2)
            printer.text("PARCEL\n")
            printer.set(bold=False, width=1, height=1)
            printer.text("=" * (32 if is_58mm else 42) + "\n")
            printer.text("\n")

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
