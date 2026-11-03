"""Pydantic schemas for dish costing."""

from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

# amount: ₹ for the whole batch; each: ₹ per portion (a box per cookie); percent: of the batch's raw material.
OverheadMode = Literal["amount", "each", "percent"]
OverheadKind = Literal["packaging", "labour", "fixed", "wastage"]


class OverheadOverride(BaseModel):
    mode: Optional[OverheadMode] = None
    value: Optional[Decimal] = Field(None, ge=0)


class CostingIngredientIn(BaseModel):
    inventory_item_id: int
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)


class DishCostingIn(BaseModel):
    # A dish (menu_item_id) or a kitchen-made item (inventory_item_id): exactly one.
    menu_item_id: Optional[int] = None
    inventory_item_id: Optional[int] = None
    # A made item may leave it out: the batch then makes the sum of its lines.
    yield_units: Optional[Decimal] = Field(None, gt=0)
    target_margin_percent: Optional[Decimal] = Field(None, ge=0, lt=100)
    notes: Optional[str] = Field(None, max_length=500)
    ingredients: List[CostingIngredientIn] = Field(default_factory=list)
    packaging: OverheadOverride = Field(default_factory=OverheadOverride)
    labour: OverheadOverride = Field(default_factory=OverheadOverride)
    fixed: OverheadOverride = Field(default_factory=OverheadOverride)
    wastage: OverheadOverride = Field(default_factory=OverheadOverride)

    @model_validator(mode="after")
    def _one_subject(self):
        if (self.menu_item_id is None) == (self.inventory_item_id is None):
            raise ValueError("Give either menu_item_id or inventory_item_id")
        if self.menu_item_id is not None and self.yield_units is None:
            raise ValueError("yield_units is required for a dish")
        return self


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
    unit_error: bool = False
    needs_pack_size: bool = False
    price_source: Optional[Literal["purchase", "typed", "recipe"]] = None
    price_as_of: Optional[datetime] = None
    reason: Optional[Literal["retired", "needs_pack_size", "unknown_unit", "no_price"]] = None
    is_presence: bool = False


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


class UsedIn(BaseModel):
    costing_id: int
    name: str
    kind: Literal["dish", "made"]


class DishCostingOut(BaseModel):
    id: int
    menu_item_id: Optional[int] = None
    menu_item_name: Optional[str] = None
    inventory_item_id: Optional[int] = None
    kind: Literal["dish", "made"] = "dish"
    # The dish's or the made item's name, and the made item's unit.
    name: str = ""
    unit: Optional[str] = None
    used_in: List[UsedIn] = Field(default_factory=list)
    yield_units: Decimal
    # Made items: the lines summed in the item's unit, or None if one doesn't convert.
    auto_yield: Optional[Decimal] = None
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
    # Ingredients that aren't costed yet; 0 when is_complete.
    gap_count: int = 0


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
    via: List[str] = []   # kitchen-made items the change passed through to reach this dish


class MadeImpact(BaseModel):
    item_id: int
    name: str
    unit: str
    cost_before: Decimal
    cost_after: Decimal


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


class OverviewRow(BaseModel):
    kind: Literal["dish", "made"]
    costing_id: Optional[int] = None
    menu_item_id: Optional[int] = None
    inventory_item_id: Optional[int] = None
    name: str
    category: Optional[str] = None
    cost_per_unit: Optional[Decimal] = None
    unit: Optional[str] = None
    selling_price: Optional[Decimal] = None
    margin_percent: Optional[Decimal] = None
    target_margin_percent: Optional[Decimal] = None
    margin_ceiling: Optional[Decimal] = None   # best margin possible while prices are missing
    missing_count: int = 0
    cost_last_week: Optional[Decimal] = None
    status: Literal["below_target", "missing_prices", "no_recipe", "on_target", "costed"]


class OverviewTotals(BaseModel):
    below_target: int
    missing_prices: int
    no_recipe: int
    average_margin: Optional[Decimal] = None


class Overview(BaseModel):
    rows: List[OverviewRow]
    totals: OverviewTotals
