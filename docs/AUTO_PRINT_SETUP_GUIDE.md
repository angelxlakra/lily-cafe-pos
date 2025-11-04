# Automatic Thermal Printer Setup Guide

**Version:** 1.0
**Last Updated:** 2025-11-04

This guide explains how to set up automatic receipt printing to your thermal printer.

---

## Overview

The POS system now supports **automatic printing** directly to thermal printers using ESC/POS commands. When enabled, receipts can automatically print to your configured thermal printer without manual intervention.

### Features

- ✅ **Direct ESC/POS printing** - Sends commands directly to printer
- ✅ **Multiple connection types** - Supports Windows printer, USB, and Serial
- ✅ **Auto-detection** - Script helps find and configure your printer
- ✅ **Backward compatible** - PDF generation still works (manual print)
- ✅ **Graceful fallback** - If printing fails, PDF is still returned

---

## Step 1: Detect Your Printer

First, connect your thermal printer and run the detection script:

```bash
cd backend
uv run python detect_printer.py
```

### What the Script Does

The script will:
1. Search for Windows printers (Win32Raw)
2. Search for USB printers (direct USB)
3. Search for Serial port printers
4. Test print to detected printer
5. Show you the configuration values to use

### Example Output

```
======================================================================
ESSAE POS-60C THERMAL PRINTER DETECTION
======================================================================

[1/3] Checking Windows printers (Win32Raw)...
Found 2 Windows printer(s):
  1. Microsoft Print to PDF
  2. Essae POS-60C

✅ Found potential thermal printer: 'Essae POS-60C'

Testing printer...
🖨️  Printing test receipt...
✅ TEST PRINT SUCCESSFUL!

======================================================================
CONFIGURATION VALUES FOR .env FILE:
======================================================================
PRINTER_ENABLED=true
PRINTER_TYPE=win32
PRINTER_NAME=Essae POS-60C
======================================================================
```

---

## Step 2: Configure Your .env File

Copy the suggested values from the detection script to your `.env` file.

### Option A: Windows Printer (Recommended for Windows)

```bash
# Thermal Printer Configuration
PRINTER_ENABLED=true
PRINTER_TYPE=win32
PRINTER_NAME=Essae POS-60C
```

### Option B: USB Printer (Direct USB)

```bash
# Thermal Printer Configuration
PRINTER_ENABLED=true
PRINTER_TYPE=usb
PRINTER_VENDOR_ID=0x0dd4
PRINTER_PRODUCT_ID=0x1234
```

### Option C: Serial Port Printer

```bash
# Thermal Printer Configuration
PRINTER_ENABLED=true
PRINTER_TYPE=serial
PRINTER_PORT=COM3
PRINTER_BAUDRATE=9600
```

---

## Step 3: Restart Backend Server

After updating `.env`, restart the backend:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

The server will load the new printer configuration.

---

## Step 4: Test Automatic Printing

### Method 1: Using API Directly

Test with a paid order (you need an order_id of a paid order):

```bash
# Without auto-print (PDF only - manual print)
curl http://localhost:8000/api/v1/orders/1/receipt > receipt.pdf

# With auto-print (prints automatically + returns PDF)
curl "http://localhost:8000/api/v1/orders/1/receipt?auto_print=true" > receipt.pdf
```

### Method 2: Using Browser

1. Open browser: `http://localhost:8000/docs`
2. Navigate to `GET /api/v1/orders/{order_id}/receipt`
3. Click "Try it out"
4. Enter an order_id (must be a paid order)
5. Set `auto_print` to `true`
6. Click "Execute"
7. Check if receipt printed automatically
8. PDF will also download in browser

### Method 3: Test Script

Create a test script `test_print.py`:

```python
import requests

# Test automatic printing
order_id = 1  # Replace with actual paid order ID
response = requests.get(
    f"http://localhost:8000/api/v1/orders/{order_id}/receipt",
    params={"auto_print": True}
)

if response.status_code == 200:
    print("✓ Receipt generated successfully")
    print("Check your printer for output!")

    # Save PDF too
    with open("receipt.pdf", "wb") as f:
        f.write(response.content)
    print("✓ PDF saved to receipt.pdf")
else:
    print(f"✗ Error: {response.status_code}")
    print(response.json())
```

Run: `uv run python test_print.py`

---

## Step 5: Frontend Integration (Optional)

To add auto-print button to your frontend:

```typescript
// In your React component
const printReceipt = async (orderId: number, autoPrint: boolean = false) => {
  try {
    const url = `/api/v1/orders/${orderId}/receipt${autoPrint ? '?auto_print=true' : ''}`;
    const response = await fetch(url);

    if (response.ok) {
      const blob = await response.blob();
      const pdfUrl = URL.createObjectURL(blob);

      if (autoPrint) {
        // Printer automatically printed, just show success
        toast.success('Receipt printed!');
      } else {
        // Open PDF for manual print
        window.open(pdfUrl, '_blank');
      }
    }
  } catch (error) {
    toast.error('Failed to print receipt');
  }
};

// Usage
<button onClick={() => printReceipt(orderId, true)}>
  🖨️ Print Now (Auto)
</button>

<button onClick={() => printReceipt(orderId, false)}>
  📄 View PDF (Manual)
</button>
```

---

## Troubleshooting

### Issue: "Printer is disabled in configuration"

**Solution:** Set `PRINTER_ENABLED=true` in `.env` and restart server.

### Issue: "PRINTER_TYPE not set"

**Solution:** Set `PRINTER_TYPE` to `win32`, `usb`, or `serial` in `.env`.

### Issue: "Failed to connect to printer"

**Possible causes:**
1. Printer not powered on
2. USB cable not connected
3. Wrong printer name/ID
4. Missing drivers (Windows)
5. Permission issues (USB/Serial)

**Solutions:**
1. Check printer power and connection
2. Re-run `detect_printer.py` to verify configuration
3. For USB: May need to run with admin privileges
4. For Windows: Install printer drivers from manufacturer
5. Check Windows "Printers & Scanners" settings

### Issue: Print attempt fails but PDF works

This is **expected behavior**. The system prioritizes reliability:
- If printing fails, the request doesn't fail
- PDF is always returned
- Check server logs for print error details

### Issue: "python-escpos library not available"

**Solution:**
```bash
cd backend
uv add python-escpos
```

### Issue: Printer prints blank receipt

**Possible causes:**
1. Thermal paper loaded incorrectly (shiny side down)
2. Printer head needs cleaning
3. Paper roll empty

**Solutions:**
1. Reload thermal paper (check manufacturer guide)
2. Clean printer head with isopropyl alcohol
3. Replace paper roll

### Issue: Characters look wrong (encoding issues)

The printer module uses "Rs." instead of "₹" for better compatibility. This is intentional.

---

## Configuration Reference

### All Printer Environment Variables

```bash
# Enable/Disable automatic printing
PRINTER_ENABLED=true|false          # Default: false

# Connection type
PRINTER_TYPE=win32|usb|serial       # Required if enabled

# Windows Printer (win32)
PRINTER_NAME=<printer_name>         # Example: "Essae POS-60C"

# USB Printer (usb)
PRINTER_VENDOR_ID=<hex_vid>         # Example: "0x0dd4" or "0dd4"
PRINTER_PRODUCT_ID=<hex_pid>        # Example: "0x1234" or "1234"

# Serial Printer (serial)
PRINTER_PORT=<port>                 # Example: "COM3" or "/dev/ttyUSB0"
PRINTER_BAUDRATE=<baudrate>         # Example: 9600, 115200 (default: 9600)
```

---

## API Endpoint Reference

### GET /api/v1/orders/{order_id}/receipt

**Query Parameters:**
- `auto_print` (boolean, optional): If `true`, prints automatically to thermal printer

**Example Requests:**

```bash
# PDF only (manual print)
GET /api/v1/orders/1/receipt

# Auto-print + PDF
GET /api/v1/orders/1/receipt?auto_print=true
```

**Response:**
- Status 200: PDF file (application/pdf)
- Status 400: Order not paid or no payment found
- Status 404: Order not found

**Behavior:**
- If `auto_print=true` and `PRINTER_ENABLED=true`: Prints to thermal printer automatically
- If printing fails: Error is logged but request succeeds (PDF still returned)
- If `auto_print=false` or `PRINTER_ENABLED=false`: Only returns PDF (no printing)

---

## Production Deployment Checklist

Before going live with auto-print:

- [ ] Thermal printer installed and tested with `detect_printer.py`
- [ ] `.env` file configured with correct printer values
- [ ] `PRINTER_ENABLED=true` set in `.env`
- [ ] Backend restarted after configuration
- [ ] Test print successful with `?auto_print=true`
- [ ] Spare thermal paper rolls available
- [ ] Staff trained on when to use auto-print vs manual
- [ ] Backup plan documented if printer fails

---

## When to Use Auto-Print vs Manual

### Use Auto-Print (`?auto_print=true`) When:
- ✅ Receipt must print immediately (e.g., customer waiting)
- ✅ Cashier station with dedicated printer
- ✅ Printer is reliable and always available
- ✅ Want to reduce manual steps

### Use Manual Print (`?auto_print=false`) When:
- ✅ Want to preview receipt before printing
- ✅ Testing or development environment
- ✅ Printer reliability is uncertain
- ✅ Need to save/email PDF instead of printing
- ✅ Multiple printers available (let user choose)

**Pro Tip:** You can offer both options in your UI:
- "Print Now" button → `auto_print=true`
- "View PDF" button → `auto_print=false` (opens in new tab)

---

## Support & Resources

### Related Documentation
- `backend/detect_printer.py` - Printer detection script
- `backend/app/utils/printer.py` - Printer utility module
- `docs/THERMAL_PRINTER_TESTING.md` - Comprehensive printer testing guide
- `.env.example` - Configuration template with examples

### Need Help?
1. Check server logs for detailed error messages
2. Re-run `detect_printer.py` to verify configuration
3. Review `THERMAL_PRINTER_TESTING.md` for hardware troubleshooting
4. Check python-escpos documentation: https://python-escpos.readthedocs.io/

---

**Document Version:** 1.0
**Status:** Complete
**Last Updated:** 2025-11-04
