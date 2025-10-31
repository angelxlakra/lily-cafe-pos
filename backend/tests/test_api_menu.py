"""
API endpoint tests for Menu Item routes.
Tests /api/v1/menu endpoints.
"""

import pytest
from fastapi import status


class TestListMenuItems:
    """Tests for GET /api/v1/menu endpoint."""

    def test_list_menu_items_empty(self, client):
        """Test listing menu items when database is empty."""
        response = client.get("/api/v1/menu")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    def test_list_menu_items_default_available_only(self, client, sample_menu_items):
        """Test that by default only available items are returned."""
        response = client.get("/api/v1/menu")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return 2 items (Masala Dosa and Filter Coffee, not Samosa)
        assert len(data) == 2
        assert all(item["is_available"] for item in data)
        assert not any(item["name"] == "Samosa" for item in data)

    def test_list_menu_items_all(self, client, sample_menu_items):
        """Test listing all menu items including unavailable."""
        response = client.get("/api/v1/menu?available_only=false")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return all 3 items
        assert len(data) == 3
        assert any(item["name"] == "Samosa" for item in data)

    def test_list_menu_items_filter_by_category(self, client, sample_menu_items, sample_categories):
        """Test filtering menu items by category."""
        south_indian_id = sample_categories[0].id
        response = client.get(f"/api/v1/menu?category_id={south_indian_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 1
        assert data[0]["name"] == "Masala Dosa"
        assert data[0]["category"]["id"] == south_indian_id

    def test_list_menu_items_filter_available_and_category(self, client, sample_menu_items, sample_categories):
        """Test filtering by both available_only and category."""
        snacks_id = sample_categories[3].id
        response = client.get(f"/api/v1/menu?available_only=true&category_id={snacks_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Samosa is in Snacks but not available
        assert len(data) == 0

    def test_list_menu_items_response_structure(self, client, sample_menu_items):
        """Test that menu item response has correct structure."""
        response = client.get("/api/v1/menu")
        data = response.json()

        first_item = data[0]
        required_fields = ["id", "name", "price", "category_id", "is_available", "created_at", "updated_at", "category"]
        for field in required_fields:
            assert field in first_item

        # Verify data types
        assert isinstance(first_item["id"], int)
        assert isinstance(first_item["name"], str)
        assert isinstance(first_item["price"], int)
        assert isinstance(first_item["is_available"], bool)
        assert isinstance(first_item["category"], dict)

    def test_list_menu_items_includes_category_details(self, client, sample_menu_items):
        """Test that menu items include full category details."""
        response = client.get("/api/v1/menu")
        data = response.json()

        first_item = data[0]
        assert "category" in first_item
        assert "id" in first_item["category"]
        assert "name" in first_item["category"]


class TestGetMenuItem:
    """Tests for GET /api/v1/menu/{item_id} endpoint."""

    def test_get_menu_item_success(self, client, sample_menu_items):
        """Test getting a single menu item by ID."""
        item_id = sample_menu_items[0].id
        response = client.get(f"/api/v1/menu/{item_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == item_id
        assert data["name"] == "Masala Dosa"
        assert data["price"] == 8000
        assert "category" in data

    def test_get_menu_item_not_found(self, client):
        """Test getting a non-existent menu item."""
        response = client.get("/api/v1/menu/9999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_get_menu_item_invalid_id(self, client):
        """Test getting a menu item with invalid ID format."""
        response = client.get("/api/v1/menu/invalid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCreateMenuItem:
    """Tests for POST /api/v1/menu endpoint."""

    def test_create_menu_item_success(self, client, auth_headers, sample_categories):
        """Test creating a new menu item with authentication."""
        item_data = {
            "name": "Idli",
            "description": "Steamed rice cakes",
            "price": 5000,
            "category_id": sample_categories[0].id,
        }

        response = client.post(
            "/api/v1/menu",
            json=item_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["name"] == "Idli"
        assert data["description"] == "Steamed rice cakes"
        assert data["price"] == 5000
        assert data["category_id"] == sample_categories[0].id
        assert data["is_available"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_menu_item_minimal_data(self, client, auth_headers, sample_categories):
        """Test creating a menu item with only required fields."""
        item_data = {
            "name": "Simple Item",
            "price": 1000,
            "category_id": sample_categories[0].id,
        }

        response = client.post(
            "/api/v1/menu",
            json=item_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["name"] == "Simple Item"
        assert data["description"] is None
        assert data["price"] == 1000

    def test_create_menu_item_without_auth(self, client, sample_categories):
        """Test creating a menu item without authentication fails."""
        item_data = {
            "name": "Unauthorized Item",
            "price": 5000,
            "category_id": sample_categories[0].id,
        }

        response = client.post("/api/v1/menu", json=item_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_menu_item_missing_required_fields(self, client, auth_headers):
        """Test creating a menu item without required fields fails."""
        # Missing name
        response = client.post(
            "/api/v1/menu",
            json={"price": 5000, "category_id": 1},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing price
        response = client.post(
            "/api/v1/menu",
            json={"name": "Test", "category_id": 1},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing category_id
        response = client.post(
            "/api/v1/menu",
            json={"name": "Test", "price": 5000},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_menu_item_invalid_price(self, client, auth_headers, sample_categories):
        """Test creating a menu item with invalid price."""
        # Negative price
        response = client.post(
            "/api/v1/menu",
            json={"name": "Test", "price": -100, "category_id": sample_categories[0].id},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Zero price
        response = client.post(
            "/api/v1/menu",
            json={"name": "Test", "price": 0, "category_id": sample_categories[0].id},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_menu_item_invalid_category(self, client, auth_headers):
        """Test creating a menu item with non-existent category."""
        item_data = {
            "name": "Test Item",
            "price": 5000,
            "category_id": 9999,
        }

        response = client.post(
            "/api/v1/menu",
            json=item_data,
            headers=auth_headers,
        )

        # Should fail due to foreign key constraint
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestUpdateMenuItem:
    """Tests for PATCH /api/v1/menu/{item_id} endpoint."""

    def test_update_menu_item_name(self, client, auth_headers, sample_menu_items):
        """Test updating menu item name."""
        item_id = sample_menu_items[0].id
        update_data = {"name": "Special Masala Dosa"}

        response = client.patch(
            f"/api/v1/menu/{item_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["name"] == "Special Masala Dosa"
        assert data["price"] == sample_menu_items[0].price  # Unchanged

    def test_update_menu_item_price(self, client, auth_headers, sample_menu_items):
        """Test updating menu item price."""
        item_id = sample_menu_items[0].id
        update_data = {"price": 9000}

        response = client.patch(
            f"/api/v1/menu/{item_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["price"] == 9000

    def test_update_menu_item_availability(self, client, auth_headers, sample_menu_items):
        """Test updating menu item availability."""
        item_id = sample_menu_items[0].id
        update_data = {"is_available": False}

        response = client.patch(
            f"/api/v1/menu/{item_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["is_available"] is False

    def test_update_menu_item_multiple_fields(self, client, auth_headers, sample_menu_items):
        """Test updating multiple fields at once."""
        item_id = sample_menu_items[0].id
        update_data = {
            "name": "Updated Dosa",
            "description": "New description",
            "price": 8500,
            "is_available": False,
        }

        response = client.patch(
            f"/api/v1/menu/{item_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["name"] == "Updated Dosa"
        assert data["description"] == "New description"
        assert data["price"] == 8500
        assert data["is_available"] is False

    def test_update_menu_item_without_auth(self, client, sample_menu_items):
        """Test updating a menu item without authentication fails."""
        item_id = sample_menu_items[0].id
        update_data = {"name": "Test"}

        response = client.patch(f"/api/v1/menu/{item_id}", json=update_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_menu_item_not_found(self, client, auth_headers):
        """Test updating a non-existent menu item."""
        update_data = {"name": "Test"}

        response = client.patch(
            "/api/v1/menu/9999",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_menu_item_empty_update(self, client, auth_headers, sample_menu_items):
        """Test updating with no fields still succeeds."""
        item_id = sample_menu_items[0].id
        update_data = {}

        response = client.patch(
            f"/api/v1/menu/{item_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK


class TestDeleteMenuItem:
    """Tests for DELETE /api/v1/menu/{item_id} endpoint."""

    def test_delete_menu_item_success(self, client, auth_headers, sample_menu_items):
        """Test soft deleting a menu item."""
        item_id = sample_menu_items[0].id

        response = client.delete(
            f"/api/v1/menu/{item_id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify item is soft deleted (not available)
        get_response = client.get(f"/api/v1/menu/{item_id}")
        assert get_response.status_code == status.HTTP_200_OK
        data = get_response.json()
        assert data["is_available"] is False

    def test_delete_menu_item_not_in_available_list(self, client, auth_headers, sample_menu_items):
        """Test that deleted items don't appear in available-only list."""
        item_id = sample_menu_items[0].id

        # Delete the item
        client.delete(f"/api/v1/menu/{item_id}", headers=auth_headers)

        # Get available items
        list_response = client.get("/api/v1/menu?available_only=true")
        items = list_response.json()

        # Deleted item should not be in the list
        assert not any(item["id"] == item_id for item in items)

    def test_delete_menu_item_in_all_list(self, client, auth_headers, sample_menu_items):
        """Test that deleted items appear in all items list."""
        item_id = sample_menu_items[0].id

        # Delete the item
        client.delete(f"/api/v1/menu/{item_id}", headers=auth_headers)

        # Get all items
        list_response = client.get("/api/v1/menu?available_only=false")
        items = list_response.json()

        # Deleted item should still be in the list
        deleted_item = next((item for item in items if item["id"] == item_id), None)
        assert deleted_item is not None
        assert deleted_item["is_available"] is False

    def test_delete_menu_item_without_auth(self, client, sample_menu_items):
        """Test deleting a menu item without authentication fails."""
        item_id = sample_menu_items[0].id

        response = client.delete(f"/api/v1/menu/{item_id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_menu_item_not_found(self, client, auth_headers):
        """Test deleting a non-existent menu item."""
        response = client.delete("/api/v1/menu/9999", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_menu_item_twice(self, client, auth_headers, sample_menu_items):
        """Test deleting an already deleted menu item."""
        item_id = sample_menu_items[0].id

        # Delete once
        response1 = client.delete(f"/api/v1/menu/{item_id}", headers=auth_headers)
        assert response1.status_code == status.HTTP_204_NO_CONTENT

        # Delete again
        response2 = client.delete(f"/api/v1/menu/{item_id}", headers=auth_headers)
        # Should still succeed (idempotent)
        assert response2.status_code == status.HTTP_204_NO_CONTENT


class TestMenuIntegration:
    """Integration tests for menu item endpoints."""

    def test_create_update_delete_flow(self, client, auth_headers, sample_categories):
        """Test complete CRUD flow for menu items."""
        # Create
        create_data = {
            "name": "Test Dosa",
            "price": 7000,
            "category_id": sample_categories[0].id,
        }
        create_response = client.post(
            "/api/v1/menu",
            json=create_data,
            headers=auth_headers,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        created_item = create_response.json()

        # Update
        update_data = {"name": "Updated Dosa", "price": 7500}
        update_response = client.patch(
            f"/api/v1/menu/{created_item['id']}",
            json=update_data,
            headers=auth_headers,
        )
        assert update_response.status_code == status.HTTP_200_OK
        updated_item = update_response.json()
        assert updated_item["name"] == "Updated Dosa"
        assert updated_item["price"] == 7500

        # Delete
        delete_response = client.delete(
            f"/api/v1/menu/{created_item['id']}",
            headers=auth_headers,
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deleted
        get_response = client.get(f"/api/v1/menu/{created_item['id']}")
        assert get_response.json()["is_available"] is False

    def test_menu_items_persist_across_requests(self, client, auth_headers, sample_categories):
        """Test that menu items persist across multiple requests."""
        # Create item
        create_data = {
            "name": "Persistent Item",
            "price": 5000,
            "category_id": sample_categories[0].id,
        }
        create_response = client.post(
            "/api/v1/menu",
            json=create_data,
            headers=auth_headers,
        )
        item_id = create_response.json()["id"]

        # Make multiple get requests
        for _ in range(3):
            response = client.get(f"/api/v1/menu/{item_id}")
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["name"] == "Persistent Item"
