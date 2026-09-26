"""What the day's sales used of each inventory item, from recipes.

Used = Σ over the night's non-canceled order lines of
       dishes sold × ingredient quantity ÷ recipe yield, in the item's own unit.
The night is the purchase sheet's day (04:00 local to 04:00 the next), the
same window as its purchases and its count; a sale at 00:30 after close
belongs to the night it was sold in, not to the next calendar day.
An ingredient in a unit the converter can't reach the item's unit from
(ml of a sauce counted in bottles) is bridged by the item's pack size
(1 bottle = 700 ml). An item no recipe mentions has no answer (None), which
is different from 0: "not worked out" is not "none used".
"""

from datetime import date
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.business_day import night_utc_bounds
from app.models.costing_models import DishCosting, DishCostingIngredient
from app.models.inventory_models import InventoryItem
from app.models.models import Order, OrderItem, OrderStatus
from app.utils.units import IncompatibleUnitError, compatible, convert


def per_portion_in_item_unit(ingredient: DishCostingIngredient, item: InventoryItem, yield_units) -> Optional[Decimal]:
    """One portion's use of an item, in the item's unit, or None if no bridge exists."""
    quantity = Decimal(ingredient.quantity) / Decimal(yield_units or 1)
    try:
        return convert(quantity, ingredient.unit, item.unit)
    except IncompatibleUnitError:
        pass
    if item.pack_size and item.pack_unit and compatible(ingredient.unit, item.pack_unit):
        return convert(quantity, ingredient.unit, item.pack_unit) / Decimal(item.pack_size)
    return None


def used_on(db: Session, day: date, items: Iterable[InventoryItem]) -> dict[int, Optional[Decimal]]:
    """Each item's use over one count night; None where no recipe says."""
    items = {item.id: item for item in items}
    used: dict[int, Optional[Decimal]] = {item_id: None for item_id in items}
    if not items:
        return used

    start, end = night_utc_bounds(day)
    sold = dict(
        db.query(OrderItem.menu_item_id, func.sum(OrderItem.quantity))
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status != OrderStatus.CANCELED, Order.created_at >= start, Order.created_at < end)
        .group_by(OrderItem.menu_item_id)
        .all()
    )
    rows = (
        db.query(DishCostingIngredient, DishCosting.menu_item_id, DishCosting.yield_units)
        .join(DishCosting, DishCosting.id == DishCostingIngredient.costing_id)
        .filter(DishCostingIngredient.inventory_item_id.in_(items))
        .all()
    )
    for ingredient, menu_item_id, yield_units in rows:
        item_id = ingredient.inventory_item_id
        portion = per_portion_in_item_unit(ingredient, items[item_id], yield_units)
        if portion is None:
            continue  # a recipe we can't convert says nothing, so stays unknown
        used[item_id] = (used[item_id] or Decimal(0)) + portion * Decimal(sold.get(menu_item_id, 0))
    return used
