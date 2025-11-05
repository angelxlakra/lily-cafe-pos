"""
PDF receipt generator for Lily Cafe POS System.
Generates thermal printer-compatible receipts for 58mm and 80mm paper.
Follows design specifications from docs/receipt-design-instructions.md
"""

import io
import os
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Literal
from zoneinfo import ZoneInfo

import qrcode
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.core.config import settings
from app.models import models

# Font setup
BACKEND_DIR = Path(__file__).parent.parent.parent
FONT_PATH = BACKEND_DIR / "public" / "fonts" / "dejavu" / "DejaVuSansMono.ttf"

if FONT_PATH.exists():
    pdfmetrics.registerFont(TTFont("DejaVuSansMono", str(FONT_PATH)))
else:
    raise FileNotFoundError(f"Font file not found at {FONT_PATH}")

# Paper size type
PaperSize = Literal["58mm", "80mm"]


class ReceiptConfig:
    """Configuration for receipt generation based on paper size."""

    def __init__(self, paper_size: PaperSize = "80mm"):
        self.paper_size = paper_size

        if paper_size == "58mm":
            # 58mm Paper Configuration (Compact)
            self.paper_width_mm = 58
            self.side_margin_mm = 3
            self.top_margin_mm = 5
            self.qr_size = 80
            self.qr_layout = "stacked"

            # Typography (58mm)
            self.font_cafe_name = 14
            self.font_cafe_sub_name = 8
            self.font_address = 8
            self.font_contact = 8
            self.font_gstin = 8
            self.font_order_number = 8
            self.font_order_details = 9
            self.font_section_header = 11
            self.font_item_name = 10
            self.font_amount = 10
            self.font_subtotal = 10
            self.font_total = 14
            self.font_payment = 10
            self.font_footer = 9
            self.font_qr_label = 8

            # Spacing
            self.section_spacing = 12
            self.item_spacing = 7
            self.line_height = 3.5 * mm
            self.small_line_height = 2.8 * mm

        else:  # 80mm Paper Configuration (Standard)
            self.paper_width_mm = 80
            self.side_margin_mm = 5
            self.top_margin_mm = 6
            self.qr_size = 100
            self.qr_layout = "side-by-side"

            # Typography (80mm) - Adjusted for better fit
            self.font_cafe_name = 16  # Smaller for better fit
            self.font_cafe_sub_name = 10
            self.font_address = 8
            self.font_contact = 8
            self.font_gstin = 8
            self.font_order_number = 12
            self.font_order_details = 9
            self.font_section_header = 11
            self.font_item_name = 10
            self.font_amount = 10
            self.font_subtotal = 10
            self.font_total = 14  # Prominent but not too large
            self.font_payment = 10
            self.font_footer = 9
            self.font_qr_label = 8

            # Spacing - More generous
            self.section_spacing = 18
            self.item_spacing = 10
            self.line_height = 4.5 * mm
            self.small_line_height = 3.5 * mm

        # Common calculations
        self.receipt_width = self.paper_width_mm * mm
        self.content_width = (self.paper_width_mm - (2 * self.side_margin_mm)) * mm
        self.left_margin = self.side_margin_mm * mm
        self.right_margin = self.receipt_width - self.left_margin
        self.receipt_height = 280 * mm  # Ample height, printer will trim


def format_currency(amount_in_paise: int) -> str:
    """Format currency with rupee symbol and 2 decimal places."""
    rupees = amount_in_paise / 100
    return f"₹{rupees:.2f}"


def convert_to_local_timezone(utc_datetime: datetime) -> datetime:
    """
    Convert UTC datetime to the configured local timezone.

    Args:
        utc_datetime: Naive datetime assumed to be in UTC

    Returns:
        Datetime converted to the configured timezone
    """
    # If datetime is naive, assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=ZoneInfo("UTC"))

    # Convert to configured timezone
    local_tz = ZoneInfo(settings.TIMEZONE)
    return utc_datetime.astimezone(local_tz)


def generate_qr_code(data: str, size: int = 100) -> ImageReader:
    """Generate QR code image from data."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to ImageReader for ReportLab
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return ImageReader(buffer)


def generate_receipt(
    order: models.Order, output: BinaryIO, paper_size: PaperSize = "80mm"
) -> None:
    """
    Generate a styled receipt PDF for the provided order.

    Args:
        order: Order model instance
        output: Binary output stream for PDF
        paper_size: Paper width - either "58mm" or "80mm" (default: "80mm")
    """
    config = ReceiptConfig(paper_size)
    c = canvas.Canvas(output, pagesize=(config.receipt_width, config.receipt_height))

    y_position = config.receipt_height - (config.top_margin_mm * mm)
    x_center = config.receipt_width / 2

    c.setFillColor(colors.black)

    # Helper functions
    def draw_centered(text: str, y: float, font: str = "Helvetica", size: float = 10, max_width: float = None, wrap: bool = False):
        """Draw centered text with optional text wrapping."""
        c.setFont(font, size)
        if max_width is None:
            max_width = config.content_width

        width = c.stringWidth(text, font, size)

        # If text fits, draw it normally
        if width <= max_width:
            c.drawString(x_center - width / 2, y, text)
            return y  # Return the y position after drawing
        elif wrap:
            # Text is too long, wrap across multiple lines
            words = text.split()
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                if c.stringWidth(test_line, font, size) <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        # Single word too long, just use it
                        lines.append(word)

            if current_line:
                lines.append(' '.join(current_line))

            # Draw all lines
            line_spacing = size * 1.2
            current_y = y
            for line in lines:
                line_width = c.stringWidth(line, font, size)
                c.drawString(x_center - line_width / 2, current_y, line)
                current_y -= line_spacing

            return current_y  # Return the final y position
        else:
            # Just draw the text (it will overflow, but that's the fallback)
            c.drawString(x_center - width / 2, y, text)
            return y

    def draw_left(text: str, y: float, font: str = "Helvetica", size: float = 9):
        """Draw left-aligned text."""
        c.setFont(font, size)
        c.drawString(config.left_margin, y, text)

    def draw_right(text: str, y: float, font: str = "Helvetica", size: float = 9):
        """Draw right-aligned text."""
        c.setFont(font, size)
        width = c.stringWidth(text, font, size)
        c.drawString(config.right_margin - width, y, text)

    def draw_separator(y: float, thickness: float = 0.35, color: str = "#CCCCCC"):
        """Draw a horizontal separator line."""
        c.setLineWidth(thickness)
        c.setStrokeColor(colors.HexColor(color))
        c.line(config.left_margin, y, config.right_margin, y)
        c.setStrokeColor(colors.black)

    def add_spacing(multiplier: float = 1.0):
        """Add standard spacing."""
        nonlocal y_position
        y_position -= config.line_height * multiplier

    def add_small_spacing(multiplier: float = 1.0):
        """Add small spacing."""
        nonlocal y_position
        y_position -= config.small_line_height * multiplier

    def draw_row(
        left_text: str,
        right_text: str,
        left_font: str = "Helvetica",
        left_size: float = None,
        right_font: str = "DejaVuSansMono",
        right_size: float = None,
        spacing: float = 0.9,
    ):
        """Draw a row with left and right aligned text."""
        left_size = left_size or config.font_item_name
        right_size = right_size or config.font_amount
        draw_left(left_text, y_position, left_font, left_size)
        draw_right(right_text, y_position, right_font, right_size)
        add_small_spacing(spacing)

    # ============================================================================
    # HEADER SECTION
    # ============================================================================

    # Logo if available
    if settings.RESTAURANT_LOGO_PATH and os.path.exists(settings.RESTAURANT_LOGO_PATH):
        try:
            logo = ImageReader(settings.RESTAURANT_LOGO_PATH)
            img_width, img_height = logo.getSize()
            max_logo_width = config.content_width * 0.8
            max_logo_height = 20 * mm if paper_size == "80mm" else 15 * mm
            aspect_ratio = img_width / img_height

            logo_width = min(max_logo_width, img_width)
            logo_height = logo_width / aspect_ratio
            if logo_height > max_logo_height:
                logo_height = max_logo_height
                logo_width = logo_height * aspect_ratio

            logo_x = (config.receipt_width - logo_width) / 2
            c.drawImage(
                settings.RESTAURANT_LOGO_PATH,
                logo_x,
                y_position - logo_height,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask="auto",
            )
            y_position -= logo_height + config.small_line_height
        except Exception:
            pass

    # Restaurant name (split into two lines: "Lily" and "Cafe by Mary's Kitchen")
    # Check if the name contains "Lily" to split it properly
    restaurant_name = settings.RESTAURANT_NAME
    add_small_spacing(0.5)
    if "Lily" in restaurant_name:
        # First line: "Lily"
        draw_centered("LILY", y_position, "Helvetica-Bold", config.font_cafe_name)
        add_small_spacing(1.4)
        # Second line: Rest of the name
        rest_of_name = restaurant_name.replace("Lily ", "").strip()
        draw_centered(rest_of_name, y_position, "Helvetica-Bold", config.font_cafe_sub_name)
        add_spacing(0.9)
    else:
        # Fallback: use wrapping for other names
        y_position = draw_centered(
            restaurant_name, y_position, "Helvetica-Bold", config.font_cafe_name, wrap=True
        )
        add_spacing(0.9)

    # Address
    draw_centered(
        settings.RESTAURANT_ADDRESS_LINE1, y_position, "Helvetica", config.font_address
    )
    add_small_spacing(0.9)
    draw_centered(
        settings.RESTAURANT_ADDRESS_LINE2, y_position, "Helvetica", config.font_address
    )
    add_small_spacing(1.0)

    # Contact info
    if paper_size == "58mm":
        # Stack vertically for narrow paper
        draw_centered(
            f"Tel: {settings.RESTAURANT_PHONE}", y_position, "Helvetica", config.font_contact
        )
        add_small_spacing(0.8)
        draw_centered(settings.RESTAURANT_EMAIL, y_position, "Helvetica", config.font_contact)
    else:
        # Side by side for wider paper
        draw_centered(
            f"Tel: {settings.RESTAURANT_PHONE} | {settings.RESTAURANT_EMAIL}",
            y_position,
            "Helvetica",
            config.font_contact,
        )
    add_small_spacing(1.3)

    # GSTIN
    draw_centered(
        f"GSTIN: {settings.RESTAURANT_GSTIN}", y_position, "Helvetica", config.font_gstin
    )
    add_spacing(1.2)

    # Thick separator after header
    draw_separator(y_position, thickness=1.0, color="#999999")
    add_spacing(1.3)

    # ============================================================================
    # ORDER INFORMATION SECTION
    # ============================================================================

    # Order number
    draw_left(
        f"Order No: {order.order_number}",
        y_position,
        "Helvetica-Bold",
        config.font_order_number,
    )
    add_spacing(1)

    # Date and time (convert from UTC to local timezone)
    local_time = convert_to_local_timezone(order.created_at)
    draw_left(
        f"Date: {local_time.strftime('%d-%m-%Y %I:%M %p')}",
        y_position,
        "Helvetica",
        config.font_order_details,
    )
    add_spacing(1)

    # Customer name
    if order.customer_name:
        draw_left(
            f"Customer: {order.customer_name}",
            y_position,
            "Helvetica",
            config.font_order_details,
        )
        add_spacing(2)
    add_spacing(1.0)

    # Table number (prominent and centered)
    draw_centered(
        f"Table {order.table_number}", y_position, "Helvetica-Bold", config.font_section_header + 8
    )
    add_spacing(1.2)

    

    # Separator
    draw_separator(y_position)
    add_spacing(1)

    # ============================================================================
    # ITEMS TABLE SECTION
    # ============================================================================

    # Table header
    draw_row(
        "Item",
        "Amount",
        left_font="Helvetica-Bold",
        right_font="Helvetica-Bold",
        left_size=config.font_section_header,
        right_size=config.font_section_header,
        spacing=0.6,
    )

    # Add thin separator under header
    draw_separator(y_position, thickness=0.25)
    add_small_spacing(1.5)

    # Items
    for item in order.order_items:
        # Item name with quantity
        if paper_size == "58mm":
            # Compact format for narrow paper
            item_text = f"{item.quantity}x {item.menu_item_name}"
            draw_left(item_text, y_position, "Helvetica", config.font_item_name)
            add_small_spacing(1)
            # Rate and amount on same line
            rate_text = f"@ {format_currency(item.unit_price)}"
            amount_text = format_currency(item.subtotal)
            draw_left(rate_text, y_position, "DejaVuSansMono", config.font_amount - 1)
            draw_right(amount_text, y_position, "DejaVuSansMono", config.font_amount)
            add_spacing(1.5)
        else:
            # Standard format for wider paper
            # Item quantity and name
            draw_left(
                f"{item.quantity}x {item.menu_item_name}",
                y_position,
                "Helvetica",
                config.font_item_name,
            )
            add_small_spacing(0.75)
            # Rate and amount on next line with indent
            rate_text = f"   @ {format_currency(item.unit_price)}"
            draw_left(rate_text, y_position, "DejaVuSansMono", config.font_amount - 1)
            draw_right(format_currency(item.subtotal), y_position, "DejaVuSansMono", config.font_amount)
            add_spacing(1.1)

    draw_separator(y_position)
    add_spacing(1)

    # ============================================================================
    # TOTALS SECTION
    # ============================================================================

    # Subtotal
    draw_row(
        "Subtotal:",
        format_currency(order.subtotal),
        left_size=config.font_subtotal,
        right_size=config.font_subtotal,
        spacing=1.5,
    )

    # GST breakdown (CGST + SGST)
    half_gst_rate = settings.GST_RATE / 2
    cgst_amount = order.gst_amount // 2
    sgst_amount = order.gst_amount - cgst_amount

    draw_row(
        f"CGST ({half_gst_rate}%):",
        format_currency(cgst_amount),
        left_size=config.font_subtotal,
        right_size=config.font_subtotal,
        spacing=1.5,
    )
    draw_row(
        f"SGST ({half_gst_rate}%):",
        format_currency(sgst_amount),
        left_size=config.font_subtotal,
        right_size=config.font_subtotal,
        spacing=0.5,  # More spacing after last tax line
    )

    # Separator before total
    draw_separator(y_position, thickness=0.5)
    add_spacing(2)  # More spacing after separator

    # TOTAL (prominent)
    draw_row(
        "TOTAL:",
        format_currency(order.total_amount),
        left_font="Helvetica-Bold",
        left_size=config.font_total,
        right_font="DejaVuSansMono",
        right_size=config.font_total,
        spacing=1.5,  # More spacing after total
    )

    # ============================================================================
    # PAYMENT SECTION (commented out for now)
    # ============================================================================

    # if order.payments:
    #     draw_separator(y_position, thickness=0.5)
    #     add_spacing(1)

    #     draw_left("Payments:", y_position, "Helvetica-Bold", config.font_section_header)
    #     add_small_spacing(0.8)
    #     # Add thin separator under Payments header
    #     draw_separator(y_position, thickness=0.25)
    #     add_small_spacing(1.2)

    #     for payment in order.payments:
    #         draw_row(
    #             f"{payment.payment_method.value.upper()}:",
    #             format_currency(payment.amount),
    #             left_size=config.font_payment,
    #             right_size=config.font_payment,
    #             spacing=1.2,
    #         )

    # ============================================================================
    # FOOTER SECTION
    # ============================================================================

    draw_separator(y_position, thickness=1.0, color="#999999")
    add_spacing(0.9)

    # Thank you message
    draw_centered("Thank you for visiting!", y_position, "Helvetica", config.font_footer)
    add_small_spacing(1)
    # draw_centered("Please visit again!", y_position, "Helvetica", config.font_footer)
    # add_small_spacing(0.75)
    draw_centered("#withlovefrommary", y_position, "Helvetica-Oblique", config.font_qr_label)
    add_spacing(1.0)

    # ============================================================================
    # QR CODE SECTION (commented right now)
    # ============================================================================

    # draw_centered(
    #     "Rate Your Experience", y_position, "Helvetica-Bold", config.font_section_header
    # )
    # add_spacing(0.9)

    # # QR code URLs from settings
    # google_review_url = settings.GOOGLE_REVIEW_URL
    # feedback_form_url = settings.FEEDBACK_FORM_URL

    # # Generate QR codes
    # qr_google = generate_qr_code(google_review_url, config.qr_size)
    # qr_feedback = generate_qr_code(feedback_form_url, config.qr_size)

    # qr_box = config.qr_size * 0.28  # Convert pixels to mm approximately

    # if config.qr_layout == "side-by-side":
    #     # 80mm paper - QR codes side by side
    #     qr_gap = 20 * mm  # Increased gap between QR codes
    #     qr_y = y_position - qr_box
    #     left_x = x_center - qr_box - (qr_gap / 2)
    #     right_x = x_center + (qr_gap / 2)

    #     # Draw QR codes
    #     c.drawImage(qr_google, left_x, qr_y, width=qr_box, height=qr_box, mask="auto")
    #     c.drawImage(qr_feedback, right_x, qr_y, width=qr_box, height=qr_box, mask="auto")

    #     # Labels below QR codes with proper spacing
    #     y_label = qr_y - 4 * mm  # More spacing between QR and label
    #     c.setFont("Helvetica", config.font_qr_label)

    #     # Left label (Google Review) - centered under left QR code
    #     left_label = "Google Review"
    #     label_width = c.stringWidth(left_label, "Helvetica", config.font_qr_label)
    #     c.drawString(left_x + (qr_box - label_width) / 2, y_label, left_label)

    #     # Right label (Feedback Form) - centered under right QR code
    #     right_label = "Feedback Form"
    #     label_width = c.stringWidth(right_label, "Helvetica", config.font_qr_label)
    #     c.drawString(right_x + (qr_box - label_width) / 2, y_label, right_label)

    #     y_position = y_label - 5 * mm

    # else:
    #     # 58mm paper - QR codes stacked vertically
    #     qr_x = (config.receipt_width - qr_box) / 2

    #     # First QR code (Google Review)
    #     qr_y = y_position - qr_box
    #     c.drawImage(qr_google, qr_x, qr_y, width=qr_box, height=qr_box, mask="auto")
    #     y_position = qr_y - 3 * mm
    #     draw_centered("Google Review", y_position, "Helvetica", config.font_qr_label)
    #     add_spacing(1.2)

    #     # Second QR code (Feedback Form)
    #     qr_y = y_position - qr_box
    #     c.drawImage(qr_feedback, qr_x, qr_y, width=qr_box, height=qr_box, mask="auto")
    #     y_position = qr_y - 3 * mm
    #     draw_centered("Feedback Form", y_position, "Helvetica", config.font_qr_label)
    #     add_spacing(0.5)

    # Save the PDF
    c.showPage()
    c.save()


def generate_order_chit_pdf(
    order: models.Order, output: BinaryIO, paper_size: PaperSize = "80mm"
) -> None:
    """
    Generate a simple order chit (kitchen ticket) PDF.

    Minimal design with:
    - Very large table number (customizable)
    - Order items with quantities
    - Total amount
    - Space for handwritten notes

    Args:
        order: Order model instance
        output: Binary output stream for PDF
        paper_size: Paper width - either "58mm" or "80mm" (default: "80mm")
    """
    config = ReceiptConfig(paper_size)
    c = canvas.Canvas(output, pagesize=(config.receipt_width, config.receipt_height))

    y_position = config.receipt_height - (config.top_margin_mm * mm)
    x_center = config.receipt_width / 2

    c.setFillColor(colors.black)

    # Helper functions
    def draw_centered(text: str, y: float, font: str = "Helvetica", size: float = 10):
        """Draw centered text."""
        c.setFont(font, size)
        width = c.stringWidth(text, font, size)
        c.drawString(x_center - width / 2, y, text)

    def draw_left(text: str, y: float, font: str = "Helvetica", size: float = 9):
        """Draw left-aligned text."""
        c.setFont(font, size)
        c.drawString(config.left_margin, y, text)

    def draw_separator(y: float, char: str = "="):
        """Draw a text-based separator line."""
        c.setFont("Courier", 10)
        width_chars = int(config.content_width / (2.5 * mm))  # Approximate char width
        separator_line = char * width_chars
        draw_centered(separator_line, y, "Courier", 10)

    def add_spacing(mm_spacing: float):
        """Add spacing in millimeters."""
        nonlocal y_position
        y_position -= mm_spacing * mm

    # ============================================================================
    # HEADER - VERY LARGE TABLE NUMBER
    # ============================================================================

    add_spacing(5)

    # Draw "TABLE" label in medium font
    table_label_size = 24 if paper_size == "80mm" else 18
    draw_centered("TABLE", y_position, "Helvetica-Bold", table_label_size)
    add_spacing(35)  # Large spacing to prevent overlap

    # Draw table number in GIANT font (much larger than before!)
    table_number_size = 120 if paper_size == "80mm" else 80  # MASSIVE - easily visible from across kitchen
    draw_centered(str(order.table_number), y_position, "Helvetica-Bold", table_number_size)
    add_spacing(45)  # Extra spacing after large number

    # Separator
    draw_separator(y_position)
    add_spacing(8)

    # ============================================================================
    # ORDER INFORMATION
    # ============================================================================

    # Order number and time
    local_time = convert_to_local_timezone(order.created_at)
    draw_centered(f"Order: {order.order_number}", y_position, "Helvetica", 11)
    add_spacing(5)
    draw_centered(f"Time: {local_time.strftime('%I:%M %p')}", y_position, "Helvetica", 11)
    add_spacing(5)

    # Customer name if present
    if order.customer_name:
        draw_centered(f"Name: {order.customer_name}", y_position, "Helvetica", 11)
        add_spacing(5)

    add_spacing(3)
    draw_separator(y_position)
    add_spacing(8)

    # ============================================================================
    # ITEMS SECTION - Large, readable text
    # ============================================================================

    for item in order.order_items:
        # Item with large quantity and name (NO PRICES - kitchen doesn't need them)
        item_text = f"{item.quantity}x {item.menu_item_name}"
        draw_left(item_text, y_position, "Helvetica-Bold", 16)
        add_spacing(10)

    add_spacing(3)
    draw_separator(y_position)
    add_spacing(8)

    # ============================================================================
    # NOTES SECTION - Space for handwritten notes
    # ============================================================================

    draw_separator(y_position, char="-")
    add_spacing(5)
    draw_left("NOTES:", y_position, "Helvetica-Bold", 12)
    add_spacing(10)

    # Add blank space for notes (multiple lines)
    for _ in range(6):
        add_spacing(8)

    draw_separator(y_position, char="-")
    add_spacing(15)

    # Save the PDF
    c.showPage()
    c.save()
