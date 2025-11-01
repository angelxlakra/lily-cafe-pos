# Thermal Printer Setup Guide

This guide explains how to set up direct thermal printing for receipts, eliminating browser print dialogs and margin issues.

## Overview

The system now supports two printing methods:

1. **PDF Generation** (Original) - Generates PDF receipts for browser printing
2. **Direct Thermal Printing** (New) - Sends ESC/POS commands directly to USB thermal printer

Direct thermal printing advantages:
- ✅ No browser print dialog
- ✅ Minimal top margin (no extra feed gap)
- ✅ Faster printing
- ✅ No cross-origin issues
- ✅ Better formatting control

## Prerequisites

### 1. Install Dependencies

Already included in `pyproject.toml`:
```bash
cd backend
uv sync --extra dev  # Installs pyusb for printer detection
```

### 2. Find Your Printer's USB IDs

Run the printer configuration script:

```bash
cd backend
python3 scripts/configure_printer.py
```

This will show:
```
🖨️  Seiben - XP-80C Thermal Printer
   Vendor ID:  0x0416 (1046)
   Product ID: 0x5011 (20497)
   Class: 0x07
```

**Note:** On Linux, you may need to run with `sudo` or add your user to the `lp` group:
```bash
sudo usermod -a -G lp $USER
# Then log out and back in
```

## Usage

### Option 1: API Endpoint (Recommended)

Use the new thermal print endpoint:

```bash
# Basic usage (uses default USB IDs)
POST /api/v1/orders/{order_id}/print-thermal

# With specific USB IDs
POST /api/v1/orders/{order_id}/print-thermal?vendor_id=0x0416&product_id=0x5011

# Test mode (no physical printer required)
POST /api/v1/orders/{order_id}/print-thermal?printer_type=dummy
```

Example with curl:
```bash
curl -X POST "http://localhost:8000/api/v1/orders/1/print-thermal?vendor_id=0x0416&product_id=0x5011"
```

Success response:
```json
{
  "message": "Receipt printed successfully",
  "order_id": 1,
  "order_number": "ORD-20251101-124119",
  "printer_type": "usb"
}
```

### Option 2: From Frontend

Update your frontend to call the thermal print endpoint instead of PDF:

```typescript
async function printDirectToThermal(orderId: number): Promise<void> {
  const response = await axios.post(
    `${API_BASE}/orders/${orderId}/print-thermal`,
    null,
    {
      params: {
        printer_type: 'usb',
        vendor_id: 0x0416,
        product_id: 0x5011
      }
    }
  );

  if (response.data.message) {
    console.log('✅ Printed:', response.data.message);
  }
}
```

## Common USB IDs

If auto-detection doesn't work, try these common values:

| Printer Brand | Vendor ID | Product ID |
|---------------|-----------|------------|
| Seiben/XPrinter | 0x0416 | 0x5011 |
| Epson TM-T82 | 0x04b8 | 0x0202 |
| Generic POS-80 | 0x0416 | 0x5011 |
| Star TSP100 | 0x0519 | 0x0001 |

## Troubleshooting

### Printer Not Found

**Error:** `USB thermal printer not found`

**Solutions:**
1. Check printer is connected and powered on
2. Run `python3 scripts/configure_printer.py` to find correct USB IDs
3. On Linux: Add user to `lp` group or run with `sudo`
4. Try unplugging and replugging the USB cable
5. Check USB cable is not damaged

### Permission Denied (Linux)

**Error:** `USBError: [Errno 13] Access denied`

**Solutions:**
```bash
# Option 1: Add user to lp group (recommended)
sudo usermod -a -G lp $USER
# Log out and back in

# Option 2: Create udev rule
sudo nano /etc/udev/rules.d/99-thermal-printer.rules
# Add: SUBSYSTEM=="usb", ATTR{idVendor}=="0416", ATTR{idProduct}=="5011", MODE="0666"
sudo udevadm control --reload-rules

# Option 3: Run backend with sudo (not recommended for production)
sudo uvicorn app.main:app
```

### Wrong Printer IDs

If the script shows the wrong device:

1. Disconnect all USB devices except the printer
2. Run the configuration script again
3. The printer should be the only device shown

### Printing Garbled Text

**Cause:** Wrong character encoding or printer model

**Solutions:**
1. Check printer supports ESC/POS commands
2. Verify printer is configured for UTF-8 encoding
3. Try updating printer firmware

### Logo Not Printing

**Cause:** Image format not supported or too large

**Solutions:**
1. Convert logo to PNG or JPG
2. Keep logo width under 512 pixels
3. Test without logo first: Remove `RESTAURANT_LOGO_PATH` from .env

## Testing Without Printer

Use dummy mode for testing:

```bash
POST /api/v1/orders/{order_id}/print-thermal?printer_type=dummy
```

This simulates printing without a physical printer and returns success.

## Features

The thermal printer output includes:

- ✅ Restaurant logo (if configured)
- ✅ Restaurant name and details
- ✅ Order number and table
- ✅ Date and time
- ✅ All order items with quantities and prices
- ✅ Subtotal and GST breakdown
- ✅ Total amount
- ✅ Payment methods
- ✅ Thank you message
- ✅ Auto paper cut

## Configuration Options

### Printer Settings

The thermal printer is configured with:
- **Top margin:** 0mm (minimal feed gap)
- **Paper width:** 80mm thermal paper
- **Character encoding:** UTF-8
- **Line spacing:** Optimized for thermal printers

### Customization

To customize the receipt layout, edit:
```
backend/app/utils/escpos_printer.py
```

Key methods:
- `print_receipt()` - Main receipt layout
- `format_currency()` - Currency formatting
- `configure_printer_margins()` - Margin settings

## Support

For issues or questions:
1. Check this guide first
2. Run the configuration script to verify printer detection
3. Check backend logs for error details
4. Test with dummy mode to isolate printer hardware issues

## Comparison: PDF vs Thermal

| Feature | PDF Method | Thermal Method |
|---------|-----------|---------------|
| Browser dialog | Yes | No |
| Top margin | ~15-20mm | ~0-3mm |
| Speed | Slower | Faster |
| Dependencies | Browser | USB driver |
| Network printing | Easy | Requires setup |
| Preview | Yes | No |
| Best for | Email/archive | Point of sale |
