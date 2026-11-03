import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from fastapi import APIRouter , Depends, HTTPException, status
from sqlalchemy.orm import Session, object_session

from app.api.deps import get_current_owner
from app.db.session import get_db
from app.models.costing_models import OVERHEAD_KINDS, DishCosting, DishCostingIngredient
from app.core.business_day import utcnow
from app.models.inventory_models import InventoryItem
from app.models.models import MenuItem

from app.schemas import costing_schemas
from app.schemas import TokenData

from app.crud import costing_crud

from app.utils import costing as costing_utils
from app.utils import pricing
from app.utils.units import IncompatibleUnitError, to_item_unit

router = APIRouter()
logger = logging.getLogger(__name__)

# Costs and margins are the owner's: staff never see them, here or on screen.
_OWNER = Depends(get_current_owner)


# Supports
def _menu_price_rupees(menu_item) -> Decimal | None:
    # To convert calculation in rupee because MenuItem is stored in paise.
    if menu_item.price is None:
        return None
    return Decimal(menu_item.price) / Decimal("100")

def _made_unit_price(item: InventoryItem, price_overrides, memo: dict, stack: tuple[int, ...], as_of: datetime | None = None) -> tuple[Decimal | None, bool]:
    # What one unit of a kitchen-made item costs (its batch's raw cost / yield, no
    # overheads), and whether every ingredient inside it is priced. The memo is keyed
    # by item id alone, so share one only across calls with the same overrides and as_of.
    if item.id in memo:
        return memo[item.id]
    if item.id in stack:
        # A loop that got past the save-time check: a gap, not a crash, but say where.
        logger.warning("Recipe loop through inventory items %s -> %s", stack, item.id)
        return None, False
    breakdown = _compute_breakdown(item.recipe, None, price_overrides, memo, stack + (item.id,), as_of)
    result = (breakdown.raw_material_cost / breakdown.yield_units, breakdown.is_complete)
    memo[item.id] = result
    return result

def _build_ingredient_inputs(ingredients: list[DishCostingIngredient], price_overrides: dict[int, Decimal] | None = None, memo: dict | None = None, stack: tuple[int, ...] = (), as_of: datetime | None = None) -> list[costing_utils.IngredientInput]:
    # Convert DB ingredient rows into the pure calculation input format.
    # Prices come from the purchase log, falling back to the typed price
    # (app/utils/pricing.py); an override replaces either. A kitchen-made item
    # is priced from its own recipe instead.
    memo = {} if memo is None else memo
    overrides = price_overrides or {}
    inputs = []

    for row in ingredients:
        if row.inventory_item is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Inventory item {row.inventory_item_id} not found.")
    items = [row.inventory_item for row in ingredients]
    db = object_session(items[0]) if items else None
    resolved = pricing.resolve_many(db, items, as_of) if db is not None else {}

    for row in ingredients:
        item = row.inventory_item
        current = resolved.get(item.id)
        overridden = item.id in overrides
        if item.recipe is not None and not overridden:
            made_price, complete = _made_unit_price(item, price_overrides, memo, stack, as_of)
            inputs.append(costing_utils.IngredientInput(
                item_id=item.id, name=item.name, quantity=Decimal(row.quantity), unit=row.unit, stock_unit=item.unit,
                cost_per_unit=made_price, is_active=item.is_active, pack_size=item.pack_size, pack_unit=item.pack_unit,
                price_source="recipe", incomplete=not complete,
            ))
            continue
        price = overrides.get(item.id, current.price if current else item.cost_per_unit)
        source = None if overridden or current is None else current.source
        price_as_of = None if overridden or current is None else current.as_of
        inputs.append(costing_utils.IngredientInput(
            item_id=item.id, name=item.name, quantity=Decimal(row.quantity), unit=row.unit, stock_unit=item.unit, 
            cost_per_unit=(
                Decimal(price)
                if price is not None
                else None
                ),
                is_active=item.is_active,
                pack_size=item.pack_size, pack_unit=item.pack_unit, is_presence=item.is_presence,
                price_source=source, price_as_of=price_as_of,
        ))
    return inputs

def _compute_breakdown(costing: DishCosting, menu_item, price_overrides: dict[int, Decimal] | None = None, memo: dict | None = None, stack: tuple[int, ...] = (), as_of: datetime | None = None):
    # Calculate a costing breakdown for a persisted or temporary costing.
    if costing.inventory_item_id is not None:
        stack = stack + (costing.inventory_item_id,)
    ingredients = _build_ingredient_inputs(costing.ingredients, price_overrides=price_overrides, memo=memo, stack=stack, as_of=as_of)

    if menu_item is None:
        # A made item shows its raw batch cost: overheads and a price belong to the dish.
        overheads = {kind: costing_utils.OverheadInput(mode="percent", value=Decimal("0"), inherited=True) for kind in OVERHEAD_KINDS}
        target_margin = selling_price = None
    else:
        overheads = costing_utils.resolve_overheads(costing)
        target_margin = costing_utils.resolve_target_margin(costing)
        selling_price = _menu_price_rupees(menu_item)

    try:
        return costing_utils.compute(ingredients=ingredients, overheads=overheads, yield_units=costing.yield_units, selling_price=selling_price, target_margin_percent=target_margin)
    except IncompatibleUnitError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

def _breakdown_to_schema(breakdown: costing_utils.CostBreakdown) -> costing_schemas.CostBreakdownOut:
    return costing_schemas.CostBreakdownOut(
        ingredients=[
            costing_schemas.IngredientLineOut(
                inventory_item_id=line.item_id, name=line.name, quantity=line.quantity, unit=line.unit, stock_unit=line.stock_unit, unit_price=line.unit_price, line_cost=line.line_cost, share_percent=line.share_percent, price_missing=line.price_missing, is_active=line.is_active, unit_error=line.unit_error, needs_pack_size=line.needs_pack_size,
                price_source=line.price_source, price_as_of=line.price_as_of, reason=line.reason,
                is_presence=line.is_presence,
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

    made = costing.made_item
    if costing.menu_item is None and made is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Costing has no associated menu item.")

    breakdown = _compute_breakdown(costing, costing.menu_item)

    # The recipes that list this made item as an ingredient.
    used_in = {}
    for row in (made.costing_ingredients if made else []):
        user = row.costing
        dish = user.menu_item
        used_in[user.id] = costing_schemas.UsedIn(costing_id=user.id, name=(dish or user.made_item).name, kind="dish" if dish else "made")

    auto_yield = None
    if made:
        try:
            auto_yield = sum((to_item_unit(r.quantity, r.unit, made.unit) for r in costing.ingredients), Decimal(0))
        except IncompatibleUnitError:
            pass

    return costing_schemas.DishCostingOut(
        id=costing.id,
        menu_item_id=costing.menu_item_id,
        menu_item_name=costing.menu_item.name if costing.menu_item else None,
        inventory_item_id=costing.inventory_item_id,
        kind="dish" if costing.menu_item else "made",
        name=(costing.menu_item or made).name,
        unit=made.unit if made else None,
        used_in=list(used_in.values()),
        yield_units=costing.yield_units,
        auto_yield=auto_yield,
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

def _batch_yield(data: costing_schemas.DishCostingIn, made_item: InventoryItem | None, inventory_items: list[InventoryItem]):
    # A dish says how many portions it makes. A made item may leave it out, and then
    # the batch makes the sum of its lines, if they all convert to the item's unit.
    if data.yield_units is not None:
        return data.yield_units
    total = Decimal(0)
    for row in data.ingredients:
        try:
            total += to_item_unit(row.quantity, row.unit, made_item.unit)
        except IncompatibleUnitError:
            name = next((i.name for i in inventory_items if i.id == row.inventory_item_id), "An ingredient")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Type how much one batch makes ({name} is in {row.unit}, the batch in {made_item.unit})")
    if total <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type how much one batch makes")
    return total

def _build_costing_model(data: costing_schemas.DishCostingIn, inventory_items: dict[int, InventoryItem], yield_units) -> tuple[DishCosting, list[DishCostingIngredient]]:
    # Build ORM costing + ingredient rows from validated API input.

    costing = DishCosting(menu_item_id=data.menu_item_id, inventory_item_id=data.inventory_item_id, yield_units=yield_units, target_margin_percent=data.target_margin_percent, notes=data.notes)

    for kind in ("packaging", "labour", "fixed", "wastage"):
        override = getattr(data, kind)
        _apply_overhead(costing, kind, override)

    ingredients = []

    for index, ingredient in enumerate(data.ingredients):
        item = inventory_items.get(ingredient.inventory_item_id)    
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=(f"Inventory item {ingredient.inventory_item_id} not found."))
        
        ingredients.append(DishCostingIngredient(inventory_item_id=item.id, quantity=ingredient.quantity, unit=ingredient.unit, sort_order=index, inventory_item=item))
    
    return costing, ingredients


# Routes

@router.get("", response_model=List[costing_schemas.DishCostingSummary])
def get_costings(db: Session = Depends(get_db), current_user: TokenData = _OWNER):
    # Get all dish costing.
    costings = costing_crud.get_costings(db)
    result = []
    for costing in costings:
        if costing.menu_item is None:
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
            gap_count=sum(1 for line in breakdown.ingredients if line.reason),
        ))
    
    return result

_STATUS_ORDER = {"below_target": 0, "missing_prices": 1, "no_recipe": 2}

@router.get("/overview", response_model=costing_schemas.Overview)
def get_overview(db: Session = Depends(get_db), current_user: TokenData = _OWNER):
    # Every recipe in one list: dishes (and sellable dishes with no recipe yet) and
    # kitchen-made items, with this week's cost against last week's.
    week_ago = utcnow() - timedelta(days=7)
    rows = []
    # One memo per point in time, so a made item used by many dishes is costed once.
    memo_now, memo_week_ago = {}, {}

    def last_week(costing, menu_item):
        past = _compute_breakdown(costing, menu_item, memo=memo_week_ago, as_of=week_ago)
        return past.cost_per_unit if past.is_complete else None

    for costing in db.query(DishCosting).all():
        menu_item, made = costing.menu_item, costing.made_item
        if menu_item is None and (made is None or not made.is_active):
            continue
        b = _compute_breakdown(costing, menu_item, memo=memo_now)
        missing = sum(1 for line in b.ingredients if line.reason)
        if not b.is_complete:
            state = "missing_prices"
        elif menu_item is None:
            state = "costed"
        else:
            state = "below_target" if b.margin_percent is not None and b.margin_percent < b.target_margin_percent else "on_target"
        rows.append(costing_schemas.OverviewRow(
            kind="dish" if menu_item else "made", costing_id=costing.id,
            menu_item_id=costing.menu_item_id, inventory_item_id=costing.inventory_item_id,
            name=(menu_item or made).name,
            category=getattr((menu_item or made).category, "name", None),
            cost_per_unit=b.cost_per_unit, unit=made.unit if made else None,
            selling_price=b.selling_price, margin_percent=b.margin_percent if b.is_complete else None, target_margin_percent=b.target_margin_percent,
            margin_ceiling=(((b.selling_price - b.cost_per_unit) / b.selling_price * 100).quantize(Decimal("0.01")) if not b.is_complete and b.selling_price else None),
            missing_count=missing, cost_last_week=last_week(costing, menu_item), status=state,
        ))

    costed = {r.menu_item_id for r in rows if r.menu_item_id}
    for menu_item in db.query(MenuItem).filter(MenuItem.is_available.is_(True)).all():
        if menu_item.id not in costed:
            rows.append(costing_schemas.OverviewRow(
                kind="dish", menu_item_id=menu_item.id, name=menu_item.name,
                category=menu_item.category.name if menu_item.category else None,
                selling_price=_menu_price_rupees(menu_item), status="no_recipe",
            ))

    rows.sort(key=lambda r: (_STATUS_ORDER.get(r.status, 3), r.margin_percent if r.status == "below_target" else 0, r.name.lower()))
    margins = [r.margin_percent for r in rows if r.kind == "dish" and r.margin_percent is not None]
    return costing_schemas.Overview(
        rows=rows,
        totals=costing_schemas.OverviewTotals(
            below_target=sum(r.status == "below_target" for r in rows),
            missing_prices=sum(r.status == "missing_prices" for r in rows),
            no_recipe=sum(r.status == "no_recipe" for r in rows),
            average_margin=(sum(margins) / len(margins)).quantize(Decimal("0.01")) if margins else None,
        ),
    )

@router.get("/defaults", response_model=costing_schemas.DefaultsOut)
def get_costing_defaults(current_user: TokenData = _OWNER):
    """The cafe-wide overheads and target margin a dish uses unless it overrides them."""
    overheads = costing_utils.resolve_overheads()
    return costing_schemas.DefaultsOut(
        **{kind: costing_schemas.OverheadOverride(mode=o.mode, value=o.value) for kind, o in overheads.items()},
        target_margin_percent=costing_utils.resolve_target_margin(),
    )

@router.get("/{costing_id}", response_model=costing_schemas.DishCostingOut)
def get_costing(costing_id: int, db: Session = Depends(get_db), current_user: TokenData = _OWNER):
    # Get single dish costing
    costing = costing_crud.get_costing(db, costing_id)

    if not costing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Costing not found.")
    
    return _costing_to_schema(costing)

@router.get("/item/{inventory_item_id}", response_model=costing_schemas.DishCostingOut)
def get_made_item_costing(inventory_item_id: int, db: Session = Depends(get_db), current_user: TokenData = _OWNER):
    # Get the recipe of a kitchen-made inventory item.
    costing = costing_crud.get_costing_by_made_item(db, inventory_item_id)

    if not costing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recipe found for this item.")

    return _costing_to_schema(costing)

@router.get("/menu/{menu_item_id}", response_model=costing_schemas.DishCostingOut)
def get_menu_item_costing(menu_item_id: int, db: Session = Depends(get_db), current_user: TokenData = _OWNER):
    # Get costing for a specific menu item.
    menu_item = costing_crud.get_menu_item(db, menu_item_id)

    if not menu_item: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found.")

    costing = costing_crud.get_costing_by_menu_item(db, menu_item_id)

    if not costing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No costing found for this menu item.")
    
    return _costing_to_schema(costing)

# PREPARE (shared by preview, create and update)

def _prepare(db: Session, data: costing_schemas.DishCostingIn, own_id: int | None = None, unique: bool = True):
    # Resolve what the costing is for, check it, and build the unsaved costing + rows.
    if data.menu_item_id is not None:
        subject = costing_crud.get_menu_item(db, data.menu_item_id)
        if not subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
        existing = costing_crud.get_costing_by_menu_item(db, data.menu_item_id)
        made_item = None
    else:
        made_item = subject = costing_crud.get_inventory_item(db, data.inventory_item_id)
        if not made_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")
        existing = costing_crud.get_costing_by_made_item(db, data.inventory_item_id)

    if unique and existing and existing.id != own_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A costing already exists for this " + ("menu item." if made_item is None else "item."))

    inventory_ids = {ingredient.inventory_item_id for ingredient in data.ingredients}
    inventory_items = (
        db.query(InventoryItem).filter(InventoryItem.id.in_(inventory_ids)).all()
        if inventory_ids
        else []
    )
    costing, ingredient_rows = _build_costing_model(data, {item.id: item for item in inventory_items}, _batch_yield(data, made_item, inventory_items))
    if own_id is None:
        # On update the rows go straight to the saved costing: attaching them here would drag this unsaved copy into the session.
        costing.ingredients = ingredient_rows

    if made_item is not None:
        loop = costing_crud.find_cycle(db, made_item.id, list(inventory_ids))
        if loop:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A recipe can't use itself: " + " → ".join(loop))

    return subject if made_item is None else None, costing, ingredient_rows


# PREVIEW

@router.post("/preview", response_model=costing_schemas.CostBreakdownOut)
def preview_costing(data: costing_schemas.DishCostingIn, db: Session = Depends(get_db), current_user: TokenData = _OWNER):
    # Calculate costing without saving it. Editing a saved recipe previews too, so no uniqueness check.
    menu_item, costing, _ = _prepare(db, data, unique=False)
    return _breakdown_to_schema(_compute_breakdown(costing, menu_item))


# CREATE

@router.post("", response_model=costing_schemas.DishCostingOut, status_code=status.HTTP_201_CREATED)
def create_costing(data: costing_schemas.DishCostingIn, db: Session = Depends(get_db), current_user: TokenData=_OWNER):
    # Create a dish costing.
    menu_item, costing, ingredient_rows = _prepare(db, data)

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

    if (costing.menu_item_id is None) != (data.menu_item_id is None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A dish's recipe can't become a made item's, or the other way round.")

    menu_item, new_costing, ingredient_rows = _prepare(db, data, own_id=costing_id)

    update_data = {
        "menu_item_id": data.menu_item_id,
        "inventory_item_id": data.inventory_item_id,
        "yield_units": new_costing.yield_units,
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
def apply_suggested_price(costing_id: int, data: costing_schemas.ApplyPriceIn, db: Session = Depends(get_db), current_user: TokenData = _OWNER):
    # Apply the calculated suggested selling price to the menu item. data.price is
    # the price the owner confirmed; if a purchase moved the cost since, refuse
    # rather than write a price they never saw.
    costing = costing_crud.get_costing(db, costing_id)

    if not costing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Costing not found")

    menu_item = costing.menu_item

    if menu_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")

    breakdown = _compute_breakdown(costing, menu_item)

    if not breakdown.is_complete:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Some ingredients aren't costed yet, so there is no suggested price.",
        )
    if breakdown.suggested_price is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No suggested price is available.")
    if breakdown.suggested_price != data.price:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The cost changed: the suggested price is now ₹{breakdown.suggested_price:,.0f}. Check it and try again.",
        )

    # MenuItem.price is stored in paise.
    menu_item.price = int(breakdown.suggested_price * Decimal("100"))

    db.commit()
    db.refresh(menu_item)

    return _costing_to_schema(costing)


# REPRICING

# Repricing supports
def _passes_through(item: InventoryItem, overrides: dict[int, Decimal], cache: dict, stack: tuple[int, ...] = ()):
    # Whether a changed price reaches this item: None if not, else the kitchen-made
    # items between them (the item itself included, if it is one), by id.
    if item.id in overrides:
        return {}
    if item.recipe is None or item.id in stack:
        return None
    if item.id not in cache:
        found = None
        for row in item.recipe.ingredients:
            sub = _passes_through(row.inventory_item, overrides, cache, stack + (item.id,))
            if sub is not None:
                found = {**(found or {}), **sub}
        cache[item.id] = None if found is None else {**found, item.id: item}
    return cache[item.id]

def _get_reprice_impacts(db: Session, price_overrides: dict[int, Decimal]):
    # Calculate the impact of changed inventory prices across all dishes, directly
    # or through the kitchen-made items they use, and on those made items.
    affected = []
    unaffected_count = 0
    reach = {}
    before_memo, after_memo = {}, {}

    for costing in costing_crud.get_costings(db):
        if costing.menu_item is None:
            continue

        via = {}
        touched = False
        for row in costing.ingredients:
            sub = _passes_through(row.inventory_item, price_overrides, reach)
            if sub is not None:
                touched = True
                via.update(sub)

        if not touched:
            unaffected_count += 1
            continue

        before = _compute_breakdown(costing, costing.menu_item, memo=before_memo)
        after = _compute_breakdown(costing, costing.menu_item, price_overrides=price_overrides, memo=after_memo)

        target = costing_utils.resolve_target_margin(costing)

        margin_before = before.margin_percent
        margin_after = after.margin_percent

        crosses_below_target = (margin_before is not None and margin_after is not None and margin_before >= target and margin_after < target)

        affected.append(costing_schemas.DishImpact(
            costing_id=costing.id, menu_item_name=costing.menu_item.name, cost_before=before.cost_per_unit, cost_after=after.cost_per_unit, margin_before=margin_before, margin_after=margin_after, crosses_below_target=crosses_below_target,
            via=[m.name for m in via.values()],
        ))

    made_impacts = []
    for costing in db.query(DishCosting).filter(DishCosting.inventory_item_id.isnot(None)).all():
        item = costing.made_item
        if not item.is_active or item.id in price_overrides or _passes_through(item, price_overrides, reach) is None:
            continue
        made_impacts.append(costing_schemas.MadeImpact(
            item_id=item.id, name=item.name, unit=item.unit,
            cost_before=_made_unit_price(item, None, before_memo, ())[0],
            cost_after=_made_unit_price(item, price_overrides, after_memo, ())[0],
        ))

    return affected, unaffected_count, made_impacts

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

    affected, unaffected_count, _ = _get_reprice_impacts(db, price_overrides)

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
    affected, unaffected_count, _ = _get_reprice_impacts(db, price_overrides)

    # Persisting new inventory prices.
    for item_id, new_price in price_overrides.items():
        item_map[item_id].cost_per_unit = new_price

    db.commit()

    return {
        "message": "Inventory prices updated successfully", "affected_dishes": [impact.model_dump() for impact in affected], "unaffected_count": unaffected_count
    }