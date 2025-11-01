# Thermal Printer Testing Guide

**Purpose:** Instructions for testing receipt PDF generation on an actual 80mm thermal printer.

**Related:** ANG-37 - Payment processing and receipt PDF generation

---

## Prerequisites

### Hardware Required
- ✅ 80mm thermal receipt printer (ESC/POS compatible)
- ✅ USB cable or network connection
- ✅ Thermal paper roll (80mm width)
- ✅ Computer with printer drivers installed

### Software Required
- ✅ Backend server running (`uv run uvicorn app.main:app --reload`)
- ✅ PDF reader (Preview on Mac, Adobe Reader, etc.)
- ✅ CUPS or printer management software (for driver installation)

### Test Data Required
You need a **paid order** to generate a receipt. Follow these steps:

---

## Creating Test Data

### Step 1: Start the Backend
```bash
cd backend
uv run uvicorn app.main:app --reload
```

Server will start at: `http://localhost:8000`

### Step 2: Create a Test Order

**Option A: Using curl**
```bash
# Create order
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": 1,
    "customer_name": "Test Customer",
    "items": [
      {"menu_item_id": 1, "quantity": 2},
      {"menu_item_id": 2, "quantity": 1}
    ]
  }'
```

**Option B: Using HTTPie**
```bash
http POST http://localhost:8000/api/v1/orders \
  table_number=1 \
  customer_name="Test Customer" \
  items:='[{"menu_item_id": 1, "quantity": 2}, {"menu_item_id": 2, "quantity": 1}]'
```

**Save the order_id from the response!**

### Step 3: Add Payment (Using order_id from Step 2)

```bash
# Replace {order_id} with actual ID
curl -X POST http://localhost:8000/api/v1/orders/{order_id}/payments/batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "payments": [
      {"payment_method": "upi", "amount": 20000},
      {"payment_method": "cash", "amount": 3600}
    ]
  }'
```

**Note:** Adjust amounts to match your order total!

---

## Testing Receipt Generation

### Method 1: Browser Testing

1. **Open in browser:**
   ```
   http://localhost:8000/api/v1/orders/{order_id}/receipt
   ```

2. **What you should see:**
   - PDF opens directly in browser
   - Narrow width (80mm ≈ 3.15 inches)
   - All order details visible

3. **Save the PDF:**
   - Right-click → Save As
   - Name: `receipt-test.pdf`

### Method 2: Command Line Download

**Using curl:**
```bash
curl -o receipt.pdf http://localhost:8000/api/v1/orders/{order_id}/receipt
```

**Using HTTPie:**
```bash
http GET http://localhost:8000/api/v1/orders/{order_id}/receipt > receipt.pdf
```

**Using wget:**
```bash
wget -O receipt.pdf http://localhost:8000/api/v1/orders/{order_id}/receipt
```

---

## PDF Verification Checklist

Before printing, verify the PDF contains:

### Header Section
- [ ] Restaurant name: "Lily Cafe by Mary's Kitchen"
- [ ] Address lines (both lines visible)
- [ ] Phone and email
- [ ] GSTIN number

### Order Information
- [ ] Order number (format: ORD-YYYYMMDD-####)
- [ ] Table number
- [ ] Customer name (if provided)
- [ ] Date and time (format: DD-MM-YYYY HH:MM AM/PM)

### Items Section
- [ ] Item names with quantities (e.g., "2x Masala Dosa")
- [ ] Unit prices shown
- [ ] Item subtotals aligned right
- [ ] All items from order present

### Calculations
- [ ] Subtotal amount
- [ ] GST amount (18%)
- [ ] Total amount (bold)
- [ ] All amounts in ₹ (Rupee symbol)

### Payment Details
- [ ] "Payments:" header
- [ ] Each payment method listed (UPI/CASH/CARD)
- [ ] Payment amounts
- [ ] Sum of payments = total amount

### Footer
- [ ] "Thank you for visiting!" message
- [ ] "Please visit again!" message

---

## Physical Printer Testing

### Setup Your Printer

#### macOS
1. **Install drivers:** Download from printer manufacturer
2. **Add printer:** System Preferences → Printers & Scanners → +
3. **Configure:**
   - Paper size: 80mm (or "Receipt")
   - Margins: Minimal (2-3mm)
   - Orientation: Portrait

#### Linux (CUPS)
```bash
# Install CUPS if not installed
sudo apt-get install cups

# Add printer
sudo lpadmin -p ThermalPrinter -v usb://path/to/printer

# Set as default
lpadmin -d ThermalPrinter
```

#### Windows
1. Install manufacturer drivers
2. Control Panel → Devices and Printers → Add Printer
3. Configure 80mm paper size

### Print the Receipt

#### Method 1: Print from PDF Viewer
1. Open `receipt.pdf` in PDF reader
2. File → Print
3. Select thermal printer
4. **Settings:**
   - Paper: 80mm / Receipt
   - Scale: 100% (no scaling!)
   - Margins: Minimal
5. Print

#### Method 2: Command Line Print

**macOS:**
```bash
lpr -P YourPrinterName receipt.pdf
```

**Linux:**
```bash
lp -d YourPrinterName receipt.pdf
```

**Windows (PowerShell):**
```powershell
Start-Process -FilePath "receipt.pdf" -Verb Print
```

---

## Quality Verification

### Visual Inspection
After printing, check:

#### Layout & Formatting
- [ ] Paper width matches (80mm)
- [ ] No text cutoff at margins
- [ ] Left-aligned text aligns properly
- [ ] Right-aligned amounts align properly
- [ ] Centered text (header, footer) centered correctly
- [ ] Line separators print cleanly

#### Text Quality
- [ ] All text is legible
- [ ] Font size appropriate (not too small)
- [ ] No blurring or smudging
- [ ] Rupee symbol (₹) renders correctly
- [ ] Numbers are clear and readable

#### Content Accuracy
- [ ] Order number matches test order
- [ ] All items present
- [ ] Quantities correct
- [ ] Prices match expected values
- [ ] Calculations accurate:
  - Subtotal = sum of item subtotals
  - GST = 18% of subtotal
  - Total = subtotal + GST
- [ ] Payment methods listed correctly
- [ ] Payment amounts sum to total

#### Paper Handling
- [ ] Paper feeds smoothly
- [ ] No jams
- [ ] Auto-cut works (if supported)
- [ ] Receipt length appropriate (not too long)

---

## Common Issues & Solutions

### Issue: Text Too Small
**Symptoms:** Hard to read, squinting required

**Solution:** Increase font sizes in `backend/app/utils/pdf_generator.py`
```python
# Line 70: Restaurant name
draw_centered(settings.RESTAURANT_NAME, y_position, "Helvetica-Bold", 16)  # Was 14

# Line 93: Order number
draw_left(f"Order No: {order.order_number}", y_position, "Helvetica-Bold", 11)  # Was 10

# Line 110-111: Item headers
draw_left("Item", y_position, "Helvetica-Bold", 10)  # Was 9
draw_right("Amount", y_position, "Helvetica-Bold", 10)  # Was 9
```

### Issue: Text Cut Off at Edges
**Symptoms:** First/last characters missing on lines

**Solution:** Increase margins in `pdf_generator.py`
```python
# Lines 49-50
x_left = 7 * mm_unit  # Was 5mm
x_right = RECEIPT_WIDTH - 7 * mm_unit  # Was 5mm
```

### Issue: Receipt Too Long
**Symptoms:** Uses too much paper, wasteful

**Solution:** Reduce line spacing in `pdf_generator.py`
```python
# Line 47
line_height = 4 * mm_unit  # Was 5mm

# Or reduce spacing between sections
y_position -= line_height * 0.6  # Was 0.8
```

### Issue: Rupee Symbol Not Printing
**Symptoms:** Shows as "?" or box character

**Solution:** Printer may not support Unicode. Try:
```python
# In pdf_generator.py, line 32
return f"Rs.{rupees:.2f}"  # Instead of ₹
```

### Issue: Printer Not Detected
**Symptoms:** Can't find printer in print dialog

**Solutions:**
1. Check USB/network connection
2. Verify printer is powered on
3. Install/update printer drivers from manufacturer
4. Restart print spooler:
   - Mac: `sudo launchctl stop org.cups.cupsd && sudo launchctl start org.cups.cupsd`
   - Linux: `sudo systemctl restart cups`
   - Windows: Restart "Print Spooler" service

### Issue: PDF Doesn't Print (Blank Output)
**Symptoms:** Printer receives job but nothing prints

**Solutions:**
1. **Check printer mode:** Some thermal printers need specific mode
2. **Convert to image first:**
   ```bash
   # Install ImageMagick
   brew install imagemagick  # macOS
   sudo apt-get install imagemagick  # Linux

   # Convert PDF to PNG
   convert -density 300 receipt.pdf receipt.png

   # Print image
   lpr -P YourPrinter receipt.png
   ```
3. **Use raster mode:** In printer settings, enable raster printing

---

## Printer-Specific Notes

### Epson TM-T20 / TM-T88
- **Driver:** Official Epson TM-Intelligent driver
- **Paper:** 80mm thermal
- **CUPS settings:**
  - Paper Size: Receipt 80mm
  - Print Quality: Standard
  - Paper Reduction: Off
- **Auto-cut:** Supported (enable in driver)

### Star Micronics TSP143
- **Driver:** StarPRNT
- **Paper:** 80mm thermal
- **Settings:**
  - Receipt mode: ON
  - Paper width: 80mm
  - Buzzer: Optional
- **Auto-cut:** Supported

### Generic ESC/POS Printer
- **Driver:** Generic ESC/POS driver
- **May need:** Manual configuration
- **Test command:**
  ```bash
  echo -e "\x1B\x40Hello World\x0A\x0A\x1D\x56\x00" > /dev/usb/lp0
  ```

### Bluetooth Thermal Printers
- **Pair first:** System Bluetooth settings
- **Driver:** May need manufacturer-specific driver
- **Connection:** Often appears as serial port
- **Tip:** USB connection more reliable for testing

---

## Advanced Testing Scenarios

### Test 1: Single Item Order
**Purpose:** Verify minimal receipt

```bash
# Small order
{
  "table_number": 1,
  "items": [{"menu_item_id": 1, "quantity": 1}]
}
```

**Expected:** Short receipt, all sections present

### Test 2: Large Order (10+ Items)
**Purpose:** Test pagination/overflow

```bash
# Large order
{
  "table_number": 1,
  "items": [
    {"menu_item_id": 1, "quantity": 2},
    {"menu_item_id": 2, "quantity": 3},
    {"menu_item_id": 3, "quantity": 1},
    ...  # Add 10+ items
  ]
}
```

**Expected:** All items fit, no cutoff

### Test 3: Split Payment (3 Methods)
**Purpose:** Verify multiple payment methods

```bash
{
  "payments": [
    {"payment_method": "upi", "amount": 10000},
    {"payment_method": "card", "amount": 10000},
    {"payment_method": "cash", "amount": 3600}
  ]
}
```

**Expected:** All 3 methods listed

### Test 4: Long Item Names
**Purpose:** Test text wrapping

```bash
{
  "items": [
    {"menu_item_id": X, "quantity": 1}  // Item with very long name
  ]
}
```

**Expected:** Name doesn't overlap with price

### Test 5: Special Characters
**Purpose:** Test encoding

```bash
{
  "customer_name": "Test & Co. (Pvt) Ltd"
}
```

**Expected:** Special chars render correctly

---

## Performance Testing

### Test Receipt Generation Speed

```python
import time
import requests

order_id = 1  # Use actual paid order ID
url = f"http://localhost:8000/api/v1/orders/{order_id}/receipt"

# Time 100 requests
start = time.time()
for i in range(100):
    response = requests.get(url)
    assert response.status_code == 200

elapsed = time.time() - start
print(f"100 receipts in {elapsed:.2f}s")
print(f"Average: {elapsed/100*1000:.2f}ms per receipt")
```

**Expected:** < 100ms per receipt

---

## Production Deployment Checklist

Before deploying to production:

### Hardware Setup
- [ ] Thermal printer installed and tested
- [ ] Spare paper rolls available
- [ ] Printer connected via reliable connection (USB preferred)
- [ ] Auto-cut feature working (if available)
- [ ] Printer accessible from POS station

### Software Configuration
- [ ] Backend server configured with correct restaurant details
- [ ] GSTIN verified and correct
- [ ] Test receipts printed successfully
- [ ] Error handling tested (unpaid orders, missing orders)

### Staff Training
- [ ] Staff knows how to print receipts
- [ ] Staff knows how to reload paper
- [ ] Staff knows basic troubleshooting
- [ ] Backup plan if printer fails (email receipts?)

### GST Compliance
- [ ] GSTIN displays on all receipts
- [ ] GST breakdown accurate (18%)
- [ ] All required information present:
  - [ ] Business name and address
  - [ ] GSTIN
  - [ ] Invoice/order number
  - [ ] Date and time
  - [ ] Item details
  - [ ] Tax breakdown
  - [ ] Total amount

### Stress Testing
- [ ] Printed 50+ consecutive receipts
- [ ] No memory leaks observed
- [ ] Paper roll replacement tested mid-shift
- [ ] Printer recovery after paper jam tested
- [ ] Network/connection reliability verified

---

## Troubleshooting Reference

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| Blank receipt | Thermal head dirty | Clean with isopropyl alcohol |
| Faded print | Paper quality or heat settings | Use better paper, increase heat |
| Paper jam | Incorrect paper loading | Reload paper correctly |
| Won't print | Driver issue | Reinstall drivers |
| Cuts in wrong place | Auto-cut misconfigured | Adjust cut position in driver |
| Slow printing | Large PDF | Optimize PDF or use raster |

---

## Support Resources

- **ReportLab Docs:** https://www.reportlab.com/docs/reportlab-userguide.pdf
- **ESC/POS Commands:** https://reference.epson-biz.com/modules/ref_escpos/
- **CUPS Manual:** https://www.cups.org/doc/
- **Printer Manual:** Consult manufacturer documentation

---

## Sign-Off Checklist

Before marking thermal printing as complete:

- [ ] PDF generates successfully for all test orders
- [ ] Physical print test completed on actual thermal printer
- [ ] Receipt is legible and professional-looking
- [ ] All required information present and accurate
- [ ] GST compliance verified (GSTIN, breakdown, etc.)
- [ ] No text cutoff or formatting issues
- [ ] Printer integrates smoothly with POS workflow
- [ ] Staff trained on printing receipts
- [ ] Backup procedure documented (if printer fails)
- [ ] Performance meets requirements (<100ms per receipt)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-01
**Related Issue:** ANG-37
