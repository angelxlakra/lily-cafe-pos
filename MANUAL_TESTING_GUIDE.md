# ANG-36 Manual Testing Guide

This guide provides step-by-step instructions for manually testing the order management API.

## Prerequisites

1. **Start the backend server**:
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload
   ```

2. **Server should be running at**: `http://localhost:8000`

3. **Access Swagger UI** (easiest way to test): `http://localhost:8000/docs`

---

## Test Scenario 1: Create New Order (Smart POST)

### Setup: Create test data first

#### 1. Create a Category
```bash
curl -X POST "http://localhost:8000/api/v1/categories" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Category"}'
```

**Expected Response** (201):
```json
{
  "id": 1,
  "name": "Test Category",
  "created_at": "2025-01-30T10:00:00"
}
```

#### 2. Create Menu Items
```bash
# Masala Dosa - ₹80
curl -X POST "http://localhost:8000/api/v1/menu" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Masala Dosa",
    "description": "Crispy dosa with potato filling",
    "price": 8000,
    "category_id": 1
  }'

# Filter Coffee - ₹40
curl -X POST "http://localhost:8000/api/v1/menu" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Filter Coffee",
    "description": "South Indian filter coffee",
    "price": 4000,
    "category_id": 1
  }'
```

---

### Test: Create order on Table 5

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": 5,
    "customer_name": "John Doe",
    "items": [
      {"menu_item_id": 1, "quantity": 2},
      {"menu_item_id": 2, "quantity": 1}
    ]
  }'
```

**Expected Response** (201):
```json
{
  "id": 1,
  "order_number": "ORD-20250130-0001",
  "table_number": 5,
  "customer_name": "John Doe",
  "subtotal": 20000,
  "gst_amount": 3600,
  "total_amount": 23600,
  "status": "active",
  "created_at": "2025-01-30T10:00:00",
  "updated_at": "2025-01-30T10:00:00",
  "order_items": [
    {
      "id": 1,
      "menu_item_id": 1,
      "menu_item_name": "Masala Dosa",
      "quantity": 2,
      "unit_price": 8000,
      "subtotal": 16000
    },
    {
      "id": 2,
      "menu_item_id": 2,
      "menu_item_name": "Filter Coffee",
      "quantity": 1,
      "unit_price": 4000,
      "subtotal": 4000
    }
  ],
  "payments": []
}
```

**✅ Verify**:
- Order number format: `ORD-YYYYMMDD-0001`
- Subtotal: 2×₹80 + 1×₹40 = ₹200 (20000 paise)
- GST (18%): ₹36 (3600 paise)
- Total: ₹236 (23600 paise)
- Order items have snapshots (menu_item_name, unit_price)

---

## Test Scenario 2: Update Existing Order (Smart POST)

### Test: Post another order to same table

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": 5,
    "items": [
      {"menu_item_id": 1, "quantity": 3}
    ]
  }'
```

**Expected Response** (201):
```json
{
  "id": 1,
  "order_number": "ORD-20250130-0001",
  "table_number": 5,
  "customer_name": "John Doe",
  "subtotal": 24000,
  "gst_amount": 4320,
  "total_amount": 28320,
  "status": "active",
  "order_items": [
    {
      "id": 3,
      "menu_item_id": 1,
      "menu_item_name": "Masala Dosa",
      "quantity": 3,
      "unit_price": 8000,
      "subtotal": 24000
    }
  ],
  "payments": []
}
```

**✅ Verify**:
- **Same order ID** (1) - updated, not created new
- **Same order number** - preserved
- **Items replaced** (not merged) - only Dosa now, Coffee is gone
- **Totals recalculated**: 3×₹80 = ₹240, GST = ₹43.20, Total = ₹283.20

---

## Test Scenario 3: Sequential Order Numbers

### Test: Create order on different table

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": 3,
    "items": [
      {"menu_item_id": 2, "quantity": 2}
    ]
  }'
```

**Expected Response**:
```json
{
  "id": 2,
  "order_number": "ORD-20250130-0002",
  ...
}
```

**✅ Verify**:
- Order number incremented: `0002`
- Different order ID: `2`
- Independent of Table 5's order

---

## Test Scenario 4: Get Active Orders

### Test: List all active orders

```bash
curl -X GET "http://localhost:8000/api/v1/orders/active"
```

**Expected Response** (200):
```json
[
  {
    "id": 1,
    "order_number": "ORD-20250130-0001",
    "table_number": 5,
    "total_amount": 28320,
    "status": "active",
    ...
  },
  {
    "id": 2,
    "order_number": "ORD-20250130-0002",
    "table_number": 3,
    "total_amount": 9440,
    "status": "active",
    ...
  }
]
```

**✅ Verify**:
- Both orders returned
- Status is "active" for both

---

## Test Scenario 5: Get Order by ID

### Test: Get specific order

```bash
curl -X GET "http://localhost:8000/api/v1/orders/1"
```

**Expected Response** (200):
Full order details with items and payments.

### Test: Get non-existent order

```bash
curl -X GET "http://localhost:8000/api/v1/orders/99999"
```

**Expected Response** (404):
```json
{
  "detail": "Order not found"
}
```

---

## Test Scenario 6: Check Active Order for Table

### Test: Check if Table 5 has active order

```bash
curl -X GET "http://localhost:8000/api/v1/orders/table/5/active"
```

**Expected Response** (200):
Returns the active order for Table 5.

### Test: Check empty table

```bash
curl -X GET "http://localhost:8000/api/v1/orders/table/10/active"
```

**Expected Response** (200):
```json
null
```

---

## Test Scenario 7: Update Order Status (PATCH)

### Test: Update customer name

```bash
curl -X PATCH "http://localhost:8000/api/v1/orders/1" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Jane Doe"
  }'
```

**Expected Response** (200):
Order with updated customer_name.

---

## Test Scenario 8: Admin Edit Order (PUT) ⚠️ Requires Auth

### Test: Edit order items

```bash
curl -X PUT "http://localhost:8000/api/v1/orders/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "items": [
      {"menu_item_id": 2, "quantity": 5}
    ]
  }'
```

**Expected Response** (200):
Order with items replaced and totals recalculated.

**Without Auth**:
Expected Response (401): Unauthorized

---

## Test Scenario 9: Cancel Order (DELETE) ⚠️ Requires Auth

### Test: Cancel an active order

```bash
curl -X DELETE "http://localhost:8000/api/v1/orders/2" \
  -H "Authorization: Bearer <token>"
```

**Expected Response** (200):
```json
{
  "message": "Order canceled successfully",
  "order_id": 2
}
```

### Test: Verify order is canceled

```bash
curl -X GET "http://localhost:8000/api/v1/orders/2"
```

**Expected Response**:
```json
{
  "id": 2,
  "status": "canceled",
  ...
}
```

### Test: Check it's not in active orders

```bash
curl -X GET "http://localhost:8000/api/v1/orders/active"
```

**Expected**: Order 2 should NOT appear in the list.

---

## Test Scenario 10: GST Calculation Edge Cases

### Test: Single item order

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": 7,
    "items": [
      {"menu_item_id": 1, "quantity": 1}
    ]
  }'
```

**Verify**:
- Subtotal: 8000 paise (₹80)
- GST: 1440 paise (₹14.40)
- Total: 9440 paise (₹94.40)

### Test: Multiple quantities

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": 8,
    "items": [
      {"menu_item_id": 1, "quantity": 5},
      {"menu_item_id": 2, "quantity": 3}
    ]
  }'
```

**Verify**:
- Subtotal: (5×8000) + (3×4000) = 52000 paise (₹520)
- GST: 9360 paise (₹93.60)
- Total: 61360 paise (₹613.60)

---

## Test Scenario 11: Error Handling

### Test: Invalid menu item

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": 1,
    "items": [
      {"menu_item_id": 99999, "quantity": 1}
    ]
  }'
```

**Expected Response** (400):
```json
{
  "detail": "Menu item 99999 not found"
}
```

### Test: Zero quantity

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": 1,
    "items": [
      {"menu_item_id": 1, "quantity": 0}
    ]
  }'
```

**Expected Response** (422):
Validation error - quantity must be > 0.

### Test: Invalid table number

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": 0,
    "items": [
      {"menu_item_id": 1, "quantity": 1}
    ]
  }'
```

**Expected Response** (422):
Validation error - table_number must be >= 1.

---

## Test Scenario 12: Order Item Snapshots

### Test: Create order, then change menu price

1. **Create order**:
```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "table_number": 9,
    "items": [{"menu_item_id": 1, "quantity": 1}]
  }'
```

2. **Change menu item price**:
```bash
curl -X PUT "http://localhost:8000/api/v1/menu/1" \
  -H "Content-Type: application/json" \
  -d '{"price": 9000}'
```

3. **Get order again**:
```bash
curl -X GET "http://localhost:8000/api/v1/orders/[order_id]"
```

**✅ Verify**:
- Order item still shows `unit_price: 8000` (old price preserved)
- Menu item now has `price: 9000` (new price)
- Historical data integrity maintained

---

## Quick Test Checklist

### Core Functionality
- [ ] Create new order on empty table
- [ ] Update order on table with active order
- [ ] Order numbers sequential within day
- [ ] GST calculated at 18%
- [ ] Order items snapshot prices/names
- [ ] Get all active orders
- [ ] Get order by ID
- [ ] Check table for active order

### Admin Functions (requires auth)
- [ ] Edit order items (PUT)
- [ ] Cancel order (DELETE)
- [ ] Cannot cancel paid order

### Error Handling
- [ ] Invalid menu item ID
- [ ] Zero/negative quantity
- [ ] Invalid table number
- [ ] Non-existent order (404)

### Business Rules
- [ ] One active order per table
- [ ] Totals recalculated on updates
- [ ] Items replaced (not merged)
- [ ] Canceled orders not in active list

---

## Using Swagger UI (Recommended)

1. **Open**: `http://localhost:8000/docs`

2. **Expand** the `/api/v1/orders` section

3. **Try it out** on each endpoint

4. **See** request/response schemas and examples

5. **Test** auth-required endpoints by clicking "Authorize" button

---

## Troubleshooting

### Issue: "Connection refused"
**Solution**: Make sure server is running: `uv run uvicorn app.main:app --reload`

### Issue: "404 Not Found"
**Solution**: Check URL - should be `http://localhost:8000/api/v1/orders` (note `/api/v1` prefix)

### Issue: "422 Validation Error"
**Solution**: Check request body matches schema - use Swagger UI to see expected format

### Issue: "401 Unauthorized" on admin endpoints
**Solution**: Authentication needs to be implemented. Tests are skipped until auth is ready.

---

## Next Steps

1. ✅ **Run validation script**: `python backend/scripts/validate_implementation.py`

2. ✅ **Run test suite**: `cd backend && uv run pytest -v`

3. ✅ **Manual testing**: Follow this guide

4. 📝 **Document results**: Note any issues or unexpected behavior

5. 🚀 **Ready for code review**: Create PR with test results
