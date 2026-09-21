from decimal import Decimal
from os import name
from turtle import mode
from typing import List, override
from backend.app.api.v1.endpoints import inventory
from backend.tests.test_cash_inventory_access import inventory_item
from fastapi import APIRouter , Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_owner, get_current_user, get_optional_user
from app.db.session import get_db
from app.models.costing_models import DishCosting, DishCostingIngredient
from app.models.inventory_models import InventoryItem

from app.schemas import costing_schemas
from app.schemas import TokenData

from app.crud import costing_crud

from app.utils import costing as costing_utils
from app.utils.units import IncompatibleUnitError

router = APIRouter()

_READ = Depends(get_current_user)
_OWNER = Depends(get_current_owner)


# Supports
def _menu_price_rupees(menu_item) -> Decimal | None:
    # To convert calculation in rupee because MenuItem is stored in paise.
    if menu_item.price is None:
        return None
    return Decimal(menu_item.price) / Decimal("100")

def _build_ingredient_inputs(ingredients: list[DishCostingIngredient], price_overrides: dict[int, Decimal] | None = None) -> list[costing_utils.IngredientInput]:
    # Convert DB ingredient rows into the pure calculation input format.
    overrides = price_overrides or {}
    inputs = []

    for row in ingredients: 
        item = row.inventory_item

        if item is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Inventory item {row.inventory_item_id} not found.")
        
        price = overrides.get(item.id, item.cost_per_unit)
        inputs.append(costing_utils.IngredientInput(
            item_id=item.id, name=item.name, quantity=Decimal(row.quantity), unit=row.unit, stock_unit=item.unit, 
            cost_per_unit=(
                Decimal(price)
                if price is not None
                else None
                ),
                is_active=item.is_active
        ))
    return inputs

def _compute_breakdown(costing: DishCosting, menu_item, price_overrides: dict[int, Decimal] | None = None):
    # Calculate a costing breakdown for a persisted or temporary costing.
    ingredients = _build_ingredient_inputs(costing.ingredients, price_overrides=price_overrides)

    overheads = costing_utils.resolve_overheads(costing)
    target_margin = costing_utils.resolve_target_margin(costing)
    selling_price = _menu_price_rupees(menu_item)

    try:
        return costing_utils.compute(ingredients=ingredients, overheads=overheads, yield_units=costing.yield_units, selling_price=selling_price, target_margin_percent=target_margin)
    except IncompatibleUnitError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, details=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, details=str(e))

def _breakdown_to_schema(breakdown: costing_utils.CostBreakdown) -> costing_schemas.CostBreakdownOut:
    return costing_schemas.CostBreakdownOut(
        ingredients=[
            costing_schemas.IngredientLineOut(
                inventory_item_id=line.item_id, name=line.name, quantity=line.quantity, unit=line.unit, stock_unit=line.stock_unit, unit_price=line.unit_price, line_cost=line.line_cost, share_percent=line.share_percent, price_missing=line.price_missing, is_active=line.is_active
                ) for line in breakdown.ingredients],
        overheads=[costing_schemas.OverheadLineOut(
            kind=line.kind, mode=line.mode, value=line.value, amount=line.amount, percent=line.percent, inherited=line.inherited
        )for line in breakdown.overheads],
        raw_material_cost=breakdown.raw_material_cost,
        overhead_cost=breakdown.overhead_cost,
        total_cost=breakdown.total_cost,
        yield_units=breakdown.yield_units,
        raw_cost_per_unit=breakdown.raw_cost_per_unit,
        cost_per_unit=breakdown.cost_per_unit,
         selling_price=breakdown.selling_price,
        margin_amount=breakdown.margin_amount,
        margin_percent=breakdown.margin_percent,
        food_cost_percent=breakdown.food_cost_percent,
        target_margin_percent=breakdown.target_margin_percent,
        suggested_price=breakdown.suggested_price,
        is_complete=breakdown.is_complete,
        warnings=breakdown.warnings,
    )

def _costing_to_schema(costing: DishCosting) -> costing_schemas.DishCostingOut:
    # Build the complete costing response.

    if costing.menu_item in None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details="Costing has no associated menu item.")
    
    breakdown = _compute_breakdown(costing, costing.menu_item)

    return costing_schemas.DishCostingOut(
        id=costing.id,
        menu_item_id=costing.menu_item_id,
        menu_item_name=costing.menu_item.name,
        yield_units=costing.yield_units,
        target_margin_percent=costing.target_margin_percent,
        notes=costing.notes,
        packaging=costing_schemas.OverheadOverride(mode=costing.packaging_mode, value=costing.packaging_value),
        labour=costing_schemas.OverheadOverride(mode=costing.labour_mode, value=costing.labour_value),
        fixed=costing_schemas.OverheadOverride(mode=costing.fixed_mode, value=costing.fixed_value),
        wastage=costing_schemas.OverheadOverride(mode=costing.wastage_mode, value=costing.wastage_value),
        ingredients=[
            costing_schemas.CostingIngredientIn(
                inventory_item_id=row.inventory_item_id,
                quantity=row.quantity,
                unit=row.unit
            ) for row in costing.ingredients
        ],
        breakdown=_breakdown_to_schema(breakdown)
    )

def _apply_overhead(costing: DishCosting, kind: str, override: costing_schemas.OverheadOverride):
    # Apply one overhead override to the ORM model.

    setattr(costing, f"{kind}_mode", override.mode)
    setattr(costing, f"{kind}_value", override.value)

def _build_costing_model(data: costing_schemas.DishCostingIn, inventory_items: dict[int, InventoryItem]) -> tuple[DishCosting, list[DishCostingIngredient]]:
    # Build ORM costing + ingredient rows from validated API input.

    costing = DishCosting(menu_item_id=data.menu_item_id, yield_units=data.yield_units, target_margin_percent=data.target_margin_percent, notes=data.notes)

    for kind in ("packaging", "labour", "fixed", "wastage"):
        override = getattr(data, kind)
        _apply_overhead(costing, kind, override)

    ingredients = []

    for index, ingredient in enumerate(data.ingredients):
        item = inventory_items.get(ingredient.inventory_item_id)    
        if item in None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=(f"Inventory item {ingredient.inventory_item_id} not found."))
        
        ingredients.append(DishCostingIngredient(inventory_item_id=item.id, quantity=ingredient.quantity, unit=ingredient.unit, sort_order=index, inventory_item=item))
    
    return costing, ingredients


