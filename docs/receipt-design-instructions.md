# Receipt Design Instructions - Lily Cafe by Mary's Kitchen

## Overview
This document provides comprehensive design guidelines for creating a professional, readable, and legally compliant receipt for Lily Cafe by Mary's Kitchen.

---

## 1. Document Specifications

### Paper Size
- **Width:** 80mm (standard thermal receipt paper)
- **Margins:** 5mm on all sides
- **Orientation:** Portrait

### Color Scheme
- **Background:** White (#FFFFFF)
- **Primary Text:** Black (#000000)
- **Accent/Headers:** Dark Gray (#333333)
- **Separator Lines:** Medium Gray (#CCCCCC)

---

## 2. Typography

### Font Stack

**Primary Font (Body Text):**
- Font: Roboto or Open Sans
- Weights: Regular (400), Medium (500), Bold (700)
- Fallback: Arial, sans-serif

**Accent Font (Branding/Headers):**
- Font: Montserrat or Poppins
- Weights: SemiBold (600), Bold (700)
- Fallback: Arial Black, sans-serif

**Monospace Font (Numbers/Amounts):**
- Font: Roboto Mono or Source Code Pro
- Weight: Regular (400)
- Purpose: Ensures perfect alignment of decimal points
- Fallback: Courier New, monospace

### Font Sizes

```
Cafe Name/Logo:          24-28px (Bold)
Address:                 10-11px (Regular)
Contact Info:            10-11px (Regular)
GSTIN:                   10-11px (Regular)

Section Headers:         13-14px (Medium)
Order Number:            14-15px (Bold)
Order Details:           11-12px (Regular)

Table Headers:           11-12px (Bold)
Item Names:              12px (Regular)
Quantities:              12px (Regular)
Amounts:                 12px (Monospace)

Subtotals:               12px (Regular)
Tax Lines:               12px (Regular)
TOTAL:                   16-18px (Bold, Monospace)

Payment Methods:         12px (Regular)
Payment Amounts:         12px (Monospace)

Footer Message:          11-12px (Regular)
QR Code Labels:          10px (Regular)
```

### Line Spacing
- Body text: 1.4-1.6x font size
- Section spacing: 15-20px between major sections
- Item spacing: 8-10px between line items

---

## 3. Layout Structure

### Section Breakdown

#### A. Header Section
```
┌─────────────────────────────────────┐
│         [LOGO - Centered]           │
│   Lily Cafe by Mary's Kitchen       │
│  (Font: Montserrat Bold, 26px)      │
│                                     │
│ 14, Hawai Nagar Rd, Hawai Nagar,   │
│ Gitilpiri, Ranchi, Jharkhand 834003│
│   (Font: Roboto, 10px, Gray)       │
│                                     │
│  Tel: +91-1234567890 | info@        │
│        lilycafe.com                 │
│   (Font: Roboto, 10px, Gray)       │
│                                     │
│   GSTIN: 29ABCDE1234F1Z5            │
│   (Font: Roboto, 10px, Gray)       │
└─────────────────────────────────────┘
        ═══════════════════════
```

#### B. Order Information Section
```
┌─────────────────────────────────────┐
│ Order No: ORD-20251101-124119       │
│          (Bold, 14px)               │
│                                     │
│ Table: 49                           │
│ Customer: Test Customer             │
│          (Auto-Generated)           │
│ Date: 01-11-2025 09:59 AM           │
│        (Regular, 11px)              │
└─────────────────────────────────────┘
        ───────────────────────
```

#### C. Items Table Section
```
┌─────────────────────────────────────┐
│ Item            Qty  Rate    Amount │
│ ─────────────────────────────────── │
│                                     │
│ 2x Masala Dosa                      │
│    @ ₹80.00              ₹160.00    │
│                                     │
│ 1x Plain Dosa                       │
│    @ ₹60.00               ₹60.00    │
│                                     │
└─────────────────────────────────────┘
```

**Alignment Rules:**
- Item names: Left-aligned
- Quantities: After item name
- Rate: Left-aligned with indent
- Amounts: Right-aligned (monospace)

#### D. Totals Section
```
┌─────────────────────────────────────┐
│                                     │
│ Subtotal:                 ₹220.00   │
│ CGST (2.5%):                ₹5.50   │
│ SGST (2.5%):                ₹5.50   │
│        (Regular, 12px)              │
│ ─────────────────────────────────── │
│                                     │
│ TOTAL:                    ₹231.00   │
│        (Bold, 18px)                 │
│                                     │
└─────────────────────────────────────┘
```

**Tax Calculation Note:**
- Always split GST into CGST and SGST
- Each at 2.5% (total 5.0%)
- Show both percentage and amount
- Use monospace font for amounts

#### E. Payment Section
```
┌─────────────────────────────────────┐
│ Payments:                           │
│ ─────────────────────────────────── │
│                                     │
│ CASH:                     ₹115.50   │
│ UPI:                      ₹115.50   │
│                                     │
└─────────────────────────────────────┘
```

#### F. Footer Section
```
┌─────────────────────────────────────┐
│                                     │
│      Thank you for visiting!        │
│        Please visit again!          │
│        (Regular, 12px)              │
│                                     │
│ ═══════════════════════════════════ │
│                                     │
│      Rate Your Experience           │
│        (Medium, 13px)               │
│                                     │
│   [QR Code]         [QR Code]       │
│   100x100px         100x100px       │
│                                     │
│   Google           Feedback         │
│   Review            Form            │
│   (Regular, 10px)                   │
│                                     │
└─────────────────────────────────────┘
```

---

## 4. Visual Elements

### Separator Lines

**Thick Separator (Section breaks):**
- Character: `═` (double line)
- Width: Full width minus margins
- Color: #999999

**Thin Separator (Item divisions):**
- Character: `─` (single line)
- Width: Full width minus margins
- Color: #CCCCCC

**Usage:**
- After header
- After order information
- Before TOTAL line
- Before footer/QR codes

### QR Codes

**Specifications:**
- Size: 100x100px each
- Spacing: 20px between QR codes
- Background: White
- Foreground: Black
- Error correction: Level M (15%)

**QR Code 1 (Google Review):**
- Link: Google Business Profile review link
- Label: "Google Review"

**QR Code 2 (Feedback Form):**
- Link: Custom feedback form URL
- Label: "Feedback Form"

**Layout:**
```
      [QR]    [QR]
       │       │
    Google  Feedback
    Review   Form
```

---

## 5. Content Guidelines

### Number Formatting
- Currency symbol: ₹ (Indian Rupee)
- Decimal places: Always 2 decimal places
- Thousands separator: None (for readability on receipts)
- Right-align all amounts

### Date/Time Format
- Format: DD-MM-YYYY HH:MM AM/PM
- Example: 01-11-2025 09:59 AM

### Order Number Format
- Format: ORD-YYYYMMDD-HHMMSS
- Example: ORD-20251101-124119

### Text Hierarchy
1. **Most Important:** TOTAL amount, Order Number
2. **Important:** Item names, amounts, payment methods
3. **Secondary:** Contact info, tax breakdown, date/time
4. **Tertiary:** GSTIN, footer messages

---

## 6. Paper Size Configurations

### 80mm Paper (Standard) - Primary Configuration

**Document Specifications:**
- Width: 80mm
- Margins: 5mm on all sides
- Effective print width: 70mm

**Typography (80mm):**
```
Cafe Name/Logo:          24-28px (Bold)
Address:                 10-11px (Regular)
Contact Info:            10-11px (Regular)
GSTIN:                   10-11px (Regular)

Section Headers:         13-14px (Medium)
Order Number:            14-15px (Bold)
Order Details:           11-12px (Regular)

Table Headers:           11-12px (Bold)
Item Names:              12px (Regular)
Quantities:              12px (Regular)
Amounts:                 12px (Monospace)

Subtotals:               12px (Regular)
Tax Lines:               12px (Regular)
TOTAL:                   16-18px (Bold, Monospace)

Payment Methods:         12px (Regular)
Payment Amounts:         12px (Monospace)

Footer Message:          11-12px (Regular)
QR Code Labels:          10px (Regular)
```

**QR Codes:**
- Size: 100x100px each
- Spacing between codes: 20px
- Margin around codes: 10px

**Section Spacing:**
- Between major sections: 15-20px
- Between line items: 8-10px
- Line height: 1.4-1.6x font size

---

### 58mm Paper - Compact Configuration

**Document Specifications:**
- Width: 58mm
- Margins: 3mm on all sides
- Effective print width: 52mm

**Typography (58mm):**
```
Cafe Name/Logo:          20-22px (Bold)
Address:                 8-9px (Regular)
Contact Info:            8-9px (Regular)
GSTIN:                   8-9px (Regular)

Section Headers:         11-12px (Medium)
Order Number:            12-13px (Bold)
Order Details:           9-10px (Regular)

Table Headers:           9-10px (Bold)
Item Names:              10px (Regular)
Quantities:              10px (Regular)
Amounts:                 10px (Monospace)

Subtotals:               10px (Regular)
Tax Lines:               10px (Regular)
TOTAL:                   14-16px (Bold, Monospace)

Payment Methods:         10px (Regular)
Payment Amounts:         10px (Monospace)

Footer Message:          9-10px (Regular)
QR Code Labels:          8px (Regular)
```

**QR Codes:**
- Size: 80x80px each
- Spacing between codes: 15px
- Margin around codes: 8px
- Consider stacking QR codes vertically if needed

**Section Spacing:**
- Between major sections: 10-15px
- Between line items: 6-8px
- Line height: 1.3-1.5x font size

**Layout Modifications for 58mm:**

1. **Header Section:**
   - Consider removing logo or making it smaller (40x40px max)
   - Stack contact information vertically instead of inline
   - Abbreviate where possible (e.g., "Tel:" instead of "Telephone:")

2. **Order Information:**
   - Keep format similar but with tighter spacing
   - Consider abbreviations: "Ord No:" instead of "Order No:"

3. **Items Table:**
   - Remove "Qty" and "Rate" column headers
   - Use format: "2x Item Name @ ₹80.00" on one line
   - Amount on the same line, right-aligned
   - Example:
     ```
     2x Masala Dosa @ ₹80    ₹160.00
     1x Plain Dosa @ ₹60      ₹60.00
     ```

4. **QR Codes:**
   - Option A: Display QR codes side by side (80x80px each)
   - Option B: Stack vertically for better readability
   ```
   Option B Layout:
   
   Rate Your Experience
   
       [QR Code 80x80]
       Google Review
   
       [QR Code 80x80]
       Feedback Form
   ```

**58mm Example Layout:**
```
┌───────────────────────────────┐
│    Lily Cafe by Mary's        │
│        Kitchen                │
│   (Montserrat Bold, 20px)     │
│                               │
│ 14, Hawai Nagar Rd,          │
│ Hawai Nagar, Gitilpiri,      │
│ Ranchi, JH 834003            │
│ Tel: +91-1234567890          │
│ info@lilycafe.com            │
│ GSTIN: 29ABCDE1234F1Z5       │
│ (All: Roboto, 8px)           │
│                               │
├═══════════════════════════════┤
│                               │
│ Ord: ORD-20251101-124119     │
│      (Bold, 12px)             │
│ Table: 49                     │
│ Customer: Test Customer       │
│ Date: 01-11-2025 09:59 AM    │
│      (Regular, 9px)           │
│                               │
├───────────────────────────────┤
│                               │
│ 2x Masala Dosa @ ₹80          │
│                    ₹160.00    │
│                               │
│ 1x Plain Dosa @ ₹60           │
│                     ₹60.00    │
│                               │
├───────────────────────────────┤
│                               │
│ Subtotal:         ₹220.00    │
│ CGST (2.5%):        ₹5.50    │
│ SGST (2.5%):        ₹5.50    │
│ ───────────────────────────   │
│                               │
│ TOTAL:            ₹231.00    │
│      (Bold, 14px)             │
│                               │
├───────────────────────────────┤
│                               │
│ Payments:                     │
│ CASH:             ₹115.50    │
│ UPI:              ₹115.50    │
│                               │
├═══════════════════════════════┤
│                               │
│   Thank you for visiting!     │
│     Please visit again!       │
│                               │
├───────────────────────────────┤
│                               │
│   Rate Your Experience        │
│                               │
│     [QR Code 80x80]          │
│      Google Review            │
│                               │
│     [QR Code 80x80]          │
│      Feedback Form            │
│                               │
└───────────────────────────────┘
```

### Print Settings (Both Sizes)

**80mm Paper:**
- DPI: 203 (standard thermal printer)
- Color: Monochrome (Black & White)
- Print speed: Medium (for better quality)
- Paper feed: Auto-cut after print

**58mm Paper:**
- DPI: 203 (standard thermal printer)
- Color: Monochrome (Black & White)
- Print speed: Medium-Slow (for sharp text at smaller sizes)
- Paper feed: Auto-cut after print
- Consider higher contrast settings for smaller text

### CSS Implementation for Both Sizes

```css
/* 80mm Paper Configuration */
@media print and (max-width: 80mm) {
    body {
        width: 80mm;
        padding: 5mm;
        font-size: 12px;
    }
    
    .cafe-name {
        font-size: 26px;
    }
    
    .qr-code {
        width: 100px;
        height: 100px;
    }
}

/* 58mm Paper Configuration */
@media print and (max-width: 58mm) {
    body {
        width: 58mm;
        padding: 3mm;
        font-size: 10px;
    }
    
    .cafe-name {
        font-size: 20px;
    }
    
    .contact-info,
    .address {
        font-size: 8px;
        line-height: 1.3;
    }
    
    .order-number {
        font-size: 12px;
    }
    
    .total {
        font-size: 14px;
    }
    
    .qr-code {
        width: 80px;
        height: 80px;
        display: block;
        margin: 8px auto;
    }
    
    .qr-container {
        flex-direction: column;
        align-items: center;
    }
}
```

### Responsive Decision Logic

```javascript
// Automatic paper size detection
function getReceiptConfig() {
    const printerWidth = getPrinterWidth(); // in mm
    
    if (printerWidth <= 58) {
        return {
            size: '58mm',
            fontSize: 'small',
            qrSize: 80,
            margins: 3,
            qrLayout: 'stacked'
        };
    } else {
        return {
            size: '80mm',
            fontSize: 'standard',
            qrSize: 100,
            margins: 5,
            qrLayout: 'side-by-side'
        };
    }
}
```

---

## 7. Accessibility

### Readability
- Minimum font size: 10px
- Sufficient contrast ratio: 7:1 for body text
- Clear visual hierarchy
- Adequate spacing between elements

### Language Support
- Primary: English
- Ensure font supports rupee symbol (₹)
- Consider Hindi language support for future

---

## 8. Legal Compliance (India)

### Required Information (GST Act)
✓ Business name and address
✓ GSTIN number
✓ Order/Invoice number
✓ Date and time
✓ Item descriptions
✓ Item-wise amounts
✓ CGST and SGST breakdown (separate lines)
✓ Total amount
✓ Payment method

### Optional but Recommended
- Contact information
- Customer name (if available)
- Table number (for dine-in)
- Return policy
- Feedback mechanisms

---

## 9. Implementation Notes

### HTML/CSS Implementation

```css
/* Primary Fonts */
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap');

body {
    font-family: 'Roboto', Arial, sans-serif;
    width: 80mm;
    margin: 0;
    padding: 5mm;
}

.header {
    text-align: center;
    font-family: 'Montserrat', Arial Black, sans-serif;
}

.amount {
    font-family: 'Roboto Mono', Courier New, monospace;
    text-align: right;
}

.total {
    font-size: 18px;
    font-weight: bold;
}
```

### Print CSS

```css
@media print {
    @page {
        size: 80mm auto;
        margin: 0;
    }
    
    body {
        margin: 5mm;
    }
}
```

---

## 10. Example Complete Receipt Layout

```
┌─────────────────────────────────────────────┐
│              [LILY LOGO]                    │
│      Lily Cafe by Mary's Kitchen            │
│                                             │
│   14, Hawai Nagar Rd, Hawai Nagar,         │
│   Gitilpiri, Ranchi, Jharkhand 834003      │
│   Tel: +91-1234567890 | info@lilycafe.com  │
│   GSTIN: 29ABCDE1234F1Z5                   │
│                                             │
├═════════════════════════════════════════════┤
│                                             │
│   Order No: ORD-20251101-124119            │
│   Table: 49                                 │
│   Customer: Test Customer (Auto-Generated) │
│   Date: 01-11-2025 09:59 AM                │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│   Item                           Amount    │
│   ───────────────────────────────────────  │
│                                             │
│   2x Masala Dosa                           │
│      @ ₹80.00                    ₹160.00   │
│                                             │
│   1x Plain Dosa                            │
│      @ ₹60.00                     ₹60.00   │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│   Subtotal:                      ₹220.00   │
│   CGST (2.5%):                     ₹5.50   │
│   SGST (2.5%):                     ₹5.50   │
│   ─────────────────────────────────────    │
│                                             │
│   TOTAL:                         ₹231.00   │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│   Payments:                                 │
│   ─────────────────────────────────────    │
│   CASH:                          ₹115.50   │
│   UPI:                           ₹115.50   │
│                                             │
├═════════════════════════════════════════════┤
│                                             │
│         Thank you for visiting!             │
│           Please visit again!               │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│         Rate Your Experience                │
│                                             │
│      [QR Code]      [QR Code]              │
│         📱              📋                   │
│      Google         Feedback                │
│      Review          Form                   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 11. Testing Checklist

Before finalizing the design:

**General Tests:**
- [ ] Print test receipt on actual thermal paper
- [ ] Verify all text is readable at actual size
- [ ] Test QR codes scan properly from printed receipt
- [ ] Check alignment of amounts (decimal points)
- [ ] Verify CGST + SGST = Total GST
- [ ] Confirm GSTIN format is correct
- [ ] Test with various order sizes (1 item, 10 items, etc.)
- [ ] Verify date/time formatting
- [ ] Check spacing and margins
- [ ] Ensure all required legal information is present

**80mm Paper Specific:**
- [ ] Test side-by-side QR code layout
- [ ] Verify 100x100px QR codes scan properly
- [ ] Check that contact info fits on single line
- [ ] Confirm all fonts render at specified sizes
- [ ] Test with longest expected item names

**58mm Paper Specific:**
- [ ] Test stacked QR code layout (if using vertical layout)
- [ ] Verify 80x80px QR codes scan properly at print size
- [ ] Check text doesn't wrap unexpectedly
- [ ] Test abbreviated labels are clear
- [ ] Verify reduced font sizes are still legible
- [ ] Confirm items with long names wrap properly
- [ ] Test with maximum expected line items (ensure readability)
- [ ] Check that address wraps correctly across multiple lines

**Both Sizes:**
- [ ] Verify paper auto-cut works correctly
- [ ] Test print speed doesn't affect quality
- [ ] Check ink density/darkness is sufficient
- [ ] Ensure receipt doesn't fade quickly
- [ ] Test in different lighting conditions (readability)

---

## 12. Future Enhancements

Consider adding:
- Logo/branding improvements
- Loyalty program QR code
- Nutritional information option
- Allergen warnings
- Order type indicator (Dine-in/Takeaway/Delivery)
- Server name
- Estimated preparation time
- Return/refund policy
- Social media handles

---

**Document Version:** 1.0  
**Last Updated:** November 2, 2025  
**Created For:** Lily Cafe by Mary's Kitchen
