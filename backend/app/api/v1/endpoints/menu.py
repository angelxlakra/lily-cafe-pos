"""
Menu item endpoints for Lily Cafe POS System.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi.exceptions import ResponseValidationError

from app import schemas, crud
from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("", response_model=List[schemas.MenuItem])
def list_menu_items(
    available_only: bool = True,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Get all menu items.

    Query parameters:
    - available_only: Filter only available items (default: true)
    - category_id: Filter by category ID (optional)
    """
    return crud.get_menu_items(db, available_only=available_only, category_id=category_id)


@router.get("/{item_id}", response_model=schemas.MenuItem)
def get_menu_item(item_id: int, db: Session = Depends(get_db)):
    """Get a single menu item by ID."""
    item = crud.get_menu_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item


@router.post(
    "",
    response_model=schemas.MenuItem,
    status_code=status.HTTP_201_CREATED,
)
def create_menu_item(
    item: schemas.MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Create a new menu item (admin only)."""
    try:
        return crud.create_menu_item(db, item)
    except (IntegrityError, ResponseValidationError):
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid menu item data or category does not exist",
        )


@router.patch("/{item_id}", response_model=schemas.MenuItem)
def update_menu_item(
    item_id: int,
    item: schemas.MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Update a menu item (admin only)."""
    updated_item = crud.update_menu_item(db, item_id, item)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return updated_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Soft delete a menu item (admin only)."""
    if not crud.delete_menu_item(db, item_id):
        raise HTTPException(status_code=404, detail="Menu item not found")
    return None
