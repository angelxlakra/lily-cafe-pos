"""Where an inventory item's price comes from.

One order of precedence, no blending:

1. The unit price of the item's most recent purchase that was paid for
   (total_amount > 0): total ÷ quantity, in the item's own unit.
2. Otherwise the typed ``cost_per_unit``, if it is above 0.
3. Otherwise no price. A stored 0 is a placeholder, not "free" — 98 live
   items were created at 0.00.

A ₹0 purchase is a gift ("the vendor threw in coriander"). It raises stock
but says nothing about what the item costs, so it never becomes the price.

Nothing here is stored: the price is derived from the purchase log on read,
so it cannot drift from it.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inventory_models import InventoryItem, InventoryTransaction, TransactionType

# A new purchase more than this far from the current price is worth a
# "chicken was ₹320/kg, this is ₹520/kg — right?" at entry.
PRICE_JUMP_THRESHOLD = Decimal("0.30")

SOURCE_PURCHASE = "purchase"
SOURCE_TYPED = "typed"

_PRICE_PLACES = Decimal("0.0001")


def unit_price(total_amount, quantity) -> Optional[Decimal]:
    """What one unit cost on this purchase line.

    None when no total was entered, or when the quantity is not positive
    (a yes/no item bought while already in stock records a 0 movement).
    A ₹0 gift gives 0 — true for the line, though never used as the price.
    """
    if total_amount is None or quantity is None:
        return None
    quantity = Decimal(quantity)
    if quantity <= 0:
        return None
    return (Decimal(total_amount) / quantity).quantize(_PRICE_PLACES)


@dataclass(frozen=True)
class ResolvedPrice:
    price: Optional[Decimal]
    source: Optional[str]           # "purchase", "typed" or None
    as_of: Optional[datetime]       # when the purchase was made; None for typed

    def as_dict(self) -> dict:
        return {"current_price": self.price, "price_source": self.source, "price_as_of": self.as_of}


NO_PRICE = ResolvedPrice(None, None, None)


def _typed(item: InventoryItem) -> ResolvedPrice:
    if item.cost_per_unit is not None and Decimal(item.cost_per_unit) > 0:
        return ResolvedPrice(Decimal(item.cost_per_unit), SOURCE_TYPED, None)
    return NO_PRICE


def _priced_purchases(db: Session):
    return db.query(InventoryTransaction).filter(
        InventoryTransaction.transaction_type == TransactionType.PURCHASE,
        InventoryTransaction.total_amount > 0,
        InventoryTransaction.quantity > 0,
    )


def latest_priced_purchases(db: Session, item_ids: Iterable[int]) -> dict[int, InventoryTransaction]:
    """The most recent paid purchase per item, in one query.

    "Most recent" is the highest id: ids are assigned in insert order, and
    unlike created_at (second resolution in SQLite) they never tie when the
    same item appears twice on one sheet.
    """
    ids = list(set(item_ids))
    if not ids:
        return {}
    latest_ids = (
        _priced_purchases(db)
        .filter(InventoryTransaction.item_id.in_(ids))
        .with_entities(func.max(InventoryTransaction.id))
        .group_by(InventoryTransaction.item_id)
        .subquery()
    )
    rows = db.query(InventoryTransaction).filter(InventoryTransaction.id.in_(latest_ids.select())).all()
    return {t.item_id: t for t in rows}


def resolve(item: InventoryItem, latest_purchase: Optional[InventoryTransaction]) -> ResolvedPrice:
    """Apply the precedence to an item and its latest paid purchase (if any)."""
    if item.is_presence:
        return NO_PRICE  # a yes/no item has no quantity to price against
    if latest_purchase is not None:
        price = unit_price(latest_purchase.total_amount, latest_purchase.quantity)
        if price is not None and price > 0:
            return ResolvedPrice(price, SOURCE_PURCHASE, latest_purchase.created_at)
    return _typed(item)


def resolve_many(db: Session, items: Iterable[InventoryItem]) -> dict[int, ResolvedPrice]:
    items = list(items)
    latest = latest_priced_purchases(db, (i.id for i in items))
    return {i.id: resolve(i, latest.get(i.id)) for i in items}


def resolve_one(db: Session, item: InventoryItem) -> ResolvedPrice:
    return resolve_many(db, [item])[item.id]


def price_change(previous: Optional[Decimal], new: Optional[Decimal]) -> Optional[Decimal]:
    """Fractional change from previous to new (0.625 = 62.5% up), or None."""
    if previous is None or new is None or previous <= 0:
        return None
    return ((new - previous) / previous).quantize(_PRICE_PLACES)


def is_price_jump(previous: Optional[Decimal], new: Optional[Decimal]) -> bool:
    change = price_change(previous, new)
    return change is not None and abs(change) > PRICE_JUMP_THRESHOLD
