"""
Authentication and authorization for Lily Cafe POS System.
Handles JWT token generation, password hashing, and admin authentication.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app import schemas

# Password hashing context (using bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token security
security = HTTPBearer()

# JWT Configuration
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password: The password to verify
        hashed_password: The hashed password to compare against

    Returns:
        True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password.

    Args:
        password: The password to hash

    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.TOKEN_EXPIRY_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> schemas.TokenData:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token string

    Returns:
        TokenData object with decoded information

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception


def authenticate_admin(username: str, password: str) -> bool:
    """
    Authenticate admin user.

    Args:
        username: Admin username
        password: Admin password (plain text)

    Returns:
        True if authentication successful, False otherwise
    """
    # For v0.1, we use simple environment-based credentials
    # In future versions, this would check against a database
    if username != settings.ADMIN_USERNAME:
        return False

    # For v0.1, compare plain password (in production, use hashed passwords)
    return password == settings.ADMIN_PASSWORD


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    FastAPI dependency to get current authenticated user from JWT token.

    Usage:
        @app.get("/admin/dashboard")
        def get_dashboard(current_user: str = Depends(get_current_user)):
            return {"message": f"Welcome {current_user}"}

    Args:
        credentials: HTTP Bearer credentials from request header

    Returns:
        Username of authenticated user

    Raises:
        HTTPException: If token is invalid or missing
    """
    token = credentials.credentials
    token_data = verify_token(token)
    return token_data.username
