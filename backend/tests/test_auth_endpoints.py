"""
Integration tests for authentication API endpoints.
Tests login, token verification, and protected endpoints.
"""

import pytest
from fastapi import status


class TestLoginEndpoint:
    """Test /api/v1/auth/login endpoint."""

    def test_login_success(self, client, admin_credentials):
        """Test successful login with correct credentials."""
        response = client.post("/api/v1/auth/login", json=admin_credentials)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client):
        """Test login with incorrect password."""
        response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data
        assert "username or password" in data["detail"].lower()

    def test_login_wrong_username(self, client):
        """Test login with incorrect username."""
        response = client.post(
            "/api/v1/auth/login", json={"username": "wronguser", "password": "changeme123"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data

    def test_login_missing_username(self, client):
        """Test login with missing username."""
        response = client.post("/api/v1/auth/login", json={"password": "changeme123"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_missing_password(self, client):
        """Test login with missing password."""
        response = client.post("/api/v1/auth/login", json={"username": "admin"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_empty_credentials(self, client):
        """Test login with empty credentials."""
        response = client.post("/api/v1/auth/login", json={"username": "", "password": ""})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_invalid_json(self, client):
        """Test login with invalid JSON."""
        response = client.post(
            "/api/v1/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestVerifyTokenEndpoint:
    """Test /api/v1/auth/verify endpoint."""

    def test_verify_token_success(self, client, auth_token):
        """Test token verification with valid token."""
        response = client.get(
            "/api/v1/auth/verify", headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "username" in data
        assert "authenticated" in data
        assert data["username"] == "admin"
        assert data["authenticated"] is True

    def test_verify_token_missing_token(self, client):
        """Test token verification without token."""
        response = client.get("/api/v1/auth/verify")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_invalid_token(self, client):
        """Test token verification with invalid token."""
        response = client.get(
            "/api/v1/auth/verify", headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_malformed_header(self, client):
        """Test token verification with malformed authorization header."""
        response = client.get("/api/v1/auth/verify", headers={"Authorization": "InvalidFormat"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_empty_bearer(self, client):
        """Test token verification with empty bearer token."""
        response = client.get("/api/v1/auth/verify", headers={"Authorization": "Bearer "})

        # Empty bearer can result in 401 (invalid token) or 403 (forbidden)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestProtectedEndpoints:
    """Test that protected endpoints require authentication."""

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        # Try to access a protected endpoint (menu management requires auth)
        response = client.post(
            "/api/v1/menu",
            json={
                "name": "Test Item",
                "price": 5000,
                "category_id": 1,
            },
        )

        # Should require authentication
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_protected_endpoint_with_valid_token(self, client, auth_headers, sample_category):
        """Test accessing protected endpoint with valid token."""
        response = client.post(
            "/api/v1/menu",
            json={
                "name": "Test Item",
                "price": 5000,
                "category_id": sample_category.id,
            },
            headers=auth_headers,
        )

        # Should succeed with valid token
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
        ]

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.post(
            "/api/v1/menu",
            json={
                "name": "Test Item",
                "price": 5000,
                "category_id": 1,
            },
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        # Should reject invalid token
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenLifecycle:
    """Test complete token lifecycle."""

    def test_login_use_token_verify(self, client, admin_credentials):
        """Test complete workflow: login -> use token -> verify token."""
        # Step 1: Login
        login_response = client.post("/api/v1/auth/login", json=admin_credentials)
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        # Step 2: Use token to access protected endpoint
        verify_response = client.get(
            "/api/v1/auth/verify", headers={"Authorization": f"Bearer {token}"}
        )
        assert verify_response.status_code == status.HTTP_200_OK
        assert verify_response.json()["authenticated"] is True

        # Step 3: Use same token again (should still work)
        verify_response_2 = client.get(
            "/api/v1/auth/verify", headers={"Authorization": f"Bearer {token}"}
        )
        assert verify_response_2.status_code == status.HTTP_200_OK

    def test_multiple_logins_generate_different_tokens(self, client, admin_credentials):
        """Test that multiple logins generate different tokens."""
        import time

        # First login
        response1 = client.post("/api/v1/auth/login", json=admin_credentials)
        token1 = response1.json()["access_token"]

        # Wait a moment to ensure different timestamp
        time.sleep(1)

        # Second login
        response2 = client.post("/api/v1/auth/login", json=admin_credentials)
        token2 = response2.json()["access_token"]

        # Tokens should be different (different exp times)
        assert token1 != token2

        # But both should be valid
        verify1 = client.get("/api/v1/auth/verify", headers={"Authorization": f"Bearer {token1}"})
        verify2 = client.get("/api/v1/auth/verify", headers={"Authorization": f"Bearer {token2}"})

        assert verify1.status_code == status.HTTP_200_OK
        assert verify2.status_code == status.HTTP_200_OK
