"""
Inventory Categories API Endpoints.
CRUD operations for inventory category management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.api import deps
from app import schemas, crud

router = APIRouter()


@router.get("", response_model=List[schemas.InventoryCategory])
def list_inventory_categories(
    db: Session = Depends(deps.get_db)
):
    """
    Get all inventory categories.

    Returns categories ordered alphabetically by name.
    No authentication required - categories are public data.
    """
    return crud.get_inventory_categories(db)


@router.get("/{category_id}", response_model=schemas.InventoryCategory)
def get_inventory_category(
    category_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get a single inventory category by ID.

    Args:
        category_id: The ID of the category to retrieve

    Returns:
        The inventory category details

    Raises:
        404: Category not found
    """
    category = crud.get_inventory_category(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory category not found"
        )
    return category


@router.post(
    "",
    response_model=schemas.InventoryCategory,
    status_code=status.HTTP_201_CREATED
)
def create_inventory_category(
    category: schemas.InventoryCategoryCreate,
    db: Session = Depends(deps.get_db),
    current_user: str = Depends(deps.get_current_user)
):
    """
    Create a new inventory category (admin only).

    Args:
        category: Category data (name, description)

    Returns:
        The created inventory category

    Raises:
        400: Category with this name already exists
        401: Unauthorized (not logged in as admin)
    """
    try:
        return crud.create_inventory_category(db, category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category.name}' already exists"
        )


@router.patch("/{category_id}", response_model=schemas.InventoryCategory)
def update_inventory_category(
    category_id: int,
    category: schemas.InventoryCategoryUpdate,
    db: Session = Depends(deps.get_db),
    current_user: str = Depends(deps.get_current_user)
):
    """
    Update an inventory category (admin only).

    Args:
        category_id: The ID of the category to update
        category: Updated category data (all fields optional)

    Returns:
        The updated inventory category

    Raises:
        400: New name already exists
        404: Category not found
        401: Unauthorized (not logged in as admin)
    """
    try:
        updated = crud.update_inventory_category(db, category_id, category)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory category not found"
            )
        return updated
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category.name}' already exists"
        )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_category(
    category_id: int,
    db: Session = Depends(deps.get_db),
    current_user: str = Depends(deps.get_current_user)
):
    """
    Delete an inventory category (admin only).

    Args:
        category_id: The ID of the category to delete

    Returns:
        No content (204)

    Raises:
        404: Category not found
        401: Unauthorized (not logged in as admin)

    Note:
        In future versions, this will check if category has associated
        inventory items and prevent deletion if items exist.
    """
    success = crud.delete_inventory_category(db, category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory category not found"
        )
