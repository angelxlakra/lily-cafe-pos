from typing import Literal, Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field
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

    class Config:
        from_attributes = True

# Transaction Schemas
class InventoryTransactionBase(BaseModel):
    item_id: int
    quantity: Decimal
    notes: Optional[str] = Field(None, max_length=500)

class PurchaseCreate(BaseModel):
    items: List[InventoryTransactionBase]

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
