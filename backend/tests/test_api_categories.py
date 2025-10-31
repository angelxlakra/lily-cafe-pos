"""
API endpoint tests for Category routes.
Tests /api/v1/categories endpoints.
"""

import pytest
from fastapi import status


class TestListCategories:
    """Tests for GET /api/v1/categories endpoint."""

    def test_list_categories_empty(self, client):
        """Test listing categories when database is empty."""
        response = client.get("/api/v1/categories")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    def test_list_categories_with_data(self, client, sample_categories):
        """Test listing all categories."""
        response = client.get("/api/v1/categories")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 5
        assert all("id" in category for category in data)
        assert all("name" in category for category in data)
        assert all("created_at" in category for category in data)

        # Verify category names
        category_names = [cat["name"] for cat in data]
        assert "South Indian" in category_names
        assert "Beverages" in category_names
        assert "Desserts" in category_names

    def test_list_categories_response_structure(self, client, sample_categories):
        """Test that category response has correct structure."""
        response = client.get("/api/v1/categories")
        data = response.json()

        first_category = data[0]
        assert isinstance(first_category["id"], int)
        assert isinstance(first_category["name"], str)
        assert isinstance(first_category["created_at"], str)
        assert len(first_category["name"]) > 0


class TestCreateCategory:
    """Tests for POST /api/v1/categories endpoint."""

    def test_create_category_success(self, client, auth_headers):
        """Test creating a new category with authentication."""
        category_data = {"name": "Italian"}

        response = client.post(
            "/api/v1/categories",
            json=category_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["name"] == "Italian"
        assert "id" in data
        assert "created_at" in data

    def test_create_category_without_auth(self, client):
        """Test creating a category without authentication fails."""
        category_data = {"name": "Italian"}

        response = client.post("/api/v1/categories", json=category_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_category_with_invalid_token(self, client):
        """Test creating a category with invalid token fails."""
        category_data = {"name": "Italian"}
        invalid_headers = {"Authorization": "Bearer invalid_token"}

        response = client.post(
            "/api/v1/categories",
            json=category_data,
            headers=invalid_headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_category_duplicate_name(self, client, auth_headers, sample_categories):
        """Test creating a category with duplicate name fails."""
        category_data = {"name": "South Indian"}

        response = client.post(
            "/api/v1/categories",
            json=category_data,
            headers=auth_headers,
        )

        # Should fail due to unique constraint
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_create_category_empty_name(self, client, auth_headers):
        """Test creating a category with empty name fails validation."""
        category_data = {"name": ""}

        response = client.post(
            "/api/v1/categories",
            json=category_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_category_missing_name(self, client, auth_headers):
        """Test creating a category without name fails validation."""
        category_data = {}

        response = client.post(
            "/api/v1/categories",
            json=category_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_category_too_long_name(self, client, auth_headers):
        """Test creating a category with name exceeding max length."""
        # Name longer than 100 characters
        category_data = {"name": "A" * 101}

        response = client.post(
            "/api/v1/categories",
            json=category_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_multiple_categories(self, client, auth_headers):
        """Test creating multiple categories in sequence."""
        categories = ["Italian", "Chinese", "Mexican"]

        for name in categories:
            response = client.post(
                "/api/v1/categories",
                json={"name": name},
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_201_CREATED

        # Verify all were created
        response = client.get("/api/v1/categories")
        data = response.json()
        category_names = [cat["name"] for cat in data]

        for name in categories:
            assert name in category_names


class TestCategoryIntegration:
    """Integration tests for category endpoints."""

    def test_create_and_list_category(self, client, auth_headers):
        """Test creating a category and then listing it."""
        # Create category
        create_response = client.post(
            "/api/v1/categories",
            json={"name": "Japanese"},
            headers=auth_headers,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        created_data = create_response.json()

        # List categories
        list_response = client.get("/api/v1/categories")
        assert list_response.status_code == status.HTTP_200_OK
        categories = list_response.json()

        # Verify created category is in the list
        assert any(cat["id"] == created_data["id"] for cat in categories)
        assert any(cat["name"] == "Japanese" for cat in categories)

    def test_category_persists_across_requests(self, client, auth_headers):
        """Test that created category persists across multiple requests."""
        # Create category
        client.post(
            "/api/v1/categories",
            json={"name": "Thai"},
            headers=auth_headers,
        )

        # Make multiple list requests
        for _ in range(3):
            response = client.get("/api/v1/categories")
            data = response.json()
            assert any(cat["name"] == "Thai" for cat in data)
