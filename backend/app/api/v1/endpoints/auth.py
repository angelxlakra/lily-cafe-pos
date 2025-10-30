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
    Admin login endpoint.
    Returns JWT token on successful authentication.
    """
    if not security.authenticate_admin(login_data.username, login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(
        data={"sub": login_data.username},
        expires_delta=timedelta(hours=settings.TOKEN_EXPIRY_HOURS),
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verify")
def verify_token(current_user: str = Depends(get_current_user)):
    """Verify JWT token and return current user."""
    return {"username": current_user, "authenticated": True}
