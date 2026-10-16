// Dish costing, as /api/v1/costing returns it. Money and quantities arrive
// as decimal strings; read them with Number() at the edge, never add strings.

type Num = number | string;

export type OverheadKind = 'packaging' | 'labour' | 'fixed' | 'wastage';
export type OverheadMode = 'amount' | 'percent';

/** Why an ingredient line isn't costed. Absent when it is. */
export type GapReason = 'retired' | 'needs_pack_size' | 'unknown_unit' | 'no_price';

export interface OverheadOverride {
  mode: OverheadMode | null;
  value: Num | null;
}

export interface CostingIngredientIn {
  inventory_item_id: number;
  quantity: Num;
  unit: string;
}

export interface DishCostingIn {
  menu_item_id: number;
  yield_units: Num;
  target_margin_percent?: Num | null;
  notes?: string | null;
  ingredients: CostingIngredientIn[];
  packaging?: OverheadOverride;
  labour?: OverheadOverride;
  fixed?: OverheadOverride;
  wastage?: OverheadOverride;
}

export interface IngredientLine {
  inventory_item_id: number;
  name: string;
  quantity: Num;
  unit: string;
  stock_unit: string;
  unit_price: Num;
  line_cost: Num;
  share_percent: Num | null;
  price_missing: boolean;
  is_active: boolean;
  unit_error: boolean;
  needs_pack_size: boolean;
  price_source: 'purchase' | 'typed' | null;
  price_as_of: string | null;
  reason: GapReason | null;
  /** A yes/no item: on the recipe, covered by overheads, never a gap. */
  is_presence: boolean;
}

export interface OverheadLine {
  kind: OverheadKind;
  mode: OverheadMode;
  value: Num;
  amount: Num;
  percent: Num | null;
  /** True when the dish uses the cafe-wide default. */
  inherited: boolean;
}

export interface CostBreakdown {
  ingredients: IngredientLine[];
  overheads: OverheadLine[];
  raw_material_cost: Num;
  overhead_cost: Num;
  total_cost: Num;
  yield_units: Num;
  raw_cost_per_unit: Num;
  cost_per_unit: Num;
  /** In rupees (the menu stores paise). */
  selling_price: Num | null;
  margin_amount: Num | null;
  margin_percent: Num | null;
  food_cost_percent: Num | null;
  target_margin_percent: Num | null;
  /** Rounded up to the next ₹10; null until every line is costed. */
  suggested_price: Num | null;
  is_complete: boolean;
  warnings: string[];
}

export interface DishCosting {
  id: number;
  menu_item_id: number;
  menu_item_name: string;
  yield_units: Num;
  target_margin_percent: Num | null;
  notes: string | null;
  packaging: OverheadOverride;
  labour: OverheadOverride;
  fixed: OverheadOverride;
  wastage: OverheadOverride;
  ingredients: CostingIngredientIn[];
  breakdown: CostBreakdown;
}

export interface DishCostingSummary {
  id: number;
  menu_item_id: number;
  menu_item_name: string;
  cost_per_unit: Num;
  selling_price: Num | null;
  margin_percent: Num | null;
  target_margin_percent: Num;
  below_target: boolean;
  is_complete: boolean;
  gap_count: number;
}

export interface CostingDefaults {
  packaging: OverheadOverride;
  labour: OverheadOverride;
  fixed: OverheadOverride;
  wastage: OverheadOverride;
  target_margin_percent: Num;
}
