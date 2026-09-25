# Order Management API - Quick Reference

**Base URL**: `http://localhost:8000/api/v1`
**Version**: 0.1 (ANG-36 Implementation)

---

## 📋 Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/orders` | No | Create/update order (smart upsert) |
| GET | `/orders/active` | No | List all active orders |
| GET | `/orders/{order_id}` | No | Get order details |
| GET | `/orders/table/{table_number}/active` | No | Get active order for table |
| PATCH | `/orders/{order_id}` | No | Update order metadata |
| PUT | `/orders/{order_id}` | ✅ Yes | Edit order items (admin) |
| DELETE | `/orders/{order_id}` | ✅ Yes | Cancel order (admin) |
| POST | `/orders/{order_id}/payments` | ✅ Yes | Add payment to order |
| GET | `/orders/{order_id}/payments` | No | List order payments |

---

## 🔹 POST /orders

**Create new order OR update existing order (smart logic)**

### Request
```json
{
  "table_number": 5,
  "customer_name": "John Doe",  // optional
  "items": [
    {"menu_item_id": 1, "quantity": 2},
    {"menu_item_id": 2, "quantity": 1}
  ]
}
```

### Response (201)
```json
{
  "id": 1,
  "order_number": "ORD-20250130-0001",
  "table_number": 5,
  "customer_name": "John Doe",
  "subtotal": 20000,        // ₹200 in paise
  "gst_amount": 1000,       // 5% = ₹10
  "total_amount": 21000,    // ₹210
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
    }
  ],
  "payments": []
}
```

### Behavior
- **If table empty**: Creates new order
- **If table has active order**: Updates that order (replaces items)
- **Items**: Completely replaced, not merged
- **GST**: Automatically calculated at the configured rate (default 5%)

---

## 🔹 GET /orders/active

**List all active (unpaid) orders**

### Request
```
GET /api/v1/orders/active
```

### Response (200)
```json
[
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
    "order_items": [...],
    "payments": []
  },
  {
    "id": 2,
    "order_number": "ORD-20250130-0002",
    "table_number": 3,
    ...
  }
]
```

### Use Case
Waiter views all ongoing orders across all tables.

---

## 🔹 GET /orders/{order_id}

**Get single order with full details**

### Request
```
GET /api/v1/orders/1
```

### Response (200)
Full order object (same as POST response).

### Response (404)
```json
{
  "detail": "Order not found"
}
```

---

## 🔹 GET /orders/table/{table_number}/active

**Check if table has active order**

### Request
```
GET /api/v1/orders/table/5/active
```

### Response (200) - Order exists
```json
{
  "id": 1,
  "order_number": "ORD-20250130-0001",
  "table_number": 5,
  ...
}
```

### Response (200) - No order
```json
null
```

### Use Case
Frontend checks if table is occupied before allowing new order.

---

## 🔹 PATCH /orders/{order_id}

**Update order metadata (status, customer name)**

### Request
```json
{
  "customer_name": "Jane Doe",
  "status": "active"  // optional
}
```

### Response (200)
Updated order object.

### Note
Does NOT change order items. Use PUT for that.

---

## 🔹 PUT /orders/{order_id} 🔐

**Admin: Edit order items**

### Auth Required
```
Authorization: Bearer <token>
```

### Request
```json
{
  "items": [
    {"menu_item_id": 1, "quantity": 3},
    {"menu_item_id": 2, "quantity": 1}
  ],
  "customer_name": "Updated Name"  // optional
}
```

### Response (200)
Updated order with recalculated totals.

### Response (401)
```json
{
  "detail": "Could not validate credentials"
}
```

### Use Case
Admin fixes order mistake or handles customer change request.

---

## 🔹 DELETE /orders/{order_id} 🔐

**Admin: Cancel order**

### Auth Required
```
Authorization: Bearer <token>
```

### Request
```
DELETE /api/v1/orders/1
```

### Response (200)
```json
{
  "message": "Order canceled successfully",
  "order_id": 1
}
```

### Response (400)
```json
{
  "detail": "Cannot cancel a paid order"
}
```

### Behavior
- Sets `status` to "canceled"
- Soft delete (order remains in database)
- Cannot cancel paid orders

---

## 🔹 POST /orders/{order_id}/payments 🔐

**Add payment to order**

### Auth Required
```
Authorization: Bearer <token>
```

### Request
```json
{
  "payment_method": "upi",  // "upi", "cash", "card"
  "amount": 23600
}
```

### Response (200)
```json
{
  "id": 1,
  "payment_method": "upi",
  "amount": 23600,
  "created_at": "2025-01-30T10:00:00"
}
```

### Behavior
- If total payments = order total: Order status → "paid"
- Supports split payments

---

## 🔹 GET /orders/{order_id}/payments

**List payments for order**

### Request
```
GET /api/v1/orders/1/payments
```

### Response (200)
```json
[
  {
    "id": 1,
    "payment_method": "upi",
    "amount": 20000,
    "created_at": "2025-01-30T10:00:00"
  },
  {
    "id": 2,
    "payment_method": "cash",
    "amount": 3600,
    "created_at": "2025-01-30T10:01:00"
  }
]
```

---

## 🔹 POST /orders/{order_id}/payments/batch 🔐

**Add multiple payments at once (split payment support)**

### Auth Required
```
Authorization: Bearer <token>
```

### Request
```json
{
  "payments": [
    {
      "payment_method": "upi",
      "amount": 20000
    },
    {
      "payment_method": "cash",
      "amount": 3600
    }
  ]
}
```

### Response (201)
```json
[
  {
    "id": 1,
    "payment_method": "upi",
    "amount": 20000,
    "created_at": "2025-01-30T10:00:00"
  },
  {
    "id": 2,
    "payment_method": "cash",
    "amount": 3600,
    "created_at": "2025-01-30T10:00:00"
  }
]
```

### Response (400)
```json
{
  "detail": "Payment total 15000 does not match order total 23600. Expected 23600 more to complete payment."
}
```

### Behavior
- ✅ **Atomic transaction** - All payments created together or none
- ✅ **Validation** - Total must equal order amount exactly
- ✅ **Auto-marks as paid** - Order status becomes "paid" when complete
- ❌ **Cannot overpay** - Prevents payment total > order total
- ❌ **Cannot double-pay** - Rejects if order already paid

### Use Case
Preferred method for completing orders with split payments (e.g., ₹200 UPI + ₹36 cash).

---

## 🔹 GET /orders/{order_id}/receipt

**Generate PDF receipt for paid order**

### Auth Required
❌ No authentication required (waiters can print)

### Request
```
GET /api/v1/orders/1/receipt
```

### Response (200)
```
Content-Type: application/pdf
Content-Disposition: inline; filename=receipt-ORD-20250131-0001.pdf

[PDF Binary Data]
```

### Response (400)
```json
{
  "detail": "Cannot generate receipt for unpaid order"
}
```

### Response (404)
```json
{
  "detail": "Order not found"
}
```

### Receipt Format
- **Width:** 80mm (thermal printer compatible)
- **Includes:**
  - Restaurant name, address, phone, email, GSTIN
  - Order number, table, date/time
  - All items with quantities and prices
  - Subtotal, GST at the configured rate, total
  - Payment methods used (UPI/Cash/Card)
  - Thank you message

### Use Case
Print receipt after payment completion for customer records and GST compliance.

---

## 💰 GST Calculation

**Rate**: 5% by default. The rate is stored under the `app.gst_rate` key in the
settings store (`backend/app/core/settings_store.py`) and is editable by the owner
from the Settings page — it is not an environment variable.

**Formula**:
```
subtotal = sum(item.quantity × item.unit_price)
gst_amount = int(subtotal × gst_rate / 100)
total_amount = subtotal + gst_amount
```

**Example** (at the default 5%):
- 2× Masala Dosa (₹80 each) = ₹160
- 1× Coffee (₹40) = ₹40
- **Subtotal**: ₹200
- **GST (5%)**: ₹10
- **Total**: ₹210

On the printed receipt the rate is split into equal CGST and SGST lines
(2.5% + 2.5% at the default rate).

**Important**: All amounts in **paise** (₹1 = 100 paise) to avoid float precision issues.

---

## 🔢 Order Numbers

**Format**: `ORD-YYYYMMDD-####`

**Examples**:
- `ORD-20250130-0001` - First order of Jan 30, 2025
- `ORD-20250130-0002` - Second order of Jan 30, 2025
- `ORD-20250131-0001` - First order of Jan 31, 2025 (counter resets)

**Generation**:
- Sequential within the day
- Resets daily at midnight
- Unique across all orders

---

## 📊 Order Statuses

| Status | Description | Can Edit? | Can Cancel? |
|--------|-------------|-----------|-------------|
| `active` | Order placed, not paid | ✅ Yes | ✅ Yes |
| `paid` | Bill generated, payment complete | ❌ No | ❌ No |
| `canceled` | Order canceled by admin | ❌ No | N/A |

---

## 🎯 Business Rules

### One Active Order Per Table
- Table can have only 1 active order at a time
- Posting to table with active order **updates** that order
- After payment, new orders can be created for that table

### Order Item Snapshots
- `menu_item_name` and `unit_price` saved at order time
- Price changes don't affect existing orders
- Historical data integrity maintained

### Items Replacement
- POST/PUT replaces **all** items, doesn't merge
- Frontend should send complete item list
- Waiter workflow: build entire order → submit

### GST Server-Side
- Always calculated on server
- Client values ignored
- Prevents manipulation

---

## 🚫 Error Codes

| Code | Scenario | Example |
|------|----------|---------|
| 400 | Invalid request | Menu item not found, order already paid |
| 401 | Unauthorized | Missing/invalid auth token |
| 404 | Not found | Order doesn't exist |
| 422 | Validation error | Invalid quantity, missing fields |

---

## 🧪 Testing Tips

### Using curl
```bash
# Set variables
API="http://localhost:8000/api/v1"
TOKEN="your-token-here"

# Create order
curl -X POST "$API/orders" \
  -H "Content-Type: application/json" \
  -d '{"table_number": 5, "items": [{"menu_item_id": 1, "quantity": 2}]}'

# Get active orders
curl "$API/orders/active"

# Edit order (with auth)
curl -X PUT "$API/orders/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"items": [{"menu_item_id": 2, "quantity": 1}]}'
```

### Using Swagger UI
1. Open: `http://localhost:8000/docs`
2. Expand `/api/v1/orders` section
3. Click "Try it out" on any endpoint
4. Fill in parameters and request body
5. Click "Execute"

---

## 📱 Frontend Integration

### Waiter Flow
```javascript
// 1. Check if table has order
const checkTable = async (tableNumber) => {
  const response = await fetch(`/api/v1/orders/table/${tableNumber}/active`);
  return await response.json(); // null or order object
};

// 2. Create/update order
const saveOrder = async (tableNumber, items) => {
  const response = await fetch('/api/v1/orders', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({table_number: tableNumber, items})
  });
  return await response.json();
};

// 3. Get all active orders
const getActiveOrders = async () => {
  const response = await fetch('/api/v1/orders/active');
  return await response.json();
};
```

### Admin Flow
```javascript
// 1. Edit order
const editOrder = async (orderId, items, token) => {
  const response = await fetch(`/api/v1/orders/${orderId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({items})
  });
  return await response.json();
};

// 2. Cancel order
const cancelOrder = async (orderId, token) => {
  const response = await fetch(`/api/v1/orders/${orderId}`, {
    method: 'DELETE',
    headers: {'Authorization': `Bearer ${token}`}
  });
  return await response.json();
};
```

---

## 🔗 Related Endpoints

### Menu Management
- `GET /api/v1/menu` - List menu items
- `POST /api/v1/menu` - Create menu item (admin)
- `PUT /api/v1/menu/{id}` - Update menu item (admin)

### Categories
- `GET /api/v1/categories` - List categories
- `POST /api/v1/categories` - Create category (admin)

### Authentication
- `POST /api/v1/auth/login` - Get access token

---

## 📞 Support

**Documentation**: See `/docs` in project root
**Issue**: ANG-36 on Linear
**Swagger UI**: http://localhost:8000/docs
**Test Coverage**: `backend/tests/README.md`

---

**Last Updated**: 2025-01-30
**Version**: 0.1.0 (ANG-36 Implementation)
