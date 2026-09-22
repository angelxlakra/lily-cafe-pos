from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.models.costing_models import (DishCosting, DishCostingIngredient)
from app.models.models import MenuItem
from app.models.inventory_models import InventoryItem

def get_costings(db: Session) -> List[DishCosting]:
    """Get all dish costings."""
    return (db.query(DishCosting).order_by(DishCosting.id.desc()).all())
    
def get_costing(db: Session, costing_id: int) -> Optional[DishCosting]:
    """
    Fetch one costing by its ID with all related data.
    """
    stmt = (select(DishCosting).options(selectinload(DishCosting.menu_item), selectinload(DishCosting.ingredients).selectinload(DishCostingIngredient.inventory_item)).where(DishCosting.id == costing_id))
    return db.scalar(stmt)

# def get_costing(
#     db: Session,
#     costing_id: int,
# ) -> Optional[DishCosting]:
#     """Get a single dish costing by ID."""
#     return (
#         db.query(DishCosting)
#         .filter(DishCosting.id == costing_id)
#         .first()
#     )
def get_costing_by_menu_item(db: Session, menu_item_id: int) -> Optional[DishCosting]:
    """
    Fetch the costing belonging to one menu item.
    """
    stmt = (select(DishCosting).options(selectinload(DishCosting.menu_item), selectinload(DishCosting.ingredients).selectinload(DishCostingIngredient.inventory_item)).where(DishCosting.menu_item_id == menu_item_id))
    return db.scalar(stmt)

def list_costings(db: Session,)-> list[DishCosting]:
    """
    Fetch all dish costings with their related ingredients.
    """
    stmt = (select(DishCosting).options(selectinload(DishCosting.menu_item), selectinload(DishCosting.ingredients).selectinload(DishCostingIngredient.inventory_item)).order_by(DishCosting.id.desc()))
    return list(db.scalars(stmt).unique().all())

def get_menu_item(db: Session, menu_item_id: int)-> Optional[MenuItem]:
    """
    Fetch a menu item by ID.
    """
    stmt = select(MenuItem).where(MenuItem.id==menu_item_id)
    return db.scalar(stmt)

def get_inventory_item(
    db: Session,
    inventory_item_id: int,
) -> Optional[InventoryItem]:
    """
    Fetch an inventory item by ID.
    """

    stmt = select(InventoryItem).where(
        InventoryItem.id == inventory_item_id
    )

    return db.scalar(stmt)


def create_costing(
    db: Session,
    costing_data: DishCosting,
    ingredients: list[DishCostingIngredient],
) -> DishCosting:
    """
    Create a costing and its ingredient rows.
    """

    costing_data.ingredients = ingredients

    db.add(costing_data)
    db.commit()
    db.refresh(costing_data)

    return costing_data


def update_costing(
    db: Session,
    costing: DishCosting,
    costing_data: dict,
    ingredients: list[DishCostingIngredient],
) -> DishCosting:
    """
    Update a costing and replace its ingredient rows.
    """

    for field, value in costing_data.items():
        setattr(costing, field, value)

    # Because the relationship has delete-orphan configured,
    # replacing this collection removes the old ingredient rows.
    costing.ingredients = ingredients

    db.add(costing)
    db.commit()
    db.refresh(costing)

    return costing


def delete_costing(
    db: Session,
    costing: DishCosting,
) -> None:
    """
    Delete a costing.
    """

    db.delete(costing)
    db.commit()

######

# from typing import List, Optional

# from sqlalchemy.orm import Session

# from app.models import models
# from app.models.costing_models import (
#     DishCosting,
#     DishCostingIngredient,
# )
# from app.models.inventory_models import InventoryItem


# def get_costings(db: Session) -> List[DishCosting]:
#     """Get all dish costings."""
#     return (
#         db.query(DishCosting)
#         .order_by(DishCosting.id.desc())
#         .all()
#     )


# def get_costing(
#     db: Session,
#     costing_id: int,
# ) -> Optional[DishCosting]:
#     """Get a single dish costing by ID."""
#     return (
#         db.query(DishCosting)
#         .filter(DishCosting.id == costing_id)
#         .first()
#     )


# def get_costing_by_menu_item(
#     db: Session,
#     menu_item_id: int,
# ) -> Optional[DishCosting]:
#     """Get the costing for a specific menu item."""
#     return (
#         db.query(DishCosting)
#         .filter(DishCosting.menu_item_id == menu_item_id)
#         .first()
#     )


# def get_menu_item(
#     db: Session,
#     menu_item_id: int,
# ) -> Optional[models.MenuItem]:
#     """Get a menu item by ID."""
#     return (
#         db.query(models.MenuItem)
#         .filter(models.MenuItem.id == menu_item_id)
#         .first()
#     )


# def get_inventory_item(
#     db: Session,
#     inventory_item_id: int,
# ) -> Optional[InventoryItem]:
#     """Get an inventory item by ID."""
#     return (
#         db.query(InventoryItem)
#         .filter(InventoryItem.id == inventory_item_id)
#         .first()
#     )


# def create_costing(
#     db: Session,
#     costing: DishCosting,
#     ingredients: List[DishCostingIngredient],
# ) -> DishCosting:
#     """
#     Create a dish costing with its ingredient rows.
#     """

#     costing.ingredients = ingredients

#     db.add(costing)
#     db.commit()
#     db.refresh(costing)

#     return costing


# def update_costing(
#     db: Session,
#     costing: DishCosting,
#     update_data: dict,
#     ingredients: List[DishCostingIngredient],
# ) -> DishCosting:
#     """
#     Update costing fields and replace ingredient rows.
#     """

#     for field, value in update_data.items():
#         setattr(costing, field, value)

#     # Existing ingredient rows are deleted because the relationship
#     # uses cascade="all, delete-orphan".
#     costing.ingredients = ingredients

#     db.commit()
#     db.refresh(costing)

#     return costing


# def delete_costing(
#     db: Session,
#     costing: DishCosting,
# ) -> bool:
#     """Delete a dish costing."""

#     db.delete(costing)
#     db.commit()

#     return True