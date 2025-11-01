# ANG-36 Pre-Merge Checklist

Complete these steps before merging the order management API implementation.

---

## 🔍 Code Validation

### 1. Run Validation Script
```bash
cd backend
python scripts/validate_implementation.py
```

**Expected**: All checks pass ✅

**Status**: [ ]

---

### 2. Run Test Suite
```bash
cd backend
uv sync --extra dev
uv run pytest -v
```

**Expected**: 40+ tests pass, 3 skipped (auth-required)

**Status**: [ ]

---

### 3. Check Test Coverage
```bash
uv run pytest --cov=app/crud --cov=app/api/v1/endpoints/orders --cov-report=term-missing
```

**Expected**: 90%+ coverage on modified files

**Status**: [ ]

---

## 🚀 Manual Testing

### 4. Start Server
```bash
cd backend
uv run uvicorn app.main:app --reload
```

**Expected**: Server starts without errors on http://localhost:8000

**Status**: [ ]

---

### 5. Check Swagger UI
Open: http://localhost:8000/docs

**Verify**:
- [ ] All order endpoints visible
- [ ] Schemas display correctly
- [ ] Can execute test requests

**Status**: [ ]

---

### 6. Test Core Scenarios

Follow `MANUAL_TESTING_GUIDE.md`:

#### Must Test:
- [ ] Create new order → Gets order number ORD-YYYYMMDD-0001
- [ ] Create on same table → Updates existing order (same ID)
- [ ] Create on different table → Gets order number 0002
- [ ] Get active orders → Returns only active orders
- [ ] GST calculation → 18% on subtotal
- [ ] Order item snapshots → Preserves price and name
- [ ] Check table for active order → Returns order or null

**Status**: [ ]

---

## 📝 Code Review

### 7. Review Changes
```bash
git diff main...ang-36
```

**Check**:
- [ ] No debug code left
- [ ] No commented-out code
- [ ] Proper error handling
- [ ] Docstrings present
- [ ] Type hints used

**Status**: [ ]

---

### 8. Review Modified Files

#### Modified (4 files):
- [ ] `backend/app/crud/crud.py` - CRUD logic changes
- [ ] `backend/app/schemas/schemas.py` - New schema
- [ ] `backend/app/api/v1/endpoints/orders.py` - New endpoints
- [ ] `backend/app/api/deps.py` - Auth import

#### Created (8 files):
- [ ] `backend/tests/conftest.py` - Test fixtures
- [ ] `backend/tests/test_orders.py` - Unit tests
- [ ] `backend/tests/test_order_endpoints.py` - Integration tests
- [ ] `backend/tests/README.md` - Test documentation
- [ ] `backend/scripts/validate_implementation.py` - Validation script
- [ ] `IMPLEMENTATION_SUMMARY.md` - Implementation details
- [ ] `MANUAL_TESTING_GUIDE.md` - Testing guide
- [ ] `PRE_MERGE_CHECKLIST.md` - This file

**Status**: [ ]

---

## 🐛 Known Issues

### 9. Document Known Issues

**Auth-Required Endpoints**:
- PUT /api/orders/{order_id} - Logic complete, needs auth
- DELETE /api/orders/{order_id} - Logic complete, needs auth

**Action Required**: None (will be enabled when auth is implemented)

**Status**: [X] Documented

---

### 10. No Breaking Changes

**Verify**:
- [ ] Existing endpoints still work
- [ ] Database schema compatible
- [ ] API contracts unchanged (except new endpoints)

**Status**: [ ]

---

## 📊 Performance

### 11. Test Order Number Generation Under Load

Create 10 orders rapidly:
```bash
for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/v1/orders" \
    -H "Content-Type: application/json" \
    -d "{\"table_number\": $i, \"items\": [{\"menu_item_id\": 1, \"quantity\": 1}]}" &
done
wait
```

**Verify**: All orders have unique, sequential order numbers

**Status**: [ ]

---

## 📚 Documentation

### 12. Documentation Complete

**Check**:
- [ ] `IMPLEMENTATION_SUMMARY.md` - Explains what was done
- [ ] `MANUAL_TESTING_GUIDE.md` - How to test manually
- [ ] `backend/tests/README.md` - How to run tests
- [ ] Code docstrings - All functions documented
- [ ] Linear issue updated - Mark completed tasks

**Status**: [ ]

---

## 🔐 Security

### 13. Security Review

**Verify**:
- [ ] No sensitive data in logs
- [ ] SQL injection prevented (using ORM)
- [ ] Input validation (Pydantic schemas)
- [ ] Auth required on admin endpoints
- [ ] GST calculated server-side (not from client)

**Status**: [ ]

---

## 💾 Database

### 14. Database Compatibility

**Check**:
- [ ] No migrations needed (models already match)
- [ ] Test database seeds correctly
- [ ] Can create/update/cancel orders without errors

**Status**: [ ]

---

## ✅ Linear Issue

### 15. Update Linear Issue (ANG-36)

**Mark Complete**:
- [x] Implement `POST /api/orders` (create or update order with smart logic)
- [x] Implement `GET /api/orders/active` (list all active orders)
- [x] Implement `GET /api/orders/{order_id}` (get order details)
- [x] Implement `PUT /api/orders/{order_id}` (admin edit - requires auth)
- [x] Implement `DELETE /api/orders/{order_id}` (cancel order - requires auth)
- [x] Add business logic: one active order per table
- [x] Implement GST calculation (18% on subtotal)
- [x] Generate unique order numbers (ORD-YYYYMMDD-####)
- [x] Create order item snapshots (preserve menu details)
- [x] Test order creation, updates, and edge cases

**Status**: [ ]

---

## 🎯 Final Checklist

### Before Creating PR

- [ ] All tests pass
- [ ] Manual testing complete
- [ ] No console errors
- [ ] Code reviewed
- [ ] Documentation complete
- [ ] Linear issue updated

### PR Description Should Include

- [ ] Link to ANG-36
- [ ] Summary of changes
- [ ] Test coverage report
- [ ] Screenshots of Swagger UI
- [ ] Known limitations (auth-required endpoints)
- [ ] How to test manually

---

## 📋 Quick Verification Commands

Run all at once:

```bash
cd backend

# 1. Validate implementation
echo "=== Running Validation ==="
python scripts/validate_implementation.py

# 2. Run tests
echo -e "\n=== Running Tests ==="
uv run pytest -v

# 3. Check coverage
echo -e "\n=== Checking Coverage ==="
uv run pytest --cov=app/crud --cov=app/api/v1/endpoints/orders --cov-report=term

# 4. Start server (in background)
echo -e "\n=== Starting Server ==="
uv run uvicorn app.main:app --reload &
SERVER_PID=$!

# Wait for server to start
sleep 3

# 5. Test health endpoint
echo -e "\n=== Testing Health Endpoint ==="
curl http://localhost:8000/health

# 6. Kill server
kill $SERVER_PID

echo -e "\n=== All Checks Complete ==="
```

---

## ✅ Sign-Off

### Developer
- [ ] I have completed all items on this checklist
- [ ] I have tested the implementation thoroughly
- [ ] I am confident this is ready for code review

**Name**: _________________
**Date**: _________________

### Code Reviewer
- [ ] I have reviewed the code changes
- [ ] I have verified the test coverage
- [ ] I approve this implementation

**Name**: _________________
**Date**: _________________

---

## 🚀 Post-Merge Actions

After merging to main:

1. [ ] Delete branch `ang-36`
2. [ ] Close Linear issue ANG-36
3. [ ] Update project board
4. [ ] Deploy to staging (if applicable)
5. [ ] Notify team in Slack/Discord

---

**Note**: Some tests are skipped (auth-required endpoints). These will be enabled when authentication is implemented in a future ticket.
