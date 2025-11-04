# Order Chit (Kitchen Ticket) Auto-Print Guide

**Version:** 1.0
**Last Updated:** 2025-11-04

This guide explains the **automatic order chit printing** feature that prints kitchen tickets when waiters save orders.

---

## Overview

An **Order Chit** (also called Kitchen Ticket or KOT - Kitchen Order Ticket) is a simplified receipt that prints automatically when:
- ✅ Waiters create new orders (POST /api/v1/orders)
- ✅ Admins edit existing orders (PUT /api/v1/orders/{order_id})

### What's an Order Chit?

It's a **minimal, readable ticket** for kitchen/service staff with:
- 📍 **Very Large Table Number** - 72pt font (much larger than ESC/POS limit)
- 📋 **Menu Items** - Large text with quantities
- 💰 **Amounts** - Item prices and total
- ✏️ **Notes Section** - Blank space for handwritten customizations

**No branding, no GST, no payment details** - just what the kitchen needs to prepare the order.

### Printing Method: PDF-Based (New!)

Order chits now use **PDF-based printing** instead of ESC/POS commands:
- ✅ **Much larger table numbers** - 72pt font vs ESC/POS 8x limit
- ✅ **Better font control** - Professional typography
- ✅ **Automatic fallback** - Falls back to ESC/POS if PDF printing fails
- ✅ **Same setup** - Uses existing printer configuration

---

## What It Looks Like

```
================================
          TABLE 5
================================

Order: ORD-20251104-0001
Time: 02:30 PM
Name: Rahul

================================

2x Masala Dosa
   Rs.160.00

1x Filter Coffee
   Rs.40.00

3x Samosa
   Rs.90.00

================================

      TOTAL: Rs.290.00

--------------------------------
NOTES:




--------------------------------
```

**Key Features:**
- **Very large table number** (72pt font in PDF mode, or 8x ESC/POS fallback)
- **Large item text** (16pt font) with quantities
- Regular-sized amounts
- Space for handwritten notes ("Extra spicy", "No onions", etc.)

**Printing Technology:**
- Primary: PDF-based printing (requires `PRINTER_NAME` configured)
- Fallback: ESC/POS direct printing
- Automatic switching based on availability

---

## How It Works

### Setup (One-Time)

1. **Configure printer** (same as receipt printer):
   ```bash
   cd backend
   uv run python detect_printer.py
   ```

2. **Update `.env`**:
   ```bash
   PRINTER_ENABLED=true
   PRINTER_TYPE=win32
   PRINTER_NAME=Essae POS-60C
   ```

3. **(Optional) Install SumatraPDF for Windows** - Recommended for better PDF printing:
   - Download from: https://www.sumatrapdfreader.org/
   - Install to default location
   - Provides silent PDF printing without popup dialogs

4. **Restart backend**:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

### Automatic Behavior

Once `PRINTER_ENABLED=true`:

#### When Waiter Creates Order
```bash
POST /api/v1/orders
{
  "table_number": 5,
  "items": [
    {"menu_item_id": 1, "quantity": 2},
    {"menu_item_id": 3, "quantity": 1}
  ]
}
```
**→ Order chit prints automatically!**

#### When Admin Edits Order
```bash
PUT /api/v1/orders/1
{
  "items": [
    {"menu_item_id": 1, "quantity": 3},  # Changed quantity
    {"menu_item_id": 5, "quantity": 1}   # Added item
  ]
}
```
**→ Updated order chit prints automatically!**

---

## Comparison: Order Chit vs Receipt

| Feature | Order Chit | Receipt |
|---------|-----------|---------|
| **When printed** | Order saved | Payment completed |
| **Trigger** | Automatic (if enabled) | `?auto_print=true` parameter |
| **Purpose** | Kitchen/service reference | Customer proof of payment |
| **Contains** | Table, items, notes space | Full branding, GST, payments |
| **Size** | Minimal, large text | Detailed, standard text |
| **Branding** | None | Restaurant name, logo, GSTIN |
| **GST Breakdown** | No | Yes (CGST + SGST) |
| **Payment Details** | No | Yes (UPI, Cash, Card) |
| **QR Codes** | No | Optional (feedback) |
| **Notes Space** | Yes (handwritten) | No |

---

## Use Cases

### 1. Kitchen Orders
**Scenario:** Waiter takes order at table, saves it.
**Flow:**
1. Waiter opens app, selects Table 5
2. Adds: 2x Masala Dosa, 1x Coffee
3. Clicks "Save Order"
4. **Chit prints in kitchen** with table number and items
5. Kitchen staff prepares food based on chit

**Benefits:**
- Kitchen sees orders immediately
- Large text readable from distance
- Space for special requests

### 2. Order Modifications
**Scenario:** Customer adds items to existing order.
**Flow:**
1. Admin/waiter selects existing order
2. Adds: 1x Samosa
3. Saves changes
4. **New chit prints** showing all items (old + new)
5. Kitchen prepares additional item

**Benefits:**
- Kitchen stays updated
- No confusion about what to prepare
- Original order + new items visible

### 3. Handwritten Customizations
**Scenario:** Customer wants "extra spicy" or "no onions".
**Flow:**
1. Waiter saves order (chit prints)
2. Waiter writes "EXTRA SPICY" in notes section with pen
3. Hands chit to kitchen

**Benefits:**
- Special requests clearly communicated
- Reduces verbal confusion
- Kitchen has written reference

---

## Configuration

### Using Same Printer (Recommended)

The order chit uses the **same printer** as receipts:

```bash
# .env
PRINTER_ENABLED=true
PRINTER_TYPE=win32
PRINTER_NAME=Essae POS-60C
RECEIPT_PAPER_SIZE=80mm
```

**Result:**
- Order chits print when orders saved
- Receipts print when `?auto_print=true` used
- Both use same thermal printer
- Single configuration, simple setup

### Disabling Chit Printing

To disable order chits but keep receipt printing available:

```bash
PRINTER_ENABLED=false
```

**Result:**
- No automatic chit printing
- Receipts can still be generated as PDFs (manual print)
- System functions normally without printer

---

## Frontend Integration

### React Example

```typescript
// When creating an order
const createOrder = async (orderData) => {
  try {
    const response = await fetch('/api/v1/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(orderData)
    });

    if (response.ok) {
      const order = await response.json();

      // Order chit already printed automatically!
      toast.success(`Order saved for Table ${order.table_number}!`);

      // Optional: Show confirmation that chit printed
      if (printerEnabled) {
        toast.info('Order chit printed in kitchen');
      }
    }
  } catch (error) {
    toast.error('Failed to save order');
  }
};
```

**No special code needed** - chits print automatically when `PRINTER_ENABLED=true`.

---

## Troubleshooting

### Issue: Chit not printing when order saved

**Check:**
1. Is `PRINTER_ENABLED=true` in `.env`?
2. Did you restart backend after changing `.env`?
3. Is printer powered on and connected?
4. Run `detect_printer.py` to verify connection

**Solution:**
```bash
# Verify settings
cat backend/.env | grep PRINTER

# Test printer
cd backend
uv run python detect_printer.py

# Restart backend
uv run uvicorn app.main:app --reload
```

### Issue: Chit prints but receipt doesn't

**This is normal!** Order chits print automatically, but receipts require `?auto_print=true` parameter:

```bash
# Chit: Automatic (no parameter needed)
POST /api/v1/orders

# Receipt: Needs parameter
GET /api/v1/orders/1/receipt?auto_print=true
```

### Issue: Text too small on chit (SOLVED!)

**Good news!** Order chits now use **PDF-based printing** with much larger fonts:
- Table number: **72pt font** (80mm paper) or 56pt (58mm paper)
- This is **much larger** than the ESC/POS 8x limit
- Item text: 16pt font
- Professional typography with better readability

**To adjust table number size further:**
Edit `backend/app/utils/pdf_generator.py` around line 673:
```python
# Change table number font size (default: 72pt for 80mm)
table_number_size = 96  # Even larger!
draw_centered(str(order.table_number), y_position, "Helvetica-Bold", table_number_size)
```

**If PDF printing fails, system falls back to ESC/POS:**
- ESC/POS limit: 8x height/width maximum
- To ensure PDF printing works, install SumatraPDF (Windows) or ensure CUPS is configured (Linux)

### Issue: Chit prints but has encoding errors

Some printers don't support rupee symbol (₹). The system uses "Rs." as fallback:
```
Rs.160.00  ✓ (Compatible)
₹160.00    ✗ (May not print correctly)
```

This is **intentional** for maximum printer compatibility.

### Issue: Notes section too small

To add more blank lines for notes, edit `backend/app/utils/pdf_generator.py` around line 738:

```python
# Add blank space for notes (default: 6 lines)
for _ in range(10):  # Increase to 10 lines
    add_spacing(8)
```

Or for ESC/POS fallback, edit `backend/app/utils/printer.py` around line 555:

```python
printer.text("NOTES:\n")
# Add more newlines
for _ in range(8):  # More lines
    printer.text("\n")
```

---

## PDF Printing Methods

The system tries multiple methods to print PDFs automatically:

### Windows

1. **SumatraPDF** (Recommended)
   - Silent printing without popups
   - Reliable for thermal printers
   - Auto-detected if installed
   - Install from: https://www.sumatrapdfreader.org/

2. **PowerShell Print Command**
   - Built-in Windows method
   - May show print dialog briefly
   - Fallback if SumatraPDF not found

3. **win32print Library**
   - Python library method
   - Requires `pywin32` package
   - Final fallback option

### Linux

1. **CUPS (lp command)**
   - Standard Linux printing
   - Requires CUPS configured
   - Command: `lp -d PrinterName file.pdf`

### Fallback

If all PDF methods fail, system automatically falls back to **ESC/POS** direct printing (original method with 8x font limit).

---

## Advanced Configuration

### Print Chits to Different Printer

If you have **two printers** (one for chits, one for receipts):

**Not currently supported**, but you can:
1. Set up printer for chits
2. Manually switch printer when printing receipts
3. Or use separate POS stations (one for orders, one for billing)

### Logging Chit Prints

Check server logs to verify chits are printing:

```bash
# View logs
tail -f backend/logs/app.log

# Look for:
"Order chit printed for table 5"
"Failed to print order chit for table 5"
"Error printing order chit: <error details>"
```

---

## API Reference

### POST /api/v1/orders (Create Order)

**Behavior:**
- Creates new order in database
- If `PRINTER_ENABLED=true`: Prints order chit automatically
- Returns order details (including items, totals)

**Response:**
```json
{
  "id": 1,
  "order_number": "ORD-20251104-0001",
  "table_number": 5,
  "status": "active",
  "total_amount": 29000,
  "items": [...]
}
```

**Chit Printing:**
- Automatic, no parameter needed
- Prints even if request succeeds
- If printing fails, order still saves (graceful fallback)

---

### PUT /api/v1/orders/{order_id} (Edit Order)

**Behavior:**
- Updates order items and recalculates totals
- If `PRINTER_ENABLED=true`: Prints updated order chit automatically
- Requires admin authentication

**Response:**
```json
{
  "id": 1,
  "order_number": "ORD-20251104-0001",
  "table_number": 5,
  "status": "active",
  "total_amount": 35000,
  "items": [...]
}
```

**Chit Printing:**
- Automatic after successful edit
- Shows all current items (not just changes)
- Kitchen gets updated ticket

---

## Best Practices

### For Restaurants

1. **Place printer near kitchen** - So kitchen staff see chits immediately
2. **Use 80mm paper** - More readable, better layout
3. **Train staff on notes section** - Write customizations clearly
4. **Keep spare paper** - Don't run out during rush hours
5. **Test before service** - Print test chit to verify working

### For Developers

1. **Log all print attempts** - Easier troubleshooting
2. **Graceful fallback** - Order saves even if print fails
3. **Don't fail requests** - Print errors are warnings, not failures
4. **Use same printer config** - Keep setup simple

### For Waiters

1. **Wait for chit to print** - Don't leave before seeing output
2. **Write clearly in notes** - Kitchen needs to read it
3. **Hand chit to kitchen** - Don't leave on counter
4. **Verify items** - Check chit matches order before giving to kitchen

---

## Production Deployment Checklist

Before going live:

- [ ] Printer installed near kitchen/service area
- [ ] `PRINTER_ENABLED=true` in `.env`
- [ ] Backend restarted after configuration
- [ ] Test order chit prints successfully
- [ ] Spare thermal paper rolls available (at least 5)
- [ ] Staff trained on reading chits
- [ ] Staff trained on writing in notes section
- [ ] Kitchen staff knows to expect chits
- [ ] Backup process documented (if printer fails)
- [ ] Test during mock service (simulate rush hour)

---

## Related Documentation

- **`AUTO_PRINT_SETUP_GUIDE.md`** - Setting up thermal printer
- **`THERMAL_PRINTER_TESTING.md`** - Hardware troubleshooting
- **`backend/detect_printer.py`** - Printer detection script
- **`backend/app/utils/printer.py`** - Printer implementation

---

## Support

### Common Questions

**Q: Do chits include GST breakdown?**
A: No, chits are minimal. GST only on customer receipts.

**Q: Can I print chits without enabling auto-print?**
A: No, chits only print when `PRINTER_ENABLED=true`.

**Q: What if printer runs out of paper?**
A: Orders still save! Load paper and reprint from order history if needed.

**Q: Can I customize chit format?**
A: Yes, edit `backend/app/utils/printer.py` function `print_order_chit()`.

**Q: Do canceled orders print chits?**
A: No, only active orders (not canceled/paid).

---

**Document Version:** 1.0
**Status:** Complete
**Last Updated:** 2025-11-04
