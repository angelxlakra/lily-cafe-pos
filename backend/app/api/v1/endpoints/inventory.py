from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import case, func, desc
from decimal import ROUND_HALF_UP, Decimal

from app.db.session import get_db
from app.models.inventory_models import (
    CountLineStatus,
    InventoryCategory,
    InventoryCount,
    InventoryCountLine,
    InventoryItem,
    InventoryTransaction,
    TransactionType,
    Vendor,
    presence_quantity,
)
from app.core.business_day import (
    count_night, night_utc_bounds, utcnow,
)
from app.schemas import inventory_schemas
from app.core import settings_store
from app.api.deps import get_current_user, get_current_owner
from app.schemas import TokenData, UserRole
from app.utils.email_sender import send_inventory_report
from app.utils.units import compatible, convert
from app.utils import pricing, usage

router = APIRouter()

# Access model for inventory:
#   - Reads and day-to-day stock movements (purchases, usage, counts) are
#     part of running the day, so any signed-in staff member can do them.
#   - Categories and items are master data — they carry cost prices and
#     reorder levels and shape every future report — so, like the menu,
#     only the owner login may create, change or remove them.
_READ = Depends(get_current_user)
_STAFF = Depends(get_current_user)
_OWNER = Depends(get_current_owner)

# ============================================================================
# Categories
# ============================================================================

@router.get("/categories", response_model=List[inventory_schemas.InventoryCategory])
def get_categories(db: Session = Depends(get_db), current_user: TokenData = _READ):
    """Get all inventory categories, in count order."""
    return db.query(InventoryCategory).order_by(InventoryCategory.sort_order, InventoryCategory.id).all()


def _next_sort_order(db: Session, model) -> int:
    """Place new rows after everything the owner has already arranged."""
    return (db.query(func.max(model.sort_order)).scalar() or 0) + 1


def _apply_sort_order(db: Session, model, ids: List[int]) -> None:
    rows = {row.id: row for row in db.query(model).filter(model.id.in_(ids)).all()}
    missing = set(ids) - rows.keys()
    if missing:
        raise HTTPException(status_code=404, detail=f"Unknown ids: {sorted(missing)}")
    for position, row_id in enumerate(ids, start=1):
        rows[row_id].sort_order = position
    db.commit()


@router.put("/categories/order", status_code=status.HTTP_204_NO_CONTENT)
def reorder_categories(
    order: inventory_schemas.SortOrderUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = _OWNER,
):
    """Set the order categories appear in during the nightly count. Owner only."""
    _apply_sort_order(db, InventoryCategory, order.ids)

@router.post("/categories", response_model=inventory_schemas.InventoryCategory, status_code=status.HTTP_201_CREATED)
def create_category(
    category: inventory_schemas.InventoryCategoryCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = _OWNER,
):
    """Create a new inventory category. Owner login only."""
    from datetime import datetime

    db_category = db.query(InventoryCategory).filter(InventoryCategory.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="Category name already exists")

    now = datetime.now()
    new_category = InventoryCategory(
        name=category.name,
        sort_order=_next_sort_order(db, InventoryCategory),
        created_at=now,
        updated_at=now
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.patch("/categories/{category_id}", response_model=inventory_schemas.InventoryCategory)
def update_category(
    category_id: int,
    category_update: inventory_schemas.InventoryCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = _OWNER,
):
    """Update an inventory category."""
    db_category = db.query(InventoryCategory).filter(InventoryCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category_update.name:
        existing = db.query(InventoryCategory).filter(InventoryCategory.name == category_update.name).first()
        if existing and existing.id != category_id:
            raise HTTPException(status_code=400, detail="Category name already exists")
        db_category.name = category_update.name
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = _OWNER,
):
    """Delete an inventory category."""
    db_category = db.query(InventoryCategory).filter(InventoryCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has items
    if db_category.items:
        raise HTTPException(status_code=400, detail="Cannot delete category containing items")
    
    db.delete(db_category)
    db.commit()
    return {"message": "Category deleted successfully"}

# ============================================================================
# Items
# ============================================================================

@router.get("/items", response_model=dict)
def get_items(
    category_id: Optional[int] = None,
    is_active: bool = True,
    low_stock: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = _READ
):
    """Get all inventory items with filtering."""
    query = db.query(InventoryItem)
    
    if is_active:
        query = query.filter(InventoryItem.is_active == True)
    
    if category_id:
        query = query.filter(InventoryItem.category_id == category_id)
    
    if search:
        query = query.filter(InventoryItem.name.ilike(f"%{search}%"))
        
    items = query.order_by(InventoryItem.sort_order, InventoryItem.id).all()
    
    # Filter low stock in python since it's a property
    if low_stock:
        items = [item for item in items if item.is_low_stock]
        
    prices = pricing.resolve_many(db, items)
    result_items = []
    low_stock_count = 0
    for item in items:
        result_items.append(_item_dict(item, prices[item.id]))
        if item.is_low_stock:
            low_stock_count += 1

    return {
        "items": result_items,
        "total": len(result_items),
        "low_stock_count": low_stock_count
    }

@router.get("/items/low-stock", response_model=dict)
def get_low_stock_items(db: Session = Depends(get_db), current_user: TokenData = _READ):
    """Get all low stock items sorted by urgency."""
    items = db.query(InventoryItem).filter(InventoryItem.is_active == True).all()
    low_stock_items = []
    
    for item in items:
        if item.is_low_stock:
            percentage = 0
            if item.min_threshold > 0:
                percentage = (item.current_quantity / item.min_threshold) * 100
            
            item_model = inventory_schemas.LowStockItem.model_validate(item, from_attributes=True)
            item_dict = item_model.model_dump()
            if item.category:
                item_dict['category_name'] = item.category.name
            item_dict['percentage_remaining'] = percentage
            low_stock_items.append(item_dict)
            
    # Sort by percentage remaining (ascending)
    low_stock_items.sort(key=lambda x: x['percentage_remaining'])
    
    return {
        "low_stock_items": low_stock_items,
        "count": len(low_stock_items)
    }

@router.put("/items/order", status_code=status.HTTP_204_NO_CONTENT)
def reorder_items(
    order: inventory_schemas.SortOrderUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = _OWNER,
):
    """Set the order items appear in within their category. Owner only."""
    _apply_sort_order(db, InventoryItem, order.ids)

def _item_dict(item: InventoryItem, price: pricing.ResolvedPrice, schema=inventory_schemas.InventoryItem) -> dict:
    """An item as the API returns it, with its category and resolved price."""
    item_dict = schema.model_validate(item, from_attributes=True).model_dump()
    if item.category:
        item_dict['category_name'] = item.category.name
    item_dict['is_low_stock'] = item.is_low_stock
    item_dict.update(price.as_dict())
    return item_dict

# Columns that can't hold NULL; sending null for one is a client error, not a 500.
_REQUIRED_ITEM_FIELDS = ("name", "unit", "min_threshold", "count_mode", "is_active")
_CENT = Decimal("0.01")

def _to_cents(value: Decimal) -> Decimal:
    """Round to what the column holds, but never a positive amount down to 0:
    a 1 g alert that became 0 kg would stop alerting when the item runs out."""
    rounded = value.quantize(_CENT, rounding=ROUND_HALF_UP)
    return max(rounded, _CENT) if value > 0 else rounded

def _apply_presence_rules(item: InventoryItem) -> None:
    """A yes/no item has no unit, price or pack, and alerts when out (0 < 1)."""
    if item.is_presence:
        item.unit, item.min_threshold, item.cost_per_unit = "yes/no", Decimal(1), None
        item.pack_size = item.pack_unit = None

def _log_setup_adjustment(db: Session, item: InventoryItem, before: Decimal, notes: str, username: str) -> bool:
    """Record a stock change made by editing an item (e.g. a flip to yes/no clamping 3 to 1)."""
    if item.current_quantity == before:
        return False
    db.add(InventoryTransaction(
        item_id=item.id,
        transaction_type=TransactionType.ADJUSTMENT,
        quantity=item.current_quantity - before,
        notes=notes,
        recorded_by=username,
        previous_quantity=before,
        new_quantity=item.current_quantity,
    ))
    return True

def _convert_to_unit(item: InventoryItem, new_unit: str, sent: dict, stock_sent: bool) -> None:
    """g -> kg keeps the same stock: 2000 g becomes 2 kg, not 2000 kg.

    Only values not sent in the same row are converted; sent ones are already
    in the new unit. Units of different kinds (g -> pcs) convert nothing.
    """
    old_unit = item.unit
    if not compatible(old_unit, new_unit) or convert(1, old_unit, new_unit) == 1:
        return
    if not stock_sent:
        item.current_quantity = _to_cents(convert(item.current_quantity, old_unit, new_unit))
    if "min_threshold" not in sent:
        item.min_threshold = _to_cents(convert(item.min_threshold, old_unit, new_unit))
    if "cost_per_unit" not in sent and item.cost_per_unit is not None:
        # A price is per unit, so it scales the other way.
        item.cost_per_unit = _to_cents(convert(item.cost_per_unit, new_unit, old_unit))

@router.patch("/items", response_model=dict)
def bulk_update_items(
    payload: inventory_schemas.BulkItemsUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = _OWNER,
):
    """The setup grid's one Save: every changed row, applied in one commit.

    Retiring is is_active=false, the same soft delete as DELETE /items/{id}.
    A stock change is written as an adjustment so the stock log stays complete.
    Owner only.
    """
    ids = [row.id for row in payload.items]
    items = {item.id: item for item in db.query(InventoryItem).filter(InventoryItem.id.in_(ids))}
    missing = sorted(set(ids) - items.keys())
    if missing:
        raise HTTPException(status_code=404, detail=f"Items not found: {missing}")

    category_ids = {row.category_id for row in payload.items if row.category_id is not None}
    known = {c.id for c in db.query(InventoryCategory.id).filter(InventoryCategory.id.in_(category_ids))}
    if category_ids - known:
        raise HTTPException(status_code=400, detail=f"Categories not found: {sorted(category_ids - known)}")

    adjusted = 0
    for row in payload.items:
        item = items[row.id]
        changes = row.model_dump(exclude_unset=True, exclude={"id", "current_quantity"})
        blank = [key for key in _REQUIRED_ITEM_FIELDS if key in changes and changes[key] is None]
        if blank:
            raise HTTPException(status_code=422, detail=f"{item.name}: {', '.join(blank)} can't be empty")
        if "unit" in changes:
            _convert_to_unit(item, changes["unit"], changes, row.current_quantity is not None)
        # Taken before count_mode is set: flipping to yes/no clamps the stock
        # (3 bottles -> 1), and that change belongs in the stock log.
        before = item.current_quantity
        for key, value in changes.items():
            setattr(item, key, value)
        _apply_presence_rules(item)
        item.needs_setup = False  # the owner has now looked at it
        if row.current_quantity is not None:
            item.current_quantity = row.current_quantity  # clamped by the model for yes/no
        if _log_setup_adjustment(db, item, before, "Setup grid", current_user.username):
            adjusted += 1

    db.commit()
    return {"updated": len(items), "adjusted": adjusted}

@router.get("/items/{item_id}", response_model=inventory_schemas.InventoryItem)
def get_item(item_id: int, db: Session = Depends(get_db), current_user: TokenData = _READ):
    """Get a single inventory item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return _item_dict(item, pricing.resolve_one(db, item))

@router.post("/items", response_model=inventory_schemas.InventoryItem, status_code=status.HTTP_201_CREATED)
def create_item(
    item: inventory_schemas.InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = _OWNER,
):
    """Create a new inventory item. Owner login only."""
    # Check uniqueness within category if category provided
    if item.category_id:
        existing = db.query(InventoryItem).filter(
            InventoryItem.name == item.name,
            InventoryItem.category_id == item.category_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Item name already exists in this category")
            
    new_item = InventoryItem(
        name=item.name,
        unit=item.unit,
        current_quantity=item.current_quantity,
        min_threshold=item.min_threshold,
        cost_per_unit=item.cost_per_unit,
        category_id=item.category_id,
        count_mode=item.count_mode,
        pack_size=item.pack_size,
        pack_unit=item.pack_unit,
        sort_order=_next_sort_order(db, InventoryItem),
    )
    _apply_presence_rules(new_item)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return _item_dict(new_item, pricing.resolve_one(db, new_item))

@router.patch("/items/{item_id}", response_model=inventory_schemas.InventoryItem)
def update_item(
    item_id: int,
    item_update: inventory_schemas.InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = _OWNER,
):
    """Update an inventory item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    update_data = item_update.model_dump(exclude_unset=True)
    blank = [key for key in _REQUIRED_ITEM_FIELDS if key in update_data and update_data[key] is None]
    if blank:
        raise HTTPException(status_code=422, detail=f"{', '.join(blank)} can't be empty")
    before = item.current_quantity
    for key, value in update_data.items():
        setattr(item, key, value)
    _apply_presence_rules(item)
    _log_setup_adjustment(db, item, before, "Item edited", current_user.username)

    db.commit()
    db.refresh(item)
    return _item_dict(item, pricing.resolve_one(db, item))

@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = _OWNER,
):
    """Soft delete an inventory item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    item.is_active = False
    db.commit()
    return {"message": "Item deactivated successfully"}

# ============================================================================
# Transactions
# ============================================================================

def _purchase_items(db: Session, item_ids) -> dict:
    """The purchasable items named on a sheet, or a 400 naming the first bad one."""
    items = {i.id: i for i in db.query(InventoryItem).filter(InventoryItem.id.in_(set(item_ids)))}
    for item_id in item_ids:
        item = items.get(item_id)
        if not item:
            raise HTTPException(status_code=400, detail=f"Item ID {item_id} not found")
        if not item.is_active:
            raise HTTPException(status_code=400, detail=f"Item {item.name} is inactive")
    return items

def _price_check(item: InventoryItem, quantity, total_amount, current: pricing.ResolvedPrice) -> dict:
    """This line's unit price against the item's current price.

    A ₹0 gift is never a jump: it was entered on purpose, with a note, and
    never becomes the price.
    """
    new_price = pricing.unit_price(total_amount, quantity)
    is_gift = total_amount is not None and total_amount == 0
    return {
        "item_id": item.id,
        "item_name": item.name,
        "unit": item.unit,
        "unit_price": new_price,
        "previous_price": current.price,
        "previous_source": current.source,
        "previous_as_of": current.as_of,
        "change": None if is_gift else pricing.price_change(current.price, new_price),
        "is_jump": not is_gift and pricing.is_price_jump(current.price, new_price),
    }

def _purchase_dict(t: InventoryTransaction) -> dict:
    return {
        "id": t.id,
        "item_id": t.item_id,
        "item_name": t.item.name,
        "unit": t.item.unit,
        "transaction_type": t.transaction_type,
        "quantity": t.quantity,
        "total_amount": t.total_amount,
        "unit_price": pricing.unit_price(t.total_amount, t.quantity),
        "vendor_id": t.vendor_id,
        "vendor_name": t.vendor.name if t.vendor else None,
        "notes": t.notes,
        "pack_count": t.pack_count,
        "previous_quantity": t.previous_quantity,
        "new_quantity": t.new_quantity,
        "recorded_by": t.recorded_by,
        "created_at": t.created_at,
    }

@router.post("/transactions/purchase/check", response_model=List[inventory_schemas.PriceCheckResult])
def check_purchase_prices(
    check: inventory_schemas.PurchaseCheck,
    db: Session = Depends(get_db),
    current_user: TokenData = _STAFF,
):
    """Dry run for the purchase sheet: each line's unit price against the item's
    current price, flagged when it is more than ~30% away. Writes nothing.

    Lets the sheet ask "chicken was ₹320/kg, this is ₹520/kg — right?" before
    saving. Usually a typo or a different pack size.
    """
    items = _purchase_items(db, [line.item_id for line in check.items])
    prices = pricing.resolve_many(db, items.values())
    return [
        _price_check(items[line.item_id], line.quantity, line.total_amount, prices[line.item_id])
        for line in check.items
    ]

@router.post("/transactions/purchase", status_code=status.HTTP_201_CREATED)
def record_purchase(
    purchase: inventory_schemas.PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = _STAFF,
):
    """Record purchases: raise stock and log what was paid.

    Each line carries the TOTAL paid for it; the unit price is derived, never
    stored. Buying and paying are one event — there is no credit, so the total
    is complete. The vendor is optional and never blocks a purchase.
    """
    for line in purchase.items:
        if line.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
    items = _purchase_items(db, [line.item_id for line in purchase.items])

    vendor_ids = {line.vendor_id or purchase.vendor_id for line in purchase.items} - {None}
    known = {v.id for v in db.query(Vendor.id).filter(Vendor.id.in_(vendor_ids))}
    if vendor_ids - known:
        raise HTTPException(status_code=400, detail=f"Vendors not found: {sorted(vendor_ids - known)}")

    # Prices as they stood before this sheet, for the jump flags in the response.
    prices = pricing.resolve_many(db, items.values())
    checks = []
    transactions = []
    for line in purchase.items:
        item = items[line.item_id]
        checks.append(_price_check(item, line.quantity, line.total_amount, prices[item.id]))

        previous_qty = item.current_quantity
        item.current_quantity += line.quantity
        new_qty = item.current_quantity  # read back: a yes/no item stays at 1

        transaction = InventoryTransaction(
            item_id=item.id,
            transaction_type=TransactionType.PURCHASE,
            quantity=new_qty - previous_qty,
            total_amount=line.total_amount,
            vendor_id=line.vendor_id or purchase.vendor_id,
            notes=line.notes,
            pack_count=line.pack_count,
            recorded_by=current_user.username,
            previous_quantity=previous_qty,
            new_quantity=new_qty
        )
        db.add(transaction)
        transactions.append(transaction)

    db.commit()

    # Refresh to get IDs
    for t in transactions:
        db.refresh(t)

    return {
        "message": "Purchase recorded successfully",
        "total_amount": sum((t.total_amount for t in transactions if t.total_amount is not None), Decimal(0)),
        "transactions": [
            {**_purchase_dict(t), "price_check": check} for t, check in zip(transactions, checks)
        ],
    }

@router.get("/purchases", response_model=dict)
def get_purchases(
    business_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = _READ,
):
    """One business day's purchase sheet (default today), with the day's total.

    The total is the number to check against the cash spent; lines logged
    without an amount are counted in `unpriced` so a gap is visible. Each day's
    sheet is kept; staff see today's, the owner can open any day's. `items`
    holds the owner's columns per item bought: used (from sales × recipes),
    expected remaining, the day-end count and the wastage between them.
    """
    # The sheet's day is the count night (runs to 04:00), since it holds the
    # night's count: a count at 00:30 must land on the sheet staff can see.
    today = count_night()
    day = business_date or today
    if day != today and current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only the owner can open other days' sheets")
    rows = (
        db.query(InventoryTransaction)
        .filter(
            InventoryTransaction.transaction_type == TransactionType.PURCHASE,
            InventoryTransaction.created_at >= night_utc_bounds(day)[0],
            InventoryTransaction.created_at < night_utc_bounds(day)[1],
        )
        .order_by(InventoryTransaction.id)
        .all()
    )
    return {
        "business_date": day,
        "purchases": [_purchase_dict(t) for t in rows],
        "total_amount": sum((t.total_amount for t in rows if t.total_amount is not None), Decimal(0)),
        "unpriced": sum(1 for t in rows if t.total_amount is None),
        "items": _day_columns(db, day, rows),
        "editable": day == today,
    }

def _day_columns(db: Session, day: date, rows: List[InventoryTransaction]) -> dict:
    """Per item bought that day: opening, bought, used, remaining, day-end, wastage.

    remaining = opening + bought - used, where opening is the stock as the day
    began. Used, remaining and wastage stay None until a recipe uses the item:
    "not worked out" must not read as "none used". Wastage is remaining minus
    the day-end count, so a negative figure means more was on the shelf than
    the recipes account for.
    """
    items = {t.item_id: t.item for t in rows}
    used = usage.used_on(db, day, items.values())
    start, _ = night_utc_bounds(day)
    count = (
        db.query(InventoryCount).filter(InventoryCount.business_date == day)
        .order_by(InventoryCount.created_at.desc(), InventoryCount.id.desc()).first()
    )
    counted = {
        line.item_id: line.counted_quantity
        for line in (count.lines if count else [])
        if line.status != CountLineStatus.SKIPPED.value
    }
    columns = {}
    for item_id in items:
        lines = [t for t in rows if t.item_id == item_id]
        before = (
            db.query(InventoryTransaction.new_quantity)
            .filter(InventoryTransaction.item_id == item_id, InventoryTransaction.created_at < start)
            .order_by(InventoryTransaction.created_at.desc(), InventoryTransaction.id.desc())
            .first()
        )
        opening = before[0] if before else lines[0].previous_quantity
        bought = sum((t.quantity for t in lines), Decimal(0))
        remaining = None if used[item_id] is None else opening + bought - used[item_id]
        day_end = counted.get(item_id)
        columns[item_id] = {
            "opening": opening,
            "bought": bought,
            "used": used[item_id],
            "remaining": remaining,
            "day_end": day_end,
            "wastage": None if remaining is None or day_end is None else remaining - day_end,
        }
    return columns

@router.put("/counts/tonight/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def count_one_item(
    item_id: int,
    body: inventory_schemas.DayEndCount,
    db: Session = Depends(get_db),
    current_user: TokenData = _STAFF,
):
    """Day-end stock for one item, typed on the purchase sheet.

    It is tonight's count, not a second number: the line goes into tonight's
    count (started if there is none yet) with the same adjustment the count
    screen makes, and the count screen's own save reads the same way. No
    report email — that belongs to a full count.
    """
    item = db.get(InventoryItem, item_id)
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="Item not found")
    night = count_night()
    count = (
        db.query(InventoryCount).filter(InventoryCount.business_date == night)
        .order_by(InventoryCount.created_at.desc(), InventoryCount.id.desc()).first()
    )
    if count is None:
        count = InventoryCount(business_date=night, counted_by=current_user.username, items_total=0,
                               items_checked=0, items_changed=0, items_skipped=0)
        db.add(count)
    line = next((l for l in count.lines if l.item_id == item_id), None)
    if line is None:
        line = InventoryCountLine(item_id=item_id, previous_quantity=item.current_quantity, status="")
        count.lines.append(line)

    before = item.current_quantity
    new = _counted_value(item, body.counted_quantity)
    if new != before:
        item.current_quantity = new
        db.add(InventoryTransaction(
            item_id=item.id, transaction_type=TransactionType.ADJUSTMENT, quantity=new - before,
            notes=_count_note(item, before, new), recorded_by=current_user.username,
            previous_quantity=before, new_quantity=new,
        ))
    line.counted_quantity = new
    line.status = (CountLineStatus.CHECKED if new == line.previous_quantity else CountLineStatus.CHANGED).value
    statuses = [l.status for l in count.lines]
    count.items_total = len(statuses)
    count.items_checked = statuses.count(CountLineStatus.CHECKED.value)
    count.items_changed = statuses.count(CountLineStatus.CHANGED.value)
    count.items_skipped = statuses.count(CountLineStatus.SKIPPED.value)
    db.commit()

@router.get("/purchases/frequent", response_model=List[int])
def get_frequent_purchases(db: Session = Depends(get_db), current_user: TokenData = _READ):
    """Active item ids the cafe restocks most over the last 60 days, most often first.

    Counts each time stock went up. A logged purchase weighs 3; an upward count
    correction weighs 1 — before purchases were logged it is the only trace of
    buying, so the picker has something to offer on day one.
    """
    since = utcnow() - timedelta(days=60)
    T = InventoryTransaction
    score = func.sum(case((T.transaction_type == TransactionType.PURCHASE, 3), else_=1))
    rows = (
        db.query(T.item_id)
        .join(InventoryItem, InventoryItem.id == T.item_id)
        .filter(InventoryItem.is_active, T.new_quantity > T.previous_quantity, T.created_at >= since)
        .group_by(T.item_id)
        .order_by(score.desc(), func.max(T.created_at).desc())
        .limit(30)
    )
    return [item_id for (item_id,) in rows]

def _editable_purchase(db: Session, purchase_id: int) -> InventoryTransaction:
    """A purchase line that may still be corrected in place, or a 404/409.

    Same sheet day (the count night) only, and only until a count is saved after it: once the
    count has taken it in, a correction is an adjustment so history stays honest.
    """
    t = db.get(InventoryTransaction, purchase_id)
    if not t or t.transaction_type != TransactionType.PURCHASE:
        raise HTTPException(status_code=404, detail="Purchase not found")
    if not night_utc_bounds(count_night())[0] <= t.created_at < night_utc_bounds(count_night())[1]:
        raise HTTPException(status_code=409, detail="Only today's purchases can be corrected; use a stock adjustment")
    # Column to column: SQLite keeps CURRENT_TIMESTAMP as text without
    # microseconds, so a Python datetime would miss a count in the same second.
    purchased_at = db.query(InventoryTransaction.created_at).filter(InventoryTransaction.id == t.id).scalar_subquery()
    if db.query(InventoryCount.id).filter(InventoryCount.created_at >= purchased_at).first():
        raise HTTPException(status_code=409, detail="Tonight's count already includes this purchase; use a stock adjustment")
    return t

def _move_purchase_stock(t: InventoryTransaction, quantity: Decimal) -> None:
    """Re-apply a purchase line as `quantity` (0 undoes it), keeping stock and the row in step."""
    item = t.item
    before = item.current_quantity
    item.current_quantity = before - t.quantity + quantity  # clamped by the model for yes/no
    t.quantity += item.current_quantity - before
    t.new_quantity = t.previous_quantity + t.quantity

@router.patch("/purchases/{purchase_id}", response_model=dict)
def edit_purchase(
    purchase_id: int,
    edit: inventory_schemas.PurchaseEdit,
    db: Session = Depends(get_db),
    current_user: TokenData = _STAFF,
):
    """Correct a line on today's sheet: quantity moves stock by the difference."""
    t = _editable_purchase(db, purchase_id)
    changes = edit.model_dump(exclude_unset=True)
    if changes.get("vendor_id") is not None and not db.get(Vendor, changes["vendor_id"]):
        raise HTTPException(status_code=400, detail="Vendor not found")
    if changes.get("quantity") is not None:
        _move_purchase_stock(t, changes.pop("quantity"))
    for key, value in changes.items():
        setattr(t, key, value)
    if t.total_amount is not None and t.total_amount == 0 and not (t.notes or "").strip():
        raise HTTPException(status_code=422, detail="A purchase of ₹0 needs a note saying why (e.g. free from the vendor)")
    db.commit()
    db.refresh(t)
    return _purchase_dict(t)

@router.delete("/purchases/{purchase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase(purchase_id: int, db: Session = Depends(get_db), current_user: TokenData = _STAFF):
    """Remove a line logged by mistake today, taking its stock back out."""
    t = _editable_purchase(db, purchase_id)
    _move_purchase_stock(t, Decimal(0))
    db.delete(t)
    db.commit()

@router.post("/items/quick", response_model=inventory_schemas.InventoryItem, status_code=status.HTTP_201_CREATED)
def quick_create_item(
    payload: inventory_schemas.QuickItemCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = _STAFF,
):
    """Add an item from the purchase sheet with just a name and unit. Staff can.

    Flagged needs_setup for the owner to configure in the setup grid, so nobody
    has to abandon the sheet. An active item with the same name is returned
    instead of duplicated.
    """
    name = payload.name.strip()
    existing = db.query(InventoryItem).filter(
        func.lower(InventoryItem.name) == name.lower(), InventoryItem.is_active
    ).first()
    if existing:
        return _item_dict(existing, pricing.resolve_one(db, existing))
    item = InventoryItem(
        name=name, unit=payload.unit.strip(), current_quantity=0, min_threshold=0,
        needs_setup=True, sort_order=_next_sort_order(db, InventoryItem),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _item_dict(item, pricing.resolve_one(db, item))

@router.get("/vendors", response_model=List[inventory_schemas.Vendor])
def get_vendors(db: Session = Depends(get_db), current_user: TokenData = _READ):
    """All vendors, by name. The vendor screen is a later module."""
    return db.query(Vendor).order_by(Vendor.name).all()

@router.post("/vendors", response_model=inventory_schemas.Vendor, status_code=status.HTTP_201_CREATED)
def create_vendor(
    vendor: inventory_schemas.VendorCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = _STAFF,
):
    """Add a vendor. Staff can, so a new shop never holds up the purchase sheet."""
    new_vendor = Vendor(**vendor.model_dump())
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)
    return new_vendor

@router.post("/transactions/usage", status_code=status.HTTP_201_CREATED)
def record_usage(
    usage: inventory_schemas.UsageCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = _STAFF,
):
    """Record usage transaction (stock reduction)."""
    transactions = []
    warnings = []
    
    for item_data in usage.items:
        item = db.query(InventoryItem).filter(InventoryItem.id == item_data.item_id).first()
        if not item:
            raise HTTPException(status_code=400, detail=f"Item ID {item_data.item_id} not found")
        if item_data.quantity <= 0:
            continue # Skip zero or negative usage
            
        previous_qty = item.current_quantity
        item.current_quantity -= item_data.quantity
        new_qty = item.current_quantity  # read back: a yes/no item stops at 0, not -3

        transaction = InventoryTransaction(
            item_id=item.id,
            transaction_type=TransactionType.USAGE,
            quantity=new_qty - previous_qty,  # negative for usage
            notes=item_data.notes,
            recorded_by=current_user.username,
            previous_quantity=previous_qty,
            new_quantity=new_qty
        )
        db.add(transaction)
        transactions.append(transaction)
        
        if item.is_low_stock:
            warnings.append({
                "item_id": item.id,
                "item_name": item.name,
                "message": "Now out" if item.is_presence
                else f"Now below threshold ({new_qty}/{item.min_threshold})"
            })
            
    db.commit()
    
    for t in transactions:
        db.refresh(t)
        
    return {
        "message": "Usage recorded successfully",
        "transactions": [
            {
                "id": t.id,
                "item_id": t.item_id,
                "item_name": t.item.name,
                "transaction_type": t.transaction_type,
                "quantity": t.quantity,
                "previous_quantity": t.previous_quantity,
                "new_quantity": t.new_quantity,
                "recorded_by": t.recorded_by,
                "created_at": t.created_at
            } for t in transactions
        ],
        "warnings": warnings
    }

@router.post("/transactions/adjustment", status_code=status.HTTP_201_CREATED)
def record_adjustment(
    adjustment: inventory_schemas.AdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = _STAFF,
):
    """Record inventory adjustment (correction)."""
    item = db.query(InventoryItem).filter(InventoryItem.id == adjustment.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    previous_qty = item.current_quantity
    item.current_quantity = adjustment.new_quantity
    new_qty = item.current_quantity  # read back: clamped to 1 or 0 for a yes/no item
    diff = new_qty - previous_qty

    transaction = InventoryTransaction(
        item_id=item.id,
        transaction_type=TransactionType.ADJUSTMENT,
        quantity=diff,
        notes=adjustment.notes,
        recorded_by=current_user.username,
        previous_quantity=previous_qty,
        new_quantity=new_qty
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return {
        "id": transaction.id,
        "item_id": transaction.item_id,
        "item_name": item.name,
        "transaction_type": transaction.transaction_type,
        "quantity": transaction.quantity,
        "previous_quantity": transaction.previous_quantity,
        "new_quantity": transaction.new_quantity,
        "recorded_by": transaction.recorded_by,
        "notes": transaction.notes,
        "created_at": transaction.created_at
    }

@router.post("/transactions/batch-adjustment", status_code=status.HTTP_201_CREATED)
def record_batch_adjustment(
    batch: inventory_schemas.BatchAdjustmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: TokenData = _STAFF,
):
    """
    Record multiple inventory adjustments at once (daily count).

    This endpoint is optimized for end-of-day inventory counts where
    staff updates quantities for many items at once. All adjustments
    are processed atomically - either all succeed or all fail.
    """
    # Validate all items exist first
    item_ids = [adj.item_id for adj in batch.adjustments]
    items = db.query(InventoryItem).filter(InventoryItem.id.in_(item_ids)).all()

    if len(items) != len(set(item_ids)):
        raise HTTPException(
            status_code=404,
            detail="One or more items not found"
        )

    # Create a map for quick lookup
    items_map = {item.id: item for item in items}

    # Process all adjustments
    created_transactions = []
    updated_items = []

    for adjustment in batch.adjustments:
        item = items_map.get(adjustment.item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item {adjustment.item_id} not found")

        previous_qty = item.current_quantity
        new_qty = _counted_value(item, adjustment.new_quantity)
        diff = new_qty - previous_qty

        # Skip if quantity hasn't changed
        if diff == 0:
            continue

        # Update item quantity
        item.current_quantity = new_qty
        updated_items.append(item)

        # Create transaction record
        notes = adjustment.notes or _count_note(item, previous_qty, new_qty)
        transaction = InventoryTransaction(
            item_id=item.id,
            transaction_type=TransactionType.ADJUSTMENT,
            quantity=diff,
            notes=notes,
            recorded_by=current_user.username,
            previous_quantity=previous_qty,
            new_quantity=new_qty
        )
        db.add(transaction)
        created_transactions.append({
            "item_id": item.id,
            "item_name": item.name,
            "previous_quantity": float(previous_qty),
            "new_quantity": float(new_qty),
            "difference": float(diff)
        })

    # Commit all changes atomically
    db.commit()

    # Schedule inventory report email as background task
    if settings_store.get_bool("smtp.enabled", False) and created_transactions:
        all_active_items = db.query(InventoryItem).filter(
            InventoryItem.is_active == True
        ).all()

        low_stock_data = []
        for item in all_active_items:
            if item.is_low_stock:
                pct = 0.0
                if float(item.min_threshold) > 0:
                    pct = (float(item.current_quantity) / float(item.min_threshold)) * 100
                low_stock_data.append({
                    "name": item.name,
                    "category_name": item.category.name if item.category else "Uncategorized",
                    "current_quantity": float(item.current_quantity),
                    "min_threshold": float(item.min_threshold),
                    "unit": item.unit,
                    "percentage_remaining": pct,
                })

        low_stock_data.sort(key=lambda x: x["percentage_remaining"])

        background_tasks.add_task(
            send_inventory_report,
            low_stock_items=low_stock_data,
            changes=created_transactions,
            recorded_by=current_user.username,
        )

    return {
        "success": True,
        "message": f"Updated {len(created_transactions)} items",
        "total_items_processed": len(batch.adjustments),
        "items_changed": len(created_transactions),
        "items_unchanged": len(batch.adjustments) - len(created_transactions),
        "recorded_by": current_user.username,
        "changes": created_transactions
    }

@router.get("/transactions", response_model=dict)
def get_transactions(
    item_id: Optional[int] = None,
    transaction_type: Optional[TransactionType] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: TokenData = _READ,
):
    """Get transaction history."""
    query = db.query(InventoryTransaction)
    
    if item_id:
        query = query.filter(InventoryTransaction.item_id == item_id)
    
    if transaction_type:
        query = query.filter(InventoryTransaction.transaction_type == transaction_type)
        
    total = query.count()
    transactions = query.order_by(desc(InventoryTransaction.created_at)).offset(offset).limit(limit).all()
    
    result_transactions = []
    for t in transactions:
        # Convert ORM model to Pydantic model using v2 syntax
        t_model = inventory_schemas.InventoryTransaction.model_validate(t, from_attributes=True)
        # Convert to dict to add item_name field
        t_dict = t_model.model_dump()
        if t.item:
            t_dict['item_name'] = t.item.name
            t_dict['count_mode'] = t.item.count_mode
        result_transactions.append(t_dict)
        
    return {
        "transactions": result_transactions,
        "total": total,
        "limit": limit,
        "offset": offset
    }


# ============================================================================
# Nightly count
# ============================================================================

def _counted_value(item: InventoryItem, value: Decimal) -> Decimal:
    """What a count line means for this item: a yes/no answer is 1 or 0."""
    return presence_quantity(value) if item.is_presence else value


def _count_note(item: InventoryItem, previous: Decimal, new: Decimal) -> str:
    if item.is_presence:
        return "Daily count: ran out" if new == 0 else "Daily count: have it again"
    return f"Daily count: {previous} → {new}"


def _count_summary(count: InventoryCount) -> dict:
    return inventory_schemas.CountSummary.model_validate(count, from_attributes=True).model_dump()


@router.post("/counts", response_model=inventory_schemas.CountResult, status_code=status.HTTP_201_CREATED)
def save_count(
    payload: inventory_schemas.CountCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: TokenData = _STAFF,
):
    """
    Save a nightly stock count in one step.

    Every active item gets a line: counted and equal to the system quantity is
    "checked", counted and different is "changed" (stock is adjusted and an
    ADJUSTMENT transaction recorded), and anything not counted is "skipped".
    Lines for items that no longer exist or were deactivated are ignored, so a
    count started before a master-data edit can still be saved.
    """
    counted = {line.item_id: line.counted_quantity for line in payload.lines}
    items = (
        db.query(InventoryItem)
        .filter(InventoryItem.is_active == True)
        .order_by(InventoryItem.sort_order, InventoryItem.id)
        .all()
    )

    count = InventoryCount(
        business_date=count_night(),
        counted_by=current_user.username,
        items_total=len(items),
        items_checked=0,
        items_changed=0,
        items_skipped=0,
    )
    changes, skipped_names = [], []

    for item in items:
        previous = item.current_quantity
        new = counted.get(item.id)
        if new is not None:
            new = _counted_value(item, new)
        if new is None:
            status_ = CountLineStatus.SKIPPED
            count.items_skipped += 1
            skipped_names.append(item.name)
        elif new == previous:
            status_ = CountLineStatus.CHECKED
            count.items_checked += 1
        else:
            status_ = CountLineStatus.CHANGED
            count.items_changed += 1
            item.current_quantity = new
            db.add(InventoryTransaction(
                item_id=item.id,
                transaction_type=TransactionType.ADJUSTMENT,
                quantity=new - previous,
                notes=_count_note(item, previous, new),
                recorded_by=current_user.username,
                previous_quantity=previous,
                new_quantity=new,
            ))
            changes.append({
                "item_id": item.id,
                "item_name": item.name,
                "previous_quantity": float(previous),
                "new_quantity": float(new),
                "difference": float(new - previous),
            })
        count.lines.append(InventoryCountLine(
            item_id=item.id,
            status=status_.value,
            previous_quantity=previous,
            counted_quantity=new,
        ))

    db.add(count)
    db.commit()
    db.refresh(count)

    # Only claim an email when one will actually be attempted.
    emailed = settings_store.get_bool("smtp.enabled", False) and bool(
        settings_store.get("smtp.report_emails", "").strip()
    )
    if emailed:
        low_stock_data = [
            {
                "name": item.name,
                "category_name": item.category.name if item.category else "Uncategorized",
                "current_quantity": float(item.current_quantity),
                "min_threshold": float(item.min_threshold),
                "unit": item.unit,
                "percentage_remaining": (
                    float(item.current_quantity) / float(item.min_threshold) * 100
                    if float(item.min_threshold) > 0 else 0.0
                ),
            }
            for item in items if item.is_low_stock
        ]
        low_stock_data.sort(key=lambda x: x["percentage_remaining"])
        background_tasks.add_task(
            send_inventory_report,
            low_stock_items=low_stock_data,
            changes=changes,
            recorded_by=current_user.username,
            summary={
                "checked": count.items_checked,
                "changed": count.items_changed,
                "skipped": count.items_skipped,
                "skipped_names": skipped_names,
            },
        )

    return {
        **_count_summary(count),
        "changes": changes,
        "skipped_item_names": skipped_names,
        "emailed": emailed,
    }


@router.get("/counts/today", response_model=Optional[inventory_schemas.CountSummary])
def get_todays_count(db: Session = Depends(get_db), current_user: TokenData = _READ):
    """The latest count for tonight (before 04:00 counts as last night), or null."""
    count = (
        db.query(InventoryCount)
        .filter(InventoryCount.business_date == count_night())
        .order_by(desc(InventoryCount.id))
        .first()
    )
    return _count_summary(count) if count else None


@router.get("/counts", response_model=List[inventory_schemas.CountSummary])
def list_counts(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: TokenData = _READ,
):
    """Recent counts, newest first."""
    counts = db.query(InventoryCount).order_by(desc(InventoryCount.id)).limit(limit).all()
    return [_count_summary(count) for count in counts]
