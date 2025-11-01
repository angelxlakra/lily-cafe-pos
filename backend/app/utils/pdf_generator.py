"""
PDF receipt generator for Lily Cafe POS System.
Generates thermal printer-compatible receipts (80mm width).
"""

import os
from pathlib import Path

from reportlab.lib.pagesizes import mm
from reportlab.lib.units import mm as mm_unit
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from app.core.config import settings
from app.models import models
from datetime import datetime
from typing import BinaryIO

# Get the backend directory path (parent of app directory)
BACKEND_DIR = Path(__file__).parent.parent.parent
FONT_PATH = BACKEND_DIR / "public" / "fonts" / "dejavu" / "DejaVuSansMono.ttf"

# Register DejaVuSansMono font for rupee symbol rendering
if FONT_PATH.exists():
    pdfmetrics.registerFont(TTFont("DejaVuSansMono", str(FONT_PATH)))
else:
    raise FileNotFoundError(f"Font file not found at {FONT_PATH}")

# 80mm thermal printer width
# Note: Actual printable area is ~72mm due to printer margins
RECEIPT_WIDTH = 72 * mm_unit  # Reduced from 80mm to match printable area
RECEIPT_HEIGHT = 297 * mm_unit  # A4 height, will be cut as needed


def format_currency(amount_in_paise: int) -> str:
    """
    Format currency in paise to rupees.

    Args:
        amount_in_paise: Amount in paise (e.g., 8000 for �80)

    Returns:
        Formatted string (e.g., "�80.00")
    """
    rupees = amount_in_paise / 100
    return f"\u20B9{rupees:.2f}"


def generate_receipt(order: models.Order, output: BinaryIO):
    """
    Generate a PDF receipt for an order.

    Args:
        order: Order object with all related data
        output: Binary file-like object to write PDF to
    """
    c = canvas.Canvas(output, pagesize=(RECEIPT_WIDTH, RECEIPT_HEIGHT))

    # Starting position
    y_position = RECEIPT_HEIGHT - 0 * mm_unit  # Zero top margin (content starts at very top)
    line_height = 5 * mm_unit
    x_center = RECEIPT_WIDTH / 2
    x_left = 3 * mm_unit  # Reduced margin for narrower printable area
    x_right = RECEIPT_WIDTH - 3 * mm_unit

    # Helper function to draw centered text
    def draw_centered(text, y, font="Helvetica", size=10):
        c.setFont(font, size)
        text_width = c.stringWidth(text, font, size)
        c.drawString(x_center - text_width / 2, y, text)

    # Helper function to draw left-aligned text
    def draw_left(text, y, font="Helvetica", size=9):
        c.setFont(font, size)
        c.drawString(x_left, y, text)

    # Helper function to draw right-aligned text
    def draw_right(text, y, font="Helvetica", size=9):
        c.setFont(font, size)
        text_width = c.stringWidth(text, font, size)
        c.drawString(x_right - text_width, y, text)

    # Header - Logo (if available)
    if settings.RESTAURANT_LOGO_PATH and os.path.exists(settings.RESTAURANT_LOGO_PATH):
        try:
            logo = ImageReader(settings.RESTAURANT_LOGO_PATH)
            # Get image dimensions
            img_width, img_height = logo.getSize()
            # Calculate aspect ratio and scale to fit receipt width
            max_logo_width = RECEIPT_WIDTH - (6 * mm_unit)  # Leave 3mm margins on each side
            max_logo_height = 25 * mm_unit  # Max 25mm height (increased for better visibility)

            # Scale image maintaining aspect ratio
            aspect_ratio = img_width / img_height
            if img_width > max_logo_width:
                logo_width = max_logo_width
                logo_height = logo_width / aspect_ratio
            else:
                logo_width = img_width
                logo_height = img_height

            if logo_height > max_logo_height:
                logo_height = max_logo_height
                logo_width = logo_height * aspect_ratio

            # Draw logo centered
            logo_x = (RECEIPT_WIDTH - logo_width) / 2
            c.drawImage(settings.RESTAURANT_LOGO_PATH, logo_x, y_position - logo_height,
                       width=logo_width, height=logo_height, preserveAspectRatio=True)
            y_position -= (logo_height + 3 * mm_unit)  # Add spacing after logo
        except Exception as e:
            # If logo fails to load, just continue without it
            pass

    # Header - Restaurant Name
    draw_centered(settings.RESTAURANT_NAME, y_position, "Helvetica-Bold", 14)
    y_position -= line_height

    # Restaurant Address
    draw_centered(settings.RESTAURANT_ADDRESS_LINE1, y_position, "Helvetica", 8)
    y_position -= line_height * 0.8
    draw_centered(settings.RESTAURANT_ADDRESS_LINE2, y_position, "Helvetica", 8)
    y_position -= line_height * 0.8
    draw_centered(
        f"Tel: {settings.RESTAURANT_PHONE} | {settings.RESTAURANT_EMAIL}",
        y_position,
        "Helvetica",
        8,
    )
    y_position -= line_height * 0.8
    draw_centered(f"GSTIN: {settings.RESTAURANT_GSTIN}", y_position, "Helvetica", 8)
    y_position -= line_height * 1.2

    # Separator line
    c.line(x_left, y_position, x_right, y_position)
    y_position -= line_height

    # Order Details
    draw_left(f"Order No: {order.order_number}", y_position, "Helvetica-Bold", 10)
    y_position -= line_height * 0.8
    draw_left(f"Table: {order.table_number}", y_position)
    y_position -= line_height * 0.8
    if order.customer_name:
        draw_left(f"Customer: {order.customer_name}", y_position)
        y_position -= line_height * 0.8
    draw_left(
        f"Date: {order.created_at.strftime('%d-%m-%Y %I:%M %p')}", y_position
    )
    y_position -= line_height * 1.2

    # Separator line
    c.line(x_left, y_position, x_right, y_position)
    y_position -= line_height

    # Items Header
    draw_left("Item", y_position, "Helvetica-Bold", 9)
    draw_right("Amount", y_position, "Helvetica-Bold", 9)
    y_position -= line_height * 0.8

    # Order Items
    for item in order.order_items:
        # Item name
        item_text = f"{item.quantity}x {item.menu_item_name}"
        draw_left(item_text, y_position)
        y_position -= line_height * 0.8

        # Item price (using DejaVuSansMono for rupee symbol)
        price_text = format_currency(item.unit_price)
        amount_text = format_currency(item.subtotal)
        draw_left(f"    @ {price_text}", y_position, "DejaVuSansMono", 8)
        draw_right(amount_text, y_position, "DejaVuSansMono", 9)
        y_position -= line_height * 1.2

    # Separator line
    c.line(x_left, y_position, x_right, y_position)
    y_position -= line_height

    # Subtotal
    draw_left("Subtotal:", y_position)
    draw_right(format_currency(order.subtotal), y_position, "DejaVuSansMono", 9)
    y_position -= line_height * 0.8

    # GST split into SGST and CGST (50/50)
    half_gst_rate = settings.GST_RATE / 2
    sgst_amount = order.gst_amount // 2
    cgst_amount = order.gst_amount - sgst_amount  # Ensure exact sum

    # SGST
    draw_left(f"SGST ({half_gst_rate}%):", y_position)
    draw_right(format_currency(sgst_amount), y_position, "DejaVuSansMono", 9)
    y_position -= line_height * 0.8

    # CGST
    draw_left(f"CGST ({half_gst_rate}%):", y_position)
    draw_right(format_currency(cgst_amount), y_position, "DejaVuSansMono", 9)
    y_position -= line_height * 1.2

    # Total (using DejaVuSansMono for rupee symbol)
    draw_left("TOTAL:", y_position, "Helvetica-Bold", 11)
    draw_right(format_currency(order.total_amount), y_position, "DejaVuSansMono", 11)
    y_position -= line_height * 1.5

    # Separator line
    c.line(x_left, y_position, x_right, y_position)
    y_position -= line_height

    # Payments
    if order.payments:
        draw_left("Payments:", y_position, "Helvetica-Bold", 9)
        y_position -= line_height * 0.8

        for payment in order.payments:
            method_name = payment.payment_method.value.upper()
            draw_left(f"{method_name}:", y_position)
            draw_right(format_currency(payment.amount), y_position, "DejaVuSansMono", 9)
            y_position -= line_height * 0.8

        y_position -= line_height * 0.5

    # Footer
    y_position -= line_height
    draw_centered("Thank you for visiting!", y_position, "Helvetica-Bold", 10)
    y_position -= line_height * 0.8
    draw_centered("Please visit again!", y_position, "Helvetica", 8)

    # Save PDF
    c.save()
