"""
Essae POS-60C Thermal Printer Detection Script
Detects printer connection via USB, Windows (Win32Raw), or Serial
Based on latest python-escpos library
"""

import sys
import platform

print("=" * 70)
print("ESSAE POS-60C THERMAL PRINTER DETECTION")
print("=" * 70)
print(f"Platform: {platform.system()}")
print()

detected = False

# ============================================================================
# METHOD 1: Windows Printer (Win32Raw) - Recommended for Windows
# ============================================================================
if platform.system() == "Windows":
    print("[1/3] Checking Windows printers (Win32Raw)...")
    try:
        import win32print
        from escpos.printer import Win32Raw

        # Get all printers
        printers = win32print.EnumPrinters(2)
        print(f"Found {len(printers)} Windows printer(s):")

        for i, printer_info in enumerate(printers):
            printer_name = printer_info[2]
            print(f"  {i+1}. {printer_name}")

            # Check if this looks like our thermal printer
            if any(keyword in printer_name.upper() for keyword in ["POS", "ESSAE", "60C", "THERMAL", "RECEIPT"]):
                print(f"\n✅ Found potential thermal printer: '{printer_name}'")

                # Try to print test
                try:
                    print("   Testing connection...")
                    p = Win32Raw(printer_name)
                    p.text("=" * 32 + "\n")
                    p.text("  LILY CAFE POS SYSTEM\n")
                    p.text("  Printer Test\n")
                    p.text("=" * 32 + "\n")
                    p.text("\n")
                    p.text("Printer connected successfully!\n")
                    p.text(f"Printer: {printer_name}\n")
                    p.text("\n")
                    p.text(f"Detection method: Win32Raw\n")
                    p.text("\n")
                    p.cut()
                    p.close()

                    print("   ✅ TEST PRINT SUCCESSFUL!")
                    print()
                    print("=" * 70)
                    print("CONFIGURATION FOR .env FILE:")
                    print("=" * 70)
                    print(f'PRINTER_TYPE=win32')
                    print(f'PRINTER_NAME={printer_name}')
                    print("=" * 70)
                    detected = True
                    break

                except Exception as e:
                    print(f"   ❌ Failed to print: {e}")
                    continue

        if not detected and printers:
            print("\n⚠️  No thermal printer auto-detected.")
            print("   Manual selection:")
            print("   Which printer is your Essae POS-60C? Enter number (1-{}): ".format(len(printers)))

    except ImportError as e:
        print(f"❌ Windows printer support not available: {e}")
        print("   Install with: uv pip install pywin32")
    except Exception as e:
        print(f"❌ Error checking Windows printers: {e}")

    print()

# ============================================================================
# METHOD 2: USB Printer (Direct USB)
# ============================================================================
print("[2/3] Checking USB printers...")
try:
    from escpos.printer import Usb
    import usb.core

    # List all USB devices first
    print("Scanning USB devices...")
    devices = list(usb.core.find(find_all=True))

    if devices:
        print(f"Found {len(devices)} USB device(s):")
        for device in devices:
            print(f"  Vendor: {hex(device.idVendor)}, Product: {hex(device.idProduct)}")
    else:
        print("No USB devices found")

    # Common Essae and generic thermal printer vendor IDs
    # Essae might use generic USB-to-serial chips
    vendor_ids = [
        0x0dd4,  # Common thermal printer
        0x04b8,  # Epson (sometimes Essae uses Epson chips)
        0x20d1,  # Generic thermal
        0x0519,  # Epson
        0x067b,  # Prolific USB-to-Serial
        0x1a86,  # CH340 USB-to-Serial (common in Chinese printers)
    ]

    for vid in vendor_ids:
        try:
            # Try to find device with this vendor ID
            device = usb.core.find(idVendor=vid)
            if device:
                print(f"\n✅ Found USB device: Vendor={hex(vid)}, Product={hex(device.idProduct)}")

                # Try to connect and print
                try:
                    print("   Testing connection...")
                    # Try with default endpoints
                    p = Usb(vid, device.idProduct, 0, profile="POS-5890")

                    p.text("=" * 32 + "\n")
                    p.text("  LILY CAFE POS SYSTEM\n")
                    p.text("  USB Printer Test\n")
                    p.text("=" * 32 + "\n")
                    p.text("\n")
                    p.text("USB connection successful!\n")
                    p.text(f"Vendor ID: {hex(vid)}\n")
                    p.text(f"Product ID: {hex(device.idProduct)}\n")
                    p.text("\n")
                    p.cut()
                    p.close()

                    print("   ✅ TEST PRINT SUCCESSFUL!")
                    print()
                    print("=" * 70)
                    print("CONFIGURATION FOR .env FILE:")
                    print("=" * 70)
                    print(f'PRINTER_TYPE=usb')
                    print(f'PRINTER_VENDOR_ID={hex(vid)}')
                    print(f'PRINTER_PRODUCT_ID={hex(device.idProduct)}')
                    print("=" * 70)
                    detected = True
                    break

                except Exception as e:
                    print(f"   ❌ Failed to print: {e}")
                    continue

        except Exception as e:
            continue

    if not detected:
        print("❌ No USB thermal printer detected or accessible")

except ImportError as e:
    print(f"❌ USB support not available: {e}")
    print("   Install with: uv pip install pyusb")
except Exception as e:
    print(f"❌ Error checking USB printers: {e}")

print()

# ============================================================================
# METHOD 3: Serial Port (COM port on Windows)
# ============================================================================
print("[3/3] Checking Serial ports...")
try:
    from escpos.printer import Serial
    import serial.tools.list_ports

    # List available COM ports
    ports = list(serial.tools.list_ports.comports())

    if ports:
        print(f"Found {len(ports)} serial port(s):")
        for port in ports:
            print(f"  {port.device} - {port.description}")

            # Try common thermal printer port on Windows
            if "COM" in port.device:
                try:
                    print(f"\n   Testing {port.device}...")

                    # Try common baud rates for thermal printers
                    for baudrate in [9600, 19200, 38400, 115200]:
                        try:
                            p = Serial(
                                devfile=port.device,
                                baudrate=baudrate,
                                bytesize=8,
                                parity='N',
                                stopbits=1,
                                timeout=1.0,
                                profile="POS-5890"
                            )

                            p.text("=" * 32 + "\n")
                            p.text("  LILY CAFE POS SYSTEM\n")
                            p.text("  Serial Test\n")
                            p.text("=" * 32 + "\n")
                            p.text("\n")
                            p.text(f"Port: {port.device}\n")
                            p.text(f"Baudrate: {baudrate}\n")
                            p.text("\n")
                            p.cut()
                            p.close()

                            print(f"   ✅ TEST PRINT SUCCESSFUL at {baudrate} baud!")
                            print()
                            print("=" * 70)
                            print("CONFIGURATION FOR .env FILE:")
                            print("=" * 70)
                            print(f'PRINTER_TYPE=serial')
                            print(f'PRINTER_PORT={port.device}')
                            print(f'PRINTER_BAUDRATE={baudrate}')
                            print("=" * 70)
                            detected = True
                            break

                        except Exception as e:
                            continue

                    if detected:
                        break

                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                    continue
    else:
        print("No serial ports found")

except ImportError as e:
    print(f"❌ Serial support not available: {e}")
    print("   Install with: uv pip install pyserial")
except Exception as e:
    print(f"❌ Error checking serial ports: {e}")

print()
print("=" * 70)

if detected:
    print("✅ PRINTER DETECTED AND TESTED SUCCESSFULLY!")
    print()
    print("Next steps:")
    print("1. Copy the configuration above to your .env file")
    print("2. Restart the backend server")
    print("3. Use the print receipt button in the POS system")
else:
    print("❌ NO PRINTER DETECTED")
    print()
    print("Troubleshooting:")
    print("1. Make sure printer is turned ON")
    print("2. Check USB/Serial cable is connected")
    print("3. Install printer drivers from Essae website")
    print("4. On Windows: Add printer in 'Printers & Scanners'")
    print("5. Install required libraries:")
    print("   - Windows: uv pip install pywin32")
    print("   - USB: uv pip install pyusb")
    print("   - Serial: uv pip install pyserial")

print("=" * 70)
