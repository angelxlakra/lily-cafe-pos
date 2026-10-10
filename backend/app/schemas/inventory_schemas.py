from typing import Literal, Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator
from app.models.inventory_models import TransactionType

# Category Schemas
class InventoryCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class InventoryCategoryCreate(InventoryCategoryBase):
    pass

class InventoryCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)

class InventoryCategory(InventoryCategoryBase):
    id: int
    sort_order: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Item Schemas
class InventoryItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    unit: str = Field(..., min_length=1, max_length=20)
    min_threshold: Decimal = Field(default=0, ge=0)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    category_id: Optional[int] = None
    count_mode: Literal["number", "presence"] = "number"
    pack_size: Optional[Decimal] = Field(None, gt=0)
    pack_unit: Optional[str] = Field(None, min_length=1, max_length=20)

class InventoryItemCreate(InventoryItemBase):
    current_quantity: Decimal = Field(default=0, ge=0)

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    min_threshold: Optional[Decimal] = Field(None, ge=0)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    category_id: Optional[int] = None
    is_active: Optional[bool] = None
    count_mode: Optional[Literal["number", "presence"]] = None
    pack_size: Optional[Decimal] = Field(None, gt=0)
    pack_unit: Optional[str] = Field(None, min_length=1, max_length=20)

class BulkItemUpdate(InventoryItemUpdate):
    """One changed row from the setup grid. Only the fields sent are changed."""
    id: int
    # Stock is state, not configuration: a change here is recorded as an adjustment.
    current_quantity: Optional[Decimal] = Field(None, ge=0)

class BulkItemsUpdate(BaseModel):
    items: List[BulkItemUpdate] = Field(..., min_length=1)

class InventoryItem(InventoryItemBase):
    id: int
    current_quantity: Decimal
    is_active: bool
    sort_order: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    category_name: Optional[str] = None # Computed in API
    is_low_stock: bool # Computed property
    needs_setup: bool = False
    # Resolved price (app/utils/pricing.py): latest paid purchase, else the
    # typed cost_per_unit (> 0), else None. Per the item's own unit.
    current_price: Optional[Decimal] = None
    price_source: Optional[Literal["purchase", "typed"]] = None
    price_as_of: Optional[datetime] = None  # purchase date; None for a typed price

    class Config:
        from_attributes = True

# Transaction Schemas
class InventoryTransactionBase(BaseModel):
    item_id: int
    quantity: Decimal
    notes: Optional[str] = Field(None, max_length=500)

class PurchaseLine(BaseModel):
    """One row of the daily purchase sheet: item · how much · what it cost."""
    item_id: int
    quantity: Decimal  # in the item's own unit
    # The TOTAL paid for the line ("4 kg for ₹480"), not a unit price.
    # Optional so older clients still record stock; 0 is a gift and needs a note.
    total_amount: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    vendor_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=500)
    # The sheet's "Purchased" column: 2 packs of 1 kg. quantity is still the total.
    pack_count: Optional[Decimal] = Field(None, gt=0)

    @model_validator(mode="after")
    def _gift_needs_note(self):
        if self.total_amount is not None and self.total_amount == 0 and not (self.notes or "").strip():
            raise ValueError("A purchase of ₹0 needs a note saying why (e.g. free from the vendor)")
        return self

class PurchaseCreate(BaseModel):
    items: List[PurchaseLine] = Field(..., min_length=1)
    # Default vendor for lines that don't name one — one bill, one vendor.
    vendor_id: Optional[int] = None

class PurchaseEdit(BaseModel):
    """A same-day correction to one purchase line. Only the fields sent change."""
    quantity: Optional[Decimal] = Field(None, gt=0)
    total_amount: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    vendor_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=500)
    pack_count: Optional[Decimal] = Field(None, gt=0)

class DayEndCount(BaseModel):
    counted_quantity: Decimal = Field(..., ge=0)

class QuickItemCreate(BaseModel):
    """An item bought but not in the list: just enough to log the purchase."""
    name: str = Field(..., min_length=1, max_length=200)
    unit: str = Field(..., min_length=1, max_length=20)

class PurchaseCheckLine(BaseModel):
    item_id: int
    quantity: Decimal
    total_amount: Optional[Decimal] = Field(None, ge=0)

class PurchaseCheck(BaseModel):
    items: List[PurchaseCheckLine] = Field(..., min_length=1)

class PriceCheckResult(BaseModel):
    """Enough for the sheet to ask "chicken was ₹320/kg, this is ₹520/kg — right?"."""
    item_id: int
    item_name: str
    unit: str
    unit_price: Optional[Decimal]         # this line: total ÷ quantity
    previous_price: Optional[Decimal]     # the item's current resolved price
    previous_source: Optional[Literal["purchase", "typed"]]
    previous_as_of: Optional[datetime]
    change: Optional[Decimal]             # 0.625 = 62.5% up
    is_jump: bool

# Vendors — just the table for now; the vendor screen comes later.
class VendorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    notes: Optional[str] = Field(None, max_length=500)

class Vendor(VendorCreate):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UsageCreate(BaseModel):
    items: List[InventoryTransactionBase]
    # Accepted for backward compatibility but ignored — the server records the
    # authenticated user, so the client cannot claim to be somebody else.
    recorded_by: Optional[str] = Field(None, max_length=100, deprecated=True)

class AdjustmentCreate(BaseModel):
    item_id: int
    new_quantity: Decimal = Field(..., ge=0)
    notes: Optional[str] = Field(None, max_length=500)

class AdjustmentItem(BaseModel):
    """Single item adjustment for batch operations."""
    item_id: int
    new_quantity: Decimal = Field(..., ge=0)
    notes: Optional[str] = Field(None, max_length=500)

class BatchAdjustmentCreate(BaseModel):
    """Batch adjustment for daily inventory count."""
    adjustments: List[AdjustmentItem]
    # Accepted for backward compatibility but ignored — the server records the
    # authenticated user, so the client cannot claim to be somebody else.
    recorded_by: Optional[str] = Field(None, max_length=100, deprecated=True)

class InventoryTransaction(BaseModel):
    id: int
    item_id: int
    item_name: Optional[str] = None # Computed
    transaction_type: TransactionType
    quantity: Decimal
    notes: Optional[str] = None
    recorded_by: str
    previous_quantity: Decimal
    new_quantity: Decimal
    created_at: datetime
    total_amount: Optional[Decimal] = None
    vendor_id: Optional[int] = None

    class Config:
        from_attributes = True

class LowStockItem(InventoryItem):
    percentage_remaining: float


class SortOrderUpdate(BaseModel):
    """Ids in the order they should appear in the nightly count."""
    ids: List[int] = Field(..., min_length=1)


# Nightly count
class CountLineCreate(BaseModel):
    item_id: int
    # None = not counted (skipped). Equal to the system quantity = checked.
    counted_quantity: Optional[Decimal] = Field(None, ge=0)


class CountCreate(BaseModel):
    lines: List[CountLineCreate]


class CountChange(BaseModel):
    item_id: int
    item_name: str
    previous_quantity: float
    new_quantity: float
    difference: float


class CountSummary(BaseModel):
    id: int
    business_date: date
    counted_by: str
    created_at: Optional[datetime] = None
    items_total: int
    items_checked: int
    items_changed: int
    items_skipped: int

    class Config:
        from_attributes = True


class CountResult(CountSummary):
    changes: List[CountChange]
    skipped_item_names: List[str]
    emailed: bool
