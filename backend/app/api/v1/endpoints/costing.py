from decimal import Decimal
from typing import List
from backend.app.api.v1.endpoints import menu
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


# Routes

@router.get("", response_model=List[costing_schemas.DishCostingSummary])
def get_costings(db: Session = Depends(get_db), current_user: TokenData = _READ):
    # Get all dish costing.
    costings = costing_crud.get_costings(db)
    result = []
    for costing in costings:
        if costing.menu_item in None:
            continue
        breakdown = _compute_breakdown(costing, costing.menu_item)
        
        target = (breakdown.target_margin_percent if breakdown.target_margin_percent is not None else Decimal("0"))
        
        below_target = (breakdown.margin_percent is not None and breakdown.margin_percent < target)

        result.append(costing_schemas.DishCostingSummary(
            id=costing.id,
            menu_item_id=costing.menu_item_id,
            menu_item_name=costing.menu_item.name,
            cost_per_unit=breakdown.cost_per_unit,
            selling_price=breakdown.selling_price,
            margin_percent=breakdown.margin_percent,
            target_margin_percent=target,
            below_target=below_target,
            is_complete=breakdown.is_complete,
        ))
    
    return result

@router.get("/{costing_id}", response_model=costing_schemas.DishCostingOut)
def get_costing(costing_id: int, db: Session = Depends(get_db), current_user: TokenData = _READ):
    # Get single dish costing
    costing = costing_crud.get_costing(db, costing_id)

    if not costing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Costing not found.")
    
    return _costing_to_schema(costing)

@router.get("/menu/{menu_item_id}", response_model=costing_schemas.DishCostingOut)
def get_menu_item_costing(menu_item_id: int, db: Session = Depends(get_db), current_user: TokenData = _READ):
    # Get costing for a specific menu item.
    menu_item = costing_crud.get_menu_item(db, menu_item_id)

    if not menu_item: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found.")

    costing = costing_crud.get_costing_by_menu_item(db, menu_item_id)

    if not costing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No costing found for this menu item.")
    
    return _costing_to_schema(costing)

# PREVIW

@router.post("/preview", response_model=costing_schemas.CostBreakdownOut)
def preview_costing(data: costing_schemas.DishCostingIn, db: Session = Depends(get_db), current_user: TokenData = _READ):
    # Calculate costing without saving it.
    menu_item = costing_crud.get_menu_item(
        db,
        data.menu_item_id,
    )

    if not menu_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found",
        )

    inventory_ids = {
        ingredient.inventory_item_id
        for ingredient in data.ingredients
    }

    inventory_items = (
        db.query(InventoryItem)
        .filter(InventoryItem.id.in_(inventory_ids))
        .all()
        if inventory_ids
        else []
    )

    inventory_map = {
        item.id: item
        for item in inventory_items
    }

    costing, ingredient_rows = _build_costing_model(
        data,
        inventory_map,
    )

    costing.ingredients = ingredient_rows

    breakdown = _compute_breakdown(
        costing,
        menu_item,
    )

    return _breakdown_to_schema(breakdown)


# CREATE

@router.post("", resopnse_model=costing_schemas.DishCostingOut, status_code=status.HTTP_201_CREATED)
def create_costing(data: costing_schemas.DishCostingIn, db: Session = Depends(get_db), current_user: TokenData=_OWNER):
    # Create a dish costing.
    menu_item = costing_crud.get_menu_item(db, data.menu_item_id)
    if not menu_item:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    
    existing = costing_crud.get_costing_by_menu_item(db, data.menu_item_id)

    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A costing already exists for this menu item.")
    
    inventory_ids = {ingredient.inventory_item_id for ingredient in data.ingredients}

    inventory_items = (
        db.query(InventoryItem).filter(InventoryItem.id.in_(inventory_ids)).all()
        if inventory_ids
        else []
    )

    inventory_map = {item.id: item for item in inventory_items}

    costing, ingredient_rows = _build_costing_model(data, inventory_map)

    costing.ingredients = ingredient_rows

    # Validating the calculation before writing to DB
    _compute_breakdown(costing, menu_item)

    costing = costing_crud.create_costing(db, costing, ingredient_rows)

    return _costing_to_schema(costing)


# UPDATE

@router.patch("/{costing_id}", response_model=costing_schemas.DishCostingOut)
def update_costing(costing_id: int, data: costing_schemas.DishCostingIn, db: Session = Depends(get_db), current_user: TokenData = _OWNER):
    # Update a dish costing.

    costing = costing_crud.get_costing(db, costing_id)

    if not costing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Costing not found")
    
    if costing.menu_item_id != data.menu_item_id:
        existing = costing_crud.get_costing_by_menu_item(db, data.menu_item_id)

        if existing and existing.id != costing_id:
            raise HTTPException(sataus_code=status.HTTP_409_CONFLICT, detail="A costing already exists for this menu item.")
        
    menu_item = costing_crud.get_menu_item(db, data.menu_item_id)

    if not menu_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found",
        )
    
    inventory_ids = {ingredient.inventory_item_id for ingredient in data.ingredients}

    inventory_items = (
        db.query(InventoryItem).filter(InventoryItem.id.in_(inventory_ids)).all()
        if inventory_ids
        else []
    )

    inventory_map = {item.id: item for item in inventory_items}

    new_costing, ingredient_rows = _build_costing_model(data, inventory_map)

    # Keeping the existing costing ID.
    new_costing.id = costing.id

    _compute_breakdown(new_costing, menu_item)

    update_data = {
        "menu_item_id": data.menu_item_id,
        "yield_units": data.yield_units,
        "target_margin_percent": data.target_margin_percent,
        "notes": data.notes,
        "packaging_mode": data.packaging.mode,
        "packaging_value": data.packaging.value,
        "labour_mode": data.labour.mode,
        "labour_value": data.labour.value,
        "fixed_mode": data.fixed.mode,
        "fixed_value": data.fixed.value,
        "wastage_mode": data.wastage.mode,
        "wastage_value": data.wastage.value,
    }

    costing = costing_crud.update_costing(db, costing, update_data, ingredient_rows)
    return _costing_to_schema(costing)

# DELETE

@router.delete("/{costing_id}")
def delete_costing(costing_id: int, db: Session = Depends(get_db), current_user: TokenData = _OWNER):
    # Delete a dish costing.
    costing = costing_crud.get_costing(db, costing_id)
    if not costing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Costing not found.")
    
    costing_crud.delete_costing(db, costing)

    return { "message": "Costing deleted successfully"}


# APPLY SUGGESTED PRICE

@router.post("/{costing_id}/apply-price", response_model=costing_schemas.DishCostingOut)
def apply_suggested_price(costing_id: int, db: Session = Depends(get_db), current_user: TokenData = _OWNER):
    # Apply the calculated suggested selling price to the menu item.
    costing = costing_crud.get_costing(db, costing_id)

    if not costing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Costing not found")

    menu_item = costing.menu_item

    if menu_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")

    breakdown = _compute_breakdown(costing, menu_item)

    if breakdown.suggested_price is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No suggested price is available.")
    
    # MenuItem.price is stored in paise.
    menu_item.price = int(breakdown.suggested_price * Decimal("100"))

    db.commit()
    db.refresh(menu_item)

    return _costing_to_schema(costing)


# REPRICING

# Repricing supports
def _get_reprice_impacts(db: Session, price_overrides: dict[int, Decimal]):
    # Calculate the impact of changed inventory prices across all dishes.
    costings = costing_crud.get_costings(db)
    affected = []
    unaffected_count = 0

    for costing in costings:
        if costing.menu_item is None:
            continue

        uses_changed_item = any(row.inventory_item_id in price_overrides for row in costing.ingredients)

        if not uses_changed_item:
            unaffected_count += 1
            continue

        before = _compute_breakdown(costing, costing.menu_item)
        after = _compute_breakdown(costing, costing.menu_item, price_overrides=price_overrides)

        target = costing_utils.resolve_target_margin(costing)

        margin_before = before.margin_percent
        margin_after = after.margin_percent

        crosses_below_target = (margin_before is not None and margin_after is not None and margin_before >= target and margin_after < target)

        affected.append(costing_schemas.DishImpact(
            costing_id=costing.id, menu_item_name=costing.menu_item.name, cost_before=before.cost_per_unit, cost_after=after.cost_per_unit, margin_before=margin_before, margin_after=margin_after, crosses_below_target=crosses_below_target
        ))

    return affected, unaffected_count

@router.post("/reprice/preview", response_model=costing_schemas.RepricePreview)
def preview_reprice(data: costing_schemas.RepriceRequest, db: Session = Depends(get_db), current_user: TokenData = _OWNER):
    # Preview the effect of inventory price changes without saving them.
    if not data.prices:
        return costing_schemas.RepricePreview(affected_dishes=[], unaffected_count=0)
    
    item_ids = {price.inventory_item_id for price in data.prices}

    items = (db.query(InventoryItem).filter(InventoryItem.id.in_(item_ids)).all())

    item_map = {item.id: item for item in items}

    missing = item_ids - set(item_map.keys())

    if missing: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory items not found: {sorted(missing)}")

    price_overrides = {price.inventory_item_id: price.new_cost_per_unit for price in data.prices}

    affected, unaffected_count = _get_reprice_impacts(db, price_overrides)

    return costing_schemas.RepricePreview(affected_dishes=affected, unaffected_count=unaffected_count)

@router.post("/reprice")
def reprice(data: costing_schemas.RepriceRequest, db: Session = Depends(get_db), current_user: TokenData = _OWNER):
    # Apply new inventory prices and return affected dish costings.
    if not data.prices:
        return {
            "message": "No prices supplied", "affected_dishes": [], "unaffected_count": 0,
        }
    item_ids = {price.inventory_item_id for price in data.prices}
    items = (db.query(InventoryItem).filter(InventoryItem.id.in_(item_ids)).all())
    item_map = {item.id: item for item in items}
    missing = item_ids - set(item_map.keys())
    if missing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory items not found: {sorted(missing)}")
    
    price_overrides = {price.inventory_item_id: price.new_cost_per_unit for price in data.prices}

    # Calculating impacts using the new prices beofre presisting them.
    affected, unaffected_count  = _get_reprice_impacts(db, price_overrides)

    # Persisting new inventory prices.
    for item_id, new_price in price_overrides.items():
        item_map[item_id].cost_per_unit = new_price

    db.commit()

    return {
        "message": "Inventory prices updated successfully", "affected_dishes": [impact.model_dump() for impact in affected], "unaffected_count": unaffected_count
    }