from typing import Optional, List
from datetime import datetime
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
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Item Schemas
class InventoryItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    unit: str = Field(..., min_length=1, max_length=20)
    min_threshold: Decimal = Field(default=0, ge=0)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    category_id: Optional[int] = None

class InventoryItemCreate(InventoryItemBase):
    current_quantity: Decimal = Field(default=0, ge=0)

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    min_threshold: Optional[Decimal] = Field(None, ge=0)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    category_id: Optional[int] = None
    is_active: Optional[bool] = None

class InventoryItem(InventoryItemBase):
    id: int
    current_quantity: Decimal
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    category_name: Optional[str] = None # Computed in API
    is_low_stock: bool # Computed property

    class Config:
        orm_mode = True

# Transaction Schemas
class InventoryTransactionBase(BaseModel):
    item_id: int
    quantity: Decimal
    notes: Optional[str] = Field(None, max_length=500)

class PurchaseCreate(BaseModel):
    items: List[InventoryTransactionBase]

class UsageCreate(BaseModel):
    items: List[InventoryTransactionBase]
    recorded_by: str

class AdjustmentCreate(BaseModel):
    item_id: int
    new_quantity: Decimal = Field(..., ge=0)
    notes: str = Field(..., min_length=1, max_length=500)

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
        orm_mode = True

class LowStockItem(InventoryItem):
    percentage_remaining: float
