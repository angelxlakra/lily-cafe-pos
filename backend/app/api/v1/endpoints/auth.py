"""
Authentication endpoints for Lily Cafe POS System.
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends

from app import schemas
from app.core import security
from app.core.config import settings
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/login", response_model=schemas.Token)
def login(login_data: schemas.LoginRequest):
    """
    User login endpoint.
    Returns JWT token with role on successful authentication.
    """
    user_role = security.authenticate_user(login_data.username, login_data.password)

    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token with role included
    access_token = security.create_access_token(
        data={"sub": login_data.username, "role": user_role.value},
        expires_delta=timedelta(hours=settings.TOKEN_EXPIRY_HOURS),
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verify")
def verify_token(current_user: schemas.TokenData = Depends(get_current_user)):
    """Verify JWT token and return current user with role."""
    return {
        "username": current_user.username,
        "role": current_user.role.value,
        "authenticated": True
    }
