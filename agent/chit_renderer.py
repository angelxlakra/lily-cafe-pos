# agent/chit_renderer.py
"""
Renders and prints an order chit from the JSON payload returned by /print-jobs/next.
Uses python-escpos for direct ESC/POS thermal printing.
"""

import logging

logger = logging.getLogger(__name__)


def get_printer(printer_type: str, **kwargs):
    t = printer_type.lower()
    if t == "usb":
        from escpos.printer import Usb
        vendor_id = int(kwargs["vendor_id"], 16)
        product_id = int(kwargs["product_id"], 16)
        return Usb(vendor_id, product_id)
    elif t == "serial":
        from escpos.printer import Serial
        return Serial(kwargs["port"], baudrate=int(kwargs.get("baudrate", 9600)))
    elif t == "network":
        from escpos.printer import Network
        return Network(kwargs["host"], port=int(kwargs.get("port_num", 9100)))
    elif t == "win32":
        from escpos.printer import Win32Raw
        return Win32Raw(kwargs["name"])
    raise ValueError(f"Unknown printer type: {printer_type}")


def print_chit(payload: dict, printer_cfg: dict, paper_size: str = "80mm") -> bool:
    """
    Print one chit from a payload dict.

    payload keys: order_number, table_number, customer_name, created_at, station, items
    printer_cfg keys: type, and type-specific keys (vendor_id, product_id, port, host, name)
    """
    printer = None
    try:
        printer = get_printer(printer_cfg["type"], **printer_cfg)
        is_58mm = paper_size == "58mm"
        width = 32 if is_58mm else 42

        station = payload.get("station", "kitchen").upper()

        # Header: large table number
        printer.set(align="center", bold=True, width=2, height=2)
        printer.text(f"TABLE {payload['table_number']}\n")
        printer.set(bold=False, width=1, height=1)
        printer.text("\n")

        # Order info
        printer.text(f"Order: {payload['order_number']}\n")
        # created_at is ISO string — take HH:MM portion (works for both naive and tz-aware)
        time_str = payload.get("created_at", "")[:16].replace("T", " ")
        printer.text(f"Time:  {time_str}\n")
        if payload.get("customer_name"):
            printer.text(f"Name:  {payload['customer_name']}\n")
        printer.text("\n")

        # Items — large text, no prices
        for item in payload["items"]:
            if item.get("is_beverage"):
                printer.set(align="left", bold=True, underline=True, width=2, height=2)
            else:
                printer.set(align="left", bold=True, underline=False, width=2, height=2)
            printer.text(f"{item['quantity']}x {item['name']}\n\n")

        printer.set(bold=False, underline=False, width=1, height=1)

        # Notes section
        printer.text("=" * width + "\n")
        printer.text("NOTES:\n\n\n\n\n")
        printer.text("-" * width + "\n\n")

        # Station banner at bottom — most visible when chit hangs on the rail
        printer.set(align="center")
        printer.text("=" * width + "\n")
        printer.set(bold=True, width=2, height=2)
        printer.text(f"{station}\n")
        printer.set(bold=False, width=1, height=1)
        printer.text("=" * width + "\n")

        try:
            printer.cut()
        except Exception:
            printer.text("\n\n\n")

        logger.info(f"Printed {station} chit for table {payload['table_number']}")
        return True

    except Exception as e:
        logger.error(f"Print failed: {e}")
        return False

    finally:
        if printer:
            try:
                printer.close()
            except Exception:
                pass
