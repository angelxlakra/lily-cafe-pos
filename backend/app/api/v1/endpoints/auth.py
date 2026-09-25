"""
Authentication endpoints for Lily Cafe POS System.
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, Request, status, Depends

from app import schemas
from app.core import security, settings_store
from app.core.login_throttle import LOCKED_OUT_MESSAGE, client_ip, login_throttle
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/login", response_model=schemas.Token)
def login(login_data: schemas.LoginRequest, request: Request):
    """
    User login endpoint.
    Returns JWT token with role on successful authentication.
    """
    source = client_ip(request)
    retry_after = login_throttle.retry_after(source)
    if retry_after:
        # Refused before checking the password, so a locked-out source learns
        # nothing about whether the username exists.
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=LOCKED_OUT_MESSAGE,
            headers={"Retry-After": str(retry_after)},
        )

    user_role = security.authenticate_user(login_data.username, login_data.password)

    if user_role is None:
        login_throttle.record_failure(source)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    login_throttle.record_success(source)

    # Create token with role included
    access_token = security.create_access_token(
        data={"sub": login_data.username, "role": user_role.value},
        expires_delta=timedelta(hours=settings_store.get_int("app.token_expiry_hours", 24)),
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
