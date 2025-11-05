"""
Order Chit (Kitchen Ticket) PDF generator for Lily Cafe POS System.
Generates simple, large-text chits for kitchen staff.
"""

import io
import tempfile
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.core.config import settings
from app.models import models


def generate_order_chit_pdf(order: models.Order) -> io.BytesIO:
    """
    Generate a PDF order chit with large table number and items.

    Args:
        order: Order model instance

    Returns:
        BytesIO buffer containing the PDF
    """
    # Paper size (80mm width)
    paper_size = settings.RECEIPT_PAPER_SIZE
    if paper_size == "58mm":
        receipt_width = 58 * mm
    else:
        receipt_width = 80 * mm

    receipt_height = 280 * mm  # Ample height

    # Create PDF in memory
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(receipt_width, receipt_height))

    y_position = receipt_height - (10 * mm)
    x_center = receipt_width / 2

    c.setFillColor(colors.black)

    # ============================================================================
    # GIANT TABLE NUMBER
    # ============================================================================

    # Draw "TABLE" text (very large)
    c.setFont("Helvetica-Bold", 72)  # 72pt = 1 inch tall!
    table_text = f"TABLE {order.table_number}"
    text_width = c.stringWidth(table_text, "Helvetica-Bold", 72)
    c.drawString(x_center - text_width / 2, y_position, table_text)
    y_position -= 30 * mm

    # Separator line
    c.setLineWidth(2)
    c.line(5 * mm, y_position, receipt_width - 5 * mm, y_position)
    y_position -= 8 * mm

    # ============================================================================
    # ORDER INFO (smaller text)
    # ============================================================================

    c.setFont("Helvetica", 10)

    # Order number
    c.drawString(5 * mm, y_position, f"Order: {order.order_number}")
    y_position -= 5 * mm

    # Time
    from app.utils.pdf_generator import convert_to_local_timezone
    local_time = convert_to_local_timezone(order.created_at)
    c.drawString(5 * mm, y_position, f"Time: {local_time.strftime('%I:%M %p')}")
    y_position -= 5 * mm

    # Customer name if provided
    if order.customer_name:
        c.drawString(5 * mm, y_position, f"Name: {order.customer_name}")
        y_position -= 5 * mm

    y_position -= 3 * mm

    # Separator line
    c.setLineWidth(1)
    c.line(5 * mm, y_position, receipt_width - 5 * mm, y_position)
    y_position -= 8 * mm

    # ============================================================================
    # ITEMS (Large, readable text - NO PRICES)
    # ============================================================================

    c.setFont("Helvetica-Bold", 24)  # Large items

    for item in order.order_items:
        item_text = f"{item.quantity}x {item.menu_item_name}"

        # Word wrap if text is too long
        max_width = receipt_width - 10 * mm
        if c.stringWidth(item_text, "Helvetica-Bold", 24) > max_width:
            # Try to fit, if not, truncate
            words = item_text.split()
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                if c.stringWidth(test_line, "Helvetica-Bold", 24) <= max_width:
                    current_line.append(word)
                else:
                    # Print current line
                    c.drawString(5 * mm, y_position, ' '.join(current_line))
                    y_position -= 10 * mm
                    current_line = [word]

            # Print remaining
            if current_line:
                c.drawString(5 * mm, y_position, ' '.join(current_line))
                y_position -= 10 * mm
        else:
            c.drawString(5 * mm, y_position, item_text)
            y_position -= 10 * mm

        y_position -= 3 * mm  # Extra space between items

    y_position -= 5 * mm

    # Separator line
    c.setLineWidth(1)
    c.line(5 * mm, y_position, receipt_width - 5 * mm, y_position)
    y_position -= 10 * mm

    # ============================================================================
    # NOTES SECTION
    # ============================================================================

    c.setFont("Helvetica", 10)
    c.drawString(5 * mm, y_position, "NOTES:")
    y_position -= 8 * mm

    # Draw lines for handwritten notes
    for _ in range(5):
        c.setLineWidth(0.5)
        c.setStrokeColor(colors.grey)
        c.line(5 * mm, y_position, receipt_width - 5 * mm, y_position)
        y_position -= 7 * mm

    # Save PDF
    c.showPage()
    c.save()

    pdf_buffer.seek(0)
    return pdf_buffer


def save_and_print_chit(order: models.Order) -> bool:
    """
    Generate order chit PDF and automatically send to printer.

    Args:
        order: Order model instance

    Returns:
        True if printing succeeded, False otherwise
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Generate PDF
        pdf_buffer = generate_order_chit_pdf(order)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_buffer.getvalue())
            tmp_file_path = tmp_file.name

        # Auto-print using Windows
        import platform
        if platform.system() == 'Windows':
            import win32print
            import win32api

            # Get configured printer name
            printer_name = settings.PRINTER_NAME
            if not printer_name:
                # Use default printer
                printer_name = win32print.GetDefaultPrinter()

            # Send to printer
            win32api.ShellExecute(
                0,
                "print",
                tmp_file_path,
                f'/d:"{printer_name}"',
                ".",
                0
            )

            logger.info(f"Order chit PDF sent to printer '{printer_name}' for table {order.table_number}")
            return True
        else:
            # On non-Windows, just log (could use lpr command on Linux/Mac)
            logger.warning(f"Auto-print not supported on {platform.system()}, PDF saved to {tmp_file_path}")
            return False

    except Exception as e:
        logger.error(f"Failed to generate/print order chit: {e}")
        return False
