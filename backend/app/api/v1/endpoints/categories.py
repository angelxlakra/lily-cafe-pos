"""
Category endpoints for Lily Cafe POS System.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app import schemas, crud
from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("", response_model=List[schemas.Category])
def list_categories(db: Session = Depends(get_db)):
    """Get all categories."""
    return crud.get_categories(db)


@router.post(
    "",
    response_model=schemas.Category,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Create a new category (admin only)."""
    try:
        return crud.create_category(db, category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Category with this name already exists",
        )
