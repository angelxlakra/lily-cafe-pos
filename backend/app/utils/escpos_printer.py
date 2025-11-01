"""
ESC/POS thermal printer utilities for Lily Cafe POS System.
Direct printing to thermal printers with minimal margins.
"""

import os
from pathlib import Path
from typing import Optional
from escpos.printer import Usb, Network, File, Dummy
from escpos.exceptions import USBNotFoundError, Error as EscposError
from app.core.config import settings
from app.models import models
from PIL import Image


class ThermalPrinter:
    """Wrapper for ESC/POS thermal printer operations."""

    def __init__(self, printer_type: str = "usb", **kwargs):
        """
        Initialize thermal printer connection.

        Args:
            printer_type: Type of printer connection ("usb", "network", "file", "dummy")
            **kwargs: Additional arguments for specific printer types
        """
        self.printer = None
        self.printer_type = printer_type

        try:
            if printer_type == "usb":
                # Default Seiben/XPrinter USB IDs (you may need to adjust)
                vendor_id = kwargs.get("vendor_id", 0x0416)  # Common for thermal printers
                product_id = kwargs.get("product_id", 0x5011)  # Common for thermal printers
                self.printer = Usb(vendor_id, product_id)
            elif printer_type == "network":
                host = kwargs.get("host", "192.168.1.100")
                port = kwargs.get("port", 9100)
                self.printer = Network(host, port)
            elif printer_type == "file":
                # For testing - outputs to file instead of printer
                output_path = kwargs.get("output_path", "/tmp/receipt.bin")
                self.printer = File(output_path)
            else:
                # Dummy printer for testing
                self.printer = Dummy()
        except USBNotFoundError:
            raise ConnectionError(
                "USB thermal printer not found. Please check connection and vendor/product IDs."
            )
        except EscposError as e:
            raise ConnectionError(f"Failed to connect to printer: {str(e)}")

    def format_currency(self, amount_in_paise: int) -> str:
        """Format currency in paise to rupees."""
        rupees = amount_in_paise / 100
        return f"Rs.{rupees:.2f}"

    def print_receipt(self, order: models.Order) -> None:
        """
        Print receipt directly to thermal printer.

        Args:
            order: Order object with all related data
        """
        if not self.printer:
            raise RuntimeError("Printer not initialized")

        try:
            # Initialize printer
            self.printer.hw("INIT")

            # Print logo if available
            if settings.RESTAURANT_LOGO_PATH and os.path.exists(
                settings.RESTAURANT_LOGO_PATH
            ):
                try:
                    # Load and print logo
                    logo = Image.open(settings.RESTAURANT_LOGO_PATH)
                    # Resize to fit thermal printer (max 512px width for 80mm)
                    max_width = 512
                    if logo.width > max_width:
                        ratio = max_width / logo.width
                        new_size = (max_width, int(logo.height * ratio))
                        logo = logo.resize(new_size, Image.Resampling.LANCZOS)

                    self.printer.image(logo, center=True)
                    self.printer.ln(1)
                except Exception as e:
                    # If logo fails, continue without it
                    pass

            # Header - Restaurant Name
            self.printer.set(align="center", text_type="B", width=2, height=2)
            self.printer.text(f"{settings.RESTAURANT_NAME}\n")
            self.printer.set(align="center", text_type="normal")
            self.printer.ln(1)

            # Address and contact
            self.printer.text(f"{settings.RESTAURANT_ADDRESS_LINE1}\n")
            self.printer.text(f"{settings.RESTAURANT_ADDRESS_LINE2}\n")
            self.printer.text(
                f"Tel: {settings.RESTAURANT_PHONE} | {settings.RESTAURANT_EMAIL}\n"
            )
            self.printer.text(f"GSTIN: {settings.RESTAURANT_GSTIN}\n")
            self.printer.ln(1)

            # Separator
            self.printer.text("=" * 48 + "\n")

            # Order details
            self.printer.set(align="left", text_type="B")
            self.printer.text(f"Order No: {order.order_number}\n")
            self.printer.set(text_type="normal")
            self.printer.text(f"Table: {order.table_number}\n")
            if order.customer_name:
                self.printer.text(f"Customer: {order.customer_name}\n")
            self.printer.text(
                f"Date: {order.created_at.strftime('%d-%m-%Y %I:%M %p')}\n"
            )
            self.printer.ln(1)

            # Separator
            self.printer.text("=" * 48 + "\n")

            # Items header
            self.printer.set(text_type="B")
            self.printer.text(f"{'Item':<30}{'Amount':>18}\n")
            self.printer.set(text_type="normal")
            self.printer.text("-" * 48 + "\n")

            # Order items
            for item in order.order_items:
                # Item name and quantity
                item_text = f"{item.quantity}x {item.menu_item_name}"
                self.printer.text(f"{item_text}\n")

                # Price and subtotal
                price_text = self.format_currency(item.unit_price)
                amount_text = self.format_currency(item.subtotal)
                self.printer.text(f"  @ {price_text:<25}{amount_text:>20}\n")

            # Separator
            self.printer.text("=" * 48 + "\n")

            # Totals
            subtotal_text = self.format_currency(order.subtotal)
            self.printer.text(f"{'Subtotal:':<30}{subtotal_text:>18}\n")

            gst_text = self.format_currency(order.gst_amount)
            self.printer.text(
                f"{'GST (' + str(settings.GST_RATE) + '%):':<30}{gst_text:>18}\n"
            )

            # Total - Bold and larger
            self.printer.set(text_type="B", width=2, height=2)
            total_text = self.format_currency(order.total_amount)
            self.printer.text(f"TOTAL: {total_text}\n")
            self.printer.set(text_type="normal", width=1, height=1)
            self.printer.ln(1)

            # Separator
            self.printer.text("=" * 48 + "\n")

            # Payments
            if order.payments:
                self.printer.set(text_type="B")
                self.printer.text("Payments:\n")
                self.printer.set(text_type="normal")

                for payment in order.payments:
                    method_name = payment.payment_method.value.upper()
                    payment_amount = self.format_currency(payment.amount)
                    self.printer.text(f"{method_name + ':':<30}{payment_amount:>18}\n")

                self.printer.ln(1)

            # Footer
            self.printer.ln(1)
            self.printer.set(align="center", text_type="B")
            self.printer.text("Thank you for visiting!\n")
            self.printer.set(text_type="normal")
            self.printer.text("Please visit again!\n")
            self.printer.ln(2)

            # Cut paper
            self.printer.cut()

        except EscposError as e:
            raise RuntimeError(f"Print failed: {str(e)}")

    def configure_printer_margins(self, top_margin: int = 0) -> None:
        """
        Configure printer margins (experimental).

        Args:
            top_margin: Top margin in dots (0 for minimal margin)
        """
        if not self.printer:
            raise RuntimeError("Printer not initialized")

        try:
            # Set top margin (if supported by printer)
            # ESC 3 n - Set line spacing to n/180 inch
            self.printer._raw(b"\x1b\x33" + bytes([top_margin]))
        except Exception as e:
            # Some printers may not support this command
            pass

    def close(self):
        """Close printer connection."""
        if self.printer:
            self.printer.close()


def get_printer(printer_type: str = "usb", **kwargs) -> ThermalPrinter:
    """
    Factory function to get a thermal printer instance.

    Args:
        printer_type: Type of printer ("usb", "network", "file", "dummy")
        **kwargs: Additional printer-specific arguments

    Returns:
        ThermalPrinter instance
    """
    return ThermalPrinter(printer_type=printer_type, **kwargs)
