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

# JWT token security (auto_error=False to manually handle auth errors with 401)
security = HTTPBearer(auto_error=False)

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
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        # bcrypt handles max 72 bytes and raises ValueError if exceeded
        return False


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
        TokenData object with decoded information (username and role)

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
        role_str: str = payload.get("role")

        if username is None or role_str is None:
            raise credentials_exception

        # Convert string to UserRole enum
        try:
            role = schemas.UserRole(role_str)
        except ValueError:
            raise credentials_exception

        return schemas.TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception


def authenticate_user(username: str, password: str) -> Optional[schemas.UserRole]:
    """
    Authenticate user and return their role.

    Args:
        username: Username
        password: Password (plain text)

    Returns:
        UserRole if authentication successful, None otherwise
    """
    # Check owner credentials
    if username == settings.OWNER_USERNAME:
        if password == settings.OWNER_PASSWORD:
            return schemas.UserRole.OWNER
        return None

    # Check admin credentials
    if username == settings.ADMIN_USERNAME:
        if password == settings.ADMIN_PASSWORD:
            return schemas.UserRole.ADMIN
        return None

    return None


# Keep authenticate_admin for backward compatibility (deprecated)
def authenticate_admin(username: str, password: str) -> bool:
    """
    Authenticate admin user (deprecated - use authenticate_user instead).

    Args:
        username: Admin username
        password: Admin password (plain text)

    Returns:
        True if authentication successful, False otherwise
    """
    role = authenticate_user(username, password)
    return role is not None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> schemas.TokenData:
    """
    FastAPI dependency to get current authenticated user with role from JWT token.

    Usage:
        @app.get("/admin/dashboard")
        def get_dashboard(current_user: schemas.TokenData = Depends(get_current_user)):
            return {"message": f"Welcome {current_user.username}, role: {current_user.role}"}

    Args:
        credentials: HTTP Bearer credentials from request header

    Returns:
        TokenData with username and role

    Raises:
        HTTPException: If token is invalid or missing
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    token_data = verify_token(token)
    return token_data


async def get_current_owner(
    current_user: schemas.TokenData = Depends(get_current_user),
) -> schemas.TokenData:
    """
    FastAPI dependency to require OWNER role.

    Usage:
        @app.get("/admin/analytics")
        def get_analytics(current_user: schemas.TokenData = Depends(get_current_owner)):
            return {"data": "sensitive analytics"}

    Args:
        current_user: Current authenticated user with role

    Returns:
        TokenData if user is owner

    Raises:
        HTTPException: If user is not owner (403 Forbidden)
    """
    if current_user.role != schemas.UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required",
        )
    return current_user
