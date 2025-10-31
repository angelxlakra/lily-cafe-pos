"""
Unit tests for authentication and security functions.
Tests password hashing, JWT token creation/validation, and authentication.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException

from app.core import security
from app.core.config import settings
from app import schemas


class TestPasswordHashing:
    """Test password hashing functionality.

    Note: Direct bcrypt hashing tests are skipped due to compatibility
    issues between passlib and bcrypt libraries. Password hashing is
    thoroughly tested in integration tests (test_auth_endpoints.py).
    """

    def test_authentication_with_env_password(self):
        """Test that the configured admin password works with authentication."""
        # This tests the actual authentication flow using plain text comparison
        # (v0.1 uses plain text passwords, bcrypt is ready for future versions)
        result = security.authenticate_admin(
            settings.ADMIN_USERNAME,
            settings.ADMIN_PASSWORD
        )
        assert result is True

        # Wrong password should fail
        result = security.authenticate_admin(
            settings.ADMIN_USERNAME,
            "wrongpassword"
        )
        assert result is False


class TestJWTToken:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "testuser"}
        token = security.create_access_token(data)

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

        # Token should be decodable
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert "exp" in decoded

    def test_create_access_token_with_custom_expiry(self):
        """Test JWT token creation with custom expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = security.create_access_token(data, expires_delta=expires_delta)

        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.now()

        # Expiry should be approximately 30 minutes from now
        time_diff = (exp_time - now).total_seconds()
        assert 1700 < time_diff < 1900  # ~30 minutes (with some tolerance)

    def test_create_access_token_default_expiry(self):
        """Test JWT token creation with default expiration."""
        data = {"sub": "testuser"}
        token = security.create_access_token(data)

        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.now()

        # Should use default TOKEN_EXPIRY_HOURS (24 hours)
        time_diff = (exp_time - now).total_seconds()
        expected_seconds = settings.TOKEN_EXPIRY_HOURS * 3600
        assert expected_seconds - 100 < time_diff < expected_seconds + 100

    def test_verify_token_success(self):
        """Test successful token verification."""
        data = {"sub": "admin"}
        token = security.create_access_token(data)

        token_data = security.verify_token(token)

        assert isinstance(token_data, schemas.TokenData)
        assert token_data.username == "admin"

    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            security.verify_token(invalid_token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    def test_verify_token_expired(self):
        """Test token verification with expired token."""
        data = {"sub": "testuser"}
        # Create token that expired 1 hour ago
        expires_delta = timedelta(hours=-1)
        token = security.create_access_token(data, expires_delta=expires_delta)

        with pytest.raises(HTTPException) as exc_info:
            security.verify_token(token)

        assert exc_info.value.status_code == 401

    def test_verify_token_missing_subject(self):
        """Test token verification with missing subject."""
        # Create token without 'sub' claim
        data = {"user": "testuser"}  # Wrong key
        to_encode = data.copy()
        expire = datetime.now() + timedelta(hours=1)
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=security.ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            security.verify_token(token)

        assert exc_info.value.status_code == 401


class TestAuthentication:
    """Test admin authentication."""

    def test_authenticate_admin_success(self):
        """Test successful admin authentication."""
        result = security.authenticate_admin(
            settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD
        )
        assert result is True

    def test_authenticate_admin_wrong_username(self):
        """Test admin authentication with wrong username."""
        result = security.authenticate_admin("wronguser", settings.ADMIN_PASSWORD)
        assert result is False

    def test_authenticate_admin_wrong_password(self):
        """Test admin authentication with wrong password."""
        result = security.authenticate_admin(settings.ADMIN_USERNAME, "wrongpassword")
        assert result is False

    def test_authenticate_admin_empty_credentials(self):
        """Test admin authentication with empty credentials."""
        result = security.authenticate_admin("", "")
        assert result is False
