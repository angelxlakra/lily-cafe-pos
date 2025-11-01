# Print Receipt Test Buttons - Usage Guide

## Overview
Two one-click test buttons have been added to the homepage to test the complete receipt printing flow with or without a physical printer.

---

## What They Do

### 🖨️ Print Receipt (Requires Printer)

When you click the **"🖨️ Print Receipt"** button:

1. ✅ **Authenticates** with admin credentials
2. ✅ **Creates** a test order (Table 99, 2× Item 1 + 1× Item 2)
3. ✅ **Processes** payment (cash for full amount)
4. ✅ **Generates** receipt PDF (80mm thermal format)
5. ✅ **Triggers** browser print dialog
6. ✅ **Shows** success/error feedback

### 👁️ View in Tab (No Printer Needed)

When you click the **"👁️ View in Tab"** button:

1. ✅ **Authenticates** with admin credentials
2. ✅ **Creates** a test order (Table 99, 2× Item 1 + 1× Item 2)
3. ✅ **Processes** payment (cash for full amount)
4. ✅ **Generates** receipt PDF (80mm thermal format)
5. ✅ **Opens** receipt in new browser tab
6. ✅ **Shows** success/error feedback

**Use this option when:**
- Testing without a physical printer
- Verifying receipt content before printing
- Saving PDF to disk for documentation

---

## How to Use

### Prerequisites

**1. Backend Running:**
```bash
cd backend
uv run uvicorn app.main:app --reload
```

**2. Database Seeded:**
```bash
cd backend
uv run python -m scripts.seed_data
```

**3. Frontend Running:**
```bash
cd frontend
npm run dev
```

### Usage Steps - Print Receipt

1. **Open frontend:** http://localhost:5173
2. **Click** "🖨️ Print Receipt" button
3. **Wait** 2-3 seconds (watch status updates)
4. **Print dialog appears** automatically
5. **Select** your thermal printer
6. **Print!** ✅

### Usage Steps - View in Tab

1. **Open frontend:** http://localhost:5173
2. **Click** "👁️ View in Tab" button
3. **Wait** 2-3 seconds (watch status updates)
4. **New tab opens** with PDF
5. **View/Download** the receipt
6. **Done!** ✅

---

## Visual Feedback

### While Processing:
```
🖨️ Test Receipt Printer
━━━━━━━━━━━━━━━━━━━━━━━━━
One-click test: Create order → Process payment → Print/View receipt

[⏳ Processing...] [⏳ Processing...]  ← Both buttons show spinner + status
```

### On Success (Print):
```
[🖨️ Print Receipt] [👁️ View in Tab]

┌─────────────────────────────────────┐
│ ✅ Receipt printed successfully!    │  ← Green success message
└─────────────────────────────────────┘
```

### On Success (View):
```
[🖨️ Print Receipt] [👁️ View in Tab]

┌─────────────────────────────────────┐
│ ✅ Receipt opened successfully!     │  ← Green success message
└─────────────────────────────────────┘
```

### On Error:
```
[🖨️ Print Receipt] [👁️ View in Tab]

┌─────────────────────────────────────┐
│ ❌ Print failed: Order not found    │  ← Red error message
└─────────────────────────────────────┘
```

---

## Configuration

### Change Test Order Items

Edit `frontend/src/utils/printTestReceipt.ts`:

```typescript
// Line 10-16
const TEST_ORDER = {
  table_number: 99,
  customer_name: 'Test Customer (Auto-Generated)',
  items: [
    { menu_item_id: 1, quantity: 2 }, // ← Change these!
    { menu_item_id: 2, quantity: 1 }, // ← Based on your seed data
  ],
};
```

**Find your menu item IDs:**
```bash
curl http://localhost:8000/api/v1/menu/items | jq '.[] | {id, name}'
```

### Change Admin Credentials

If you changed the default admin credentials, update:

```typescript
// Line 34-37 in printTestReceipt.ts
const response = await axios.post(`${API_BASE}/auth/login`, {
  username: 'admin',      // ← Change if different
  password: 'admin123',   // ← Change if different
});
```

### Change Payment Method

```typescript
// Line 51-55
payments: [
  { payment_method: 'upi', amount: totalAmount },  // ← Change to 'upi' or 'card'
]
```

---

## Design System Integration

Both buttons follow Lily Cafe's design system:

### Colors Used:
- **Background:** `cream` (#F5E6D3) - Warm, inviting section
- **Print Button:** `info` (#2196F3) - Blue for primary action
- **View Button:** `lily-green` (#8B9D83) - Green for secondary action
- **Success:** `success` (#4CAF50) - Green feedback
- **Error:** `error` (#F44336) - Red feedback
- **Text:** `coffee-brown` (#6F4E37) - Brand color for headings

### Styling:
- Uses custom `btn` utility (48px min touch target)
- Follows 8px spacing grid
- Smooth transitions and hover effects
- Disabled state with visual feedback
- Responsive on mobile
- Flexbox layout with 12px gap between buttons

---

## Troubleshooting

### Issue: "CORS Error"
**Solution:** Add CORS middleware to backend:

```python
# In backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "Menu item X not found"
**Solution:** Update `TEST_ORDER` items to match your seed data (see Configuration above)

### Issue: "Failed to get auth token"
**Solution:** Check backend is running and admin credentials are correct

### Issue: "Print dialog doesn't appear"
**Solution:**
1. Check browser console for errors (F12)
2. Allow popups for localhost in browser settings
3. Try a different browser (Chrome/Firefox recommended)
4. **Alternative:** Use "👁️ View in Tab" button instead (doesn't require print dialog)

### Issue: "New tab doesn't open" (View in Tab button)
**Solution:**
1. Check browser popup blocker settings
2. Allow popups for localhost:5173
3. Look for blocked popup icon in address bar
4. Temporarily disable popup blocker for testing

### Issue: "Receipt PDF loads but printer doesn't respond"
**Solution:**
1. Check printer is connected and powered on
2. Verify printer is set as default in OS
3. Try printing a test page from system settings first
4. See THERMAL_PRINTER_TESTING.md for detailed printer troubleshooting

---

## Technical Details

### API Flow:
```
POST /api/v1/auth/login
  ↓ (get token)
POST /api/v1/orders
  ↓ (order_id, total_amount)
POST /api/v1/orders/{order_id}/payments/batch
  ↓ (marks order as paid)
GET /api/v1/orders/{order_id}/receipt
  ↓ (PDF binary)
window.print()
```

### State Management:
```typescript
isPrinting: boolean       // Button disabled during operation
printStatus: string       // Progress messages
printError: string        // Error messages
```

### Error Handling:
- Network errors caught and displayed
- Axios errors extract API error messages
- 3s auto-hide for success messages
- 5s auto-hide for error messages

---

## Files Modified

1. **frontend/src/App.tsx**
   - Added Print Receipt test section with two buttons
   - Added state management for processing status
   - Added success/error feedback UI
   - Handlers for both print and view actions

2. **frontend/src/utils/printTestReceipt.ts** (new file)
   - Complete test flow logic
   - API calls (auth, order, payment, receipt)
   - Print dialog trigger (`printTestReceipt`)
   - New tab opener (`viewTestReceipt`)
   - Shared helper functions

---

## Removing This Feature

When you're done testing and want to remove this:

**Option 1: Quick Remove (keep utility function)**
```tsx
// In App.tsx, delete the entire test section (lines 62-181)
// Keep printTestReceipt.ts for programmatic use if needed
```

**Option 2: Complete Remove**
```bash
# Delete the utility file
rm frontend/src/utils/printTestReceipt.ts

# Revert App.tsx to original
git checkout HEAD -- frontend/src/App.tsx
```

**Option 3: Keep View Button, Remove Print**
```tsx
// In App.tsx, remove only the "Print Receipt" button
// Keep "View in Tab" for development/testing without printer
```

---

## Next Steps

After verifying the button works:

1. ✅ Test with actual thermal printer
2. ✅ Verify receipt format (80mm width)
3. ✅ Check GST calculations are accurate
4. ✅ Test different order sizes (1 item, 10+ items)
5. ✅ Test split payments (modify utility to use multiple payment methods)

See `THERMAL_PRINTER_TESTING.md` for comprehensive printer testing guide.

---

**Document Version:** 1.0
**Created:** 2025-11-01
**Related:** ANG-37 - Payment processing and receipt PDF generation
