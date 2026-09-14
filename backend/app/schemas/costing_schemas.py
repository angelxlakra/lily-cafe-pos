"""Pydantic schemas for dish costing."""

from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

OverheadMode = Literal["amount", "percent"]
OverheadKind = Literal["packaging", "labour", "fixed", "wastage"]


class OverheadOverride(BaseModel):
    mode: Optional[OverheadMode] = None
    value: Optional[Decimal] = Field(None, ge=0)


class CostingIngredientIn(BaseModel):
    inventory_item_id: int
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)


class DishCostingIn(BaseModel):
    menu_item_id: int
    yield_units: Decimal = Field(..., gt=0)
    target_margin_percent: Optional[Decimal] = Field(None, ge=0, lt=100)
    notes: Optional[str] = Field(None, max_length=500)
    ingredients: List[CostingIngredientIn] = Field(default_factory=list)
    packaging: OverheadOverride = Field(default_factory=OverheadOverride)
    labour: OverheadOverride = Field(default_factory=OverheadOverride)
    fixed: OverheadOverride = Field(default_factory=OverheadOverride)
    wastage: OverheadOverride = Field(default_factory=OverheadOverride)


class IngredientLineOut(BaseModel):
    inventory_item_id: int
    name: str
    quantity: Decimal
    unit: str
    stock_unit: str
    unit_price: Decimal
    line_cost: Decimal
    share_percent: Optional[Decimal]
    price_missing: bool
    is_active: bool


class OverheadLineOut(BaseModel):
    kind: OverheadKind
    mode: OverheadMode
    value: Decimal
    amount: Decimal
    percent: Optional[Decimal]
    inherited: bool


class CostBreakdownOut(BaseModel):
    ingredients: List[IngredientLineOut]
    overheads: List[OverheadLineOut]
    raw_material_cost: Decimal
    overhead_cost: Decimal
    total_cost: Decimal
    yield_units: Decimal
    raw_cost_per_unit: Decimal
    cost_per_unit: Decimal
    selling_price: Optional[Decimal]
    margin_amount: Optional[Decimal]
    margin_percent: Optional[Decimal]
    food_cost_percent: Optional[Decimal]
    target_margin_percent: Optional[Decimal]
    suggested_price: Optional[Decimal]
    is_complete: bool
    warnings: List[str]


class DishCostingOut(BaseModel):
    id: int
    menu_item_id: int
    menu_item_name: str
    yield_units: Decimal
    target_margin_percent: Optional[Decimal]
    notes: Optional[str]
    packaging: OverheadOverride
    labour: OverheadOverride
    fixed: OverheadOverride
    wastage: OverheadOverride
    ingredients: List[CostingIngredientIn]
    breakdown: CostBreakdownOut

    class Config:
        from_attributes = True


class DishCostingSummary(BaseModel):
    id: int
    menu_item_id: int
    menu_item_name: str
    cost_per_unit: Decimal
    selling_price: Optional[Decimal]
    margin_percent: Optional[Decimal]
    target_margin_percent: Decimal
    below_target: bool
    is_complete: bool


class PriceChange(BaseModel):
    inventory_item_id: int
    new_cost_per_unit: Decimal = Field(..., ge=0)


class RepriceRequest(BaseModel):
    prices: List[PriceChange]


class DishImpact(BaseModel):
    costing_id: int
    menu_item_name: str
    cost_before: Decimal
    cost_after: Decimal
    margin_before: Optional[Decimal]
    margin_after: Optional[Decimal]
    crosses_below_target: bool


class RepricePreview(BaseModel):
    affected_dishes: List[DishImpact]
    unaffected_count: int


class DefaultsOut(BaseModel):
    packaging: OverheadOverride
    labour: OverheadOverride
    fixed: OverheadOverride
    wastage: OverheadOverride
    target_margin_percent: Decimal


class ApplyPriceIn(BaseModel):
    price: Decimal = Field(..., gt=0)
