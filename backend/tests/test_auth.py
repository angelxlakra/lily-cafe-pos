"""
Authentication tests for protected endpoints.
Tests JWT token generation and authentication requirements.
"""

import pytest
from fastapi import status


class TestAuthenticationEndpoint:
    """Tests for /api/v1/auth/login endpoint."""

    def test_login_success(self, client):
        """Test successful login with correct credentials."""
        login_data = {
            "username": "admin",
            "password": "changeme123",
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client):
        """Test login with incorrect password."""
        login_data = {
            "username": "admin",
            "password": "wrongpassword",
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_login_wrong_username(self, client):
        """Test login with non-existent username."""
        login_data = {
            "username": "wronguser",
            "password": "changeme123",
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        # Missing password
        response = client.post("/api/v1/auth/login", json={"username": "admin"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing username
        response = client.post("/api/v1/auth/login", json={"password": "changeme123"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing both
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_empty_credentials(self, client):
        """Test login with empty credentials."""
        login_data = {
            "username": "",
            "password": "",
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProtectedEndpoints:
    """Tests for authentication requirements on protected endpoints."""

    def test_create_menu_item_requires_auth(self, client, sample_categories):
        """Test that creating a menu item requires authentication."""
        item_data = {
            "name": "Test Item",
            "price": 5000,
            "category_id": sample_categories[0].id,
        }

        response = client.post("/api/v1/menu", json=item_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_menu_item_requires_auth(self, client, sample_menu_items):
        """Test that updating a menu item requires authentication."""
        item_id = sample_menu_items[0].id
        update_data = {"name": "Updated Name"}

        response = client.patch(f"/api/v1/menu/{item_id}", json=update_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_menu_item_requires_auth(self, client, sample_menu_items):
        """Test that deleting a menu item requires authentication."""
        item_id = sample_menu_items[0].id

        response = client.delete(f"/api/v1/menu/{item_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_category_requires_auth(self, client):
        """Test that creating a category requires authentication."""
        category_data = {"name": "Test Category"}

        response = client.post("/api/v1/categories", json=category_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthenticationToken:
    """Tests for JWT token usage."""

    def test_valid_token_grants_access(self, client, auth_headers, sample_categories):
        """Test that valid token allows access to protected endpoints."""
        item_data = {
            "name": "Authorized Item",
            "price": 5000,
            "category_id": sample_categories[0].id,
        }

        response = client.post(
            "/api/v1/menu",
            json=item_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_invalid_token_denies_access(self, client, sample_categories):
        """Test that invalid token denies access."""
        item_data = {
            "name": "Test Item",
            "price": 5000,
            "category_id": sample_categories[0].id,
        }

        invalid_headers = {"Authorization": "Bearer invalid_token_here"}

        response = client.post(
            "/api/v1/menu",
            json=item_data,
            headers=invalid_headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_malformed_token_denies_access(self, client, sample_categories):
        """Test that malformed token header denies access."""
        item_data = {
            "name": "Test Item",
            "price": 5000,
            "category_id": sample_categories[0].id,
        }

        # Missing "Bearer" prefix
        malformed_headers = {"Authorization": "invalid_format"}

        response = client.post(
            "/api/v1/menu",
            json=item_data,
            headers=malformed_headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_works_across_multiple_requests(self, client, auth_headers, sample_categories):
        """Test that token can be reused for multiple requests."""
        for i in range(3):
            item_data = {
                "name": f"Test Item {i}",
                "price": 5000 + (i * 1000),
                "category_id": sample_categories[0].id,
            }

            response = client.post(
                "/api/v1/menu",
                json=item_data,
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_201_CREATED


class TestPublicEndpoints:
    """Tests for endpoints that don't require authentication."""

    def test_list_menu_items_public(self, client, sample_menu_items):
        """Test that listing menu items doesn't require auth."""
        response = client.get("/api/v1/menu")
        assert response.status_code == status.HTTP_200_OK

    def test_get_menu_item_public(self, client, sample_menu_items):
        """Test that getting a single menu item doesn't require auth."""
        item_id = sample_menu_items[0].id
        response = client.get(f"/api/v1/menu/{item_id}")
        assert response.status_code == status.HTTP_200_OK

    def test_list_categories_public(self, client, sample_categories):
        """Test that listing categories doesn't require auth."""
        response = client.get("/api/v1/categories")
        assert response.status_code == status.HTTP_200_OK

    def test_health_check_public(self, client):
        """Test that health check endpoint is public."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_root_endpoint_public(self, client):
        """Test that root endpoint is public."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK


class TestAuthenticationIntegration:
    """Integration tests for authentication flow."""

    def test_login_and_use_token(self, client, sample_categories):
        """Test complete flow: login, get token, use token."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "changeme123"},
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        # Use token to create item
        headers = {"Authorization": f"Bearer {token}"}
        item_data = {
            "name": "Authenticated Item",
            "price": 5000,
            "category_id": sample_categories[0].id,
        }

        create_response = client.post(
            "/api/v1/menu",
            json=item_data,
            headers=headers,
        )

        assert create_response.status_code == status.HTTP_201_CREATED
        assert create_response.json()["name"] == "Authenticated Item"

    def test_unauthorized_then_authorized_request(self, client, sample_categories):
        """Test that unauthorized request fails, then authorized succeeds."""
        item_data = {
            "name": "Test Item",
            "price": 5000,
            "category_id": sample_categories[0].id,
        }

        # First request without auth - should fail
        response1 = client.post("/api/v1/menu", json=item_data)
        assert response1.status_code == status.HTTP_401_UNAUTHORIZED

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "changeme123"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Second request with auth - should succeed
        response2 = client.post("/api/v1/menu", json=item_data, headers=headers)
        assert response2.status_code == status.HTTP_201_CREATED
