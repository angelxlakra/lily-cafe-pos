#!/bin/bash

# Test Menu Management API Endpoints

BASE_URL="http://localhost:8000"

echo "============================================"
echo "Testing Lily Cafe POS - Menu Management API"
echo "============================================"
echo ""

# Test 1: Login and get token
echo "TEST 1: Login to get auth token"
echo "POST /api/v1/auth/login"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme123"}')
echo "$LOGIN_RESPONSE" | python -m json.tool
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo ""
echo "Token obtained: ${TOKEN:0:50}..."
echo ""

# Test 2: Create new category with auth
echo "============================================"
echo "TEST 2: Create new category (with auth)"
echo "POST /api/v1/categories"
curl -s -X POST "$BASE_URL/api/v1/categories" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Italian"}' | python -m json.tool
echo ""

# Test 3: List all categories
echo "============================================"
echo "TEST 3: List all categories"
echo "GET /api/v1/categories"
curl -s "$BASE_URL/api/v1/categories" | python -m json.tool | tail -20
echo ""

# Test 4: Create new menu item with auth
echo "============================================"
echo "TEST 4: Create new menu item (with auth)"
echo "POST /api/v1/menu"
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/menu" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Pizza Margherita","description":"Classic Italian pizza","price":15000,"category_id":6}')
echo "$CREATE_RESPONSE" | python -m json.tool
ITEM_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
echo ""

# Test 5: Get single menu item
echo "============================================"
echo "TEST 5: Get single menu item"
echo "GET /api/v1/menu/$ITEM_ID"
curl -s "$BASE_URL/api/v1/menu/$ITEM_ID" | python -m json.tool
echo ""

# Test 6: Update menu item with auth
echo "============================================"
echo "TEST 6: Update menu item (with auth)"
echo "PATCH /api/v1/menu/$ITEM_ID"
curl -s -X PATCH "$BASE_URL/api/v1/menu/$ITEM_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"price":16000,"is_available":true}' | python -m json.tool
echo ""

# Test 7: Delete menu item (soft delete) with auth
echo "============================================"
echo "TEST 7: Soft delete menu item (with auth)"
echo "DELETE /api/v1/menu/$ITEM_ID"
curl -s -X DELETE "$BASE_URL/api/v1/menu/$ITEM_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nHTTP Status: %{http_code}\n"
echo ""

# Test 8: Verify soft delete
echo "============================================"
echo "TEST 8: Verify item is soft deleted (is_available=false)"
echo "GET /api/v1/menu/$ITEM_ID"
curl -s "$BASE_URL/api/v1/menu/$ITEM_ID" | python -m json.tool | grep -A1 "is_available"
echo ""

echo "============================================"
echo "All tests completed!"
echo "============================================"
