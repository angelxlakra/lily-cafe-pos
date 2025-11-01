#!/usr/bin/env python3
"""
Printer configuration utility for Lily Cafe POS System.
Helps detect USB thermal printers and find their vendor/product IDs.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import usb.core
    import usb.util
except ImportError:
    print("❌ PyUSB not installed.")
    print("Install it with: pip install pyusb")
    print("Or: uv pip install pyusb")
    sys.exit(1)


def find_usb_printers():
    """Find all USB devices that might be printers."""
    print("🔍 Scanning for USB devices...\n")

    # Find all USB devices
    devices = usb.core.find(find_all=True)

    printers = []
    all_devices = []

    for device in devices:
        try:
            vendor_id = device.idVendor
            product_id = device.idProduct

            # Try to get manufacturer and product names
            try:
                manufacturer = usb.util.get_string(device, device.iManufacturer) or "Unknown"
                product = usb.util.get_string(device, device.iProduct) or "Unknown"
            except (ValueError, usb.core.USBError):
                manufacturer = "Unknown"
                product = "Unknown"

            device_info = {
                "vendor_id": vendor_id,
                "product_id": product_id,
                "manufacturer": manufacturer,
                "product": product,
                "device_class": device.bDeviceClass,
            }

            all_devices.append(device_info)

            # USB printer class is 0x07
            # But many thermal printers use vendor-specific class (0xFF)
            if (
                device.bDeviceClass == 0x07  # Printer class
                or "print" in product.lower()
                or "pos" in product.lower()
                or "thermal" in product.lower()
            ):
                printers.append(device_info)

        except (ValueError, usb.core.USBError) as e:
            # Skip devices we can't read
            continue

    return printers, all_devices


def print_device_info(device, is_likely_printer=False):
    """Print formatted device information."""
    marker = "🖨️ " if is_likely_printer else "📱 "
    print(f"{marker} {device['manufacturer']} - {device['product']}")
    print(f"   Vendor ID:  0x{device['vendor_id']:04x} ({device['vendor_id']})")
    print(f"   Product ID: 0x{device['product_id']:04x} ({device['product_id']})")
    print(f"   Class: 0x{device['device_class']:02x}")
    print()


def main():
    """Main configuration script."""
    print("=" * 60)
    print("  Lily Cafe POS - Thermal Printer Configuration")
    print("=" * 60)
    print()

    printers, all_devices = find_usb_printers()

    if printers:
        print(f"✅ Found {len(printers)} potential printer(s):\n")
        for printer in printers:
            print_device_info(printer, is_likely_printer=True)

        print("\n" + "=" * 60)
        print("📋 Configuration Instructions:")
        print("=" * 60)
        print()
        print("To use the thermal printer, you have two options:\n")

        print("1. Test from Python:")
        print("   Use the print-thermal API endpoint with these parameters:")
        if printers:
            p = printers[0]
            print(f"   - vendor_id: 0x{p['vendor_id']:04x}")
            print(f"   - product_id: 0x{p['product_id']:04x}")
            print()
            print("   Example API call:")
            print(
                f"   POST /api/v1/orders/{{order_id}}/print-thermal?vendor_id=0x{p['vendor_id']:04x}&product_id=0x{p['product_id']:04x}"
            )
            print()

        print("\n2. Add to your .env file (for permanent configuration):")
        if printers:
            p = printers[0]
            print(f"   PRINTER_VENDOR_ID=0x{p['vendor_id']:04x}")
            print(f"   PRINTER_PRODUCT_ID=0x{p['product_id']:04x}")
            print()

    else:
        print("⚠️  No USB printers detected.\n")
        print("Possible reasons:")
        print("  - Printer is not connected via USB")
        print("  - Printer is powered off")
        print("  - USB permissions issue (try running with sudo)")
        print("  - Printer uses network connection instead\n")

        if all_devices:
            print(f"However, found {len(all_devices)} other USB device(s):")
            print("(Your printer might be in this list)\n")
            for device in all_devices[:10]:  # Show max 10
                print_device_info(device)
            if len(all_devices) > 10:
                print(f"... and {len(all_devices) - 10} more devices")

    print("\n" + "=" * 60)
    print("💡 Troubleshooting:")
    print("=" * 60)
    print()
    print("If you don't see your printer:")
    print("  1. Make sure it's connected and powered on")
    print("  2. On Linux, you may need: sudo usermod -a -G lp $USER")
    print("  3. Try running this script with sudo: sudo python3 configure_printer.py")
    print("  4. Check if the printer works with other software")
    print()
    print("Common USB IDs for thermal printers:")
    print("  - Seiben/XPrinter: vendor_id=0x0416, product_id=0x5011")
    print("  - Epson TM series: vendor_id=0x04b8")
    print("  - Generic POS-80:  vendor_id=0x0416, product_id=0x5011")
    print()
    print("You can also try these default values if auto-detection fails.")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⛔ Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
