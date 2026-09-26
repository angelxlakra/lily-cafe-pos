export interface InventoryCategory {
  id: number;
  name: string;
  sort_order: number;
  created_at: string;
  updated_at?: string;
}

export interface InventoryCategoryCreate {
  name: string;
}

export interface InventoryCategoryUpdate {
  name?: string;
}

export interface InventoryItem {
  id: number;
  name: string;
  unit: string;
  current_quantity: number;
  min_threshold: number;
  cost_per_unit?: number;
  category_id?: number;
  category_name?: string;
  is_active: boolean;
  is_low_stock: boolean;
  sort_order: number;
  count_mode: CountMode;
  pack_size?: number | null;
  pack_unit?: string | null;
  /** Added inline from the purchase sheet; the owner still has to configure it. */
  needs_setup?: boolean;
  /** Latest paid purchase's unit price, else the typed price; per the item's unit. */
  current_price?: number | null;
  price_source?: 'purchase' | 'typed' | null;
  created_at: string;
  updated_at?: string;
}

/** Counted with a number, or answered yes/no. */
export type CountMode = 'number' | 'presence';

export interface InventoryItemCreate {
  name: string;
  unit: string;
  current_quantity: number;
  min_threshold: number;
  /** null = no price. Never send 0 for "not set". */
  cost_per_unit?: number | null;
  category_id?: number;
}

export interface InventoryItemUpdate {
  name?: string;
  unit?: string;
  min_threshold?: number;
  cost_per_unit?: number | null;
  category_id?: number | null;
  is_active?: boolean;
  count_mode?: CountMode;
  pack_size?: number | null;
  pack_unit?: string | null;
}

/** One changed row from the setup grid; only the fields sent change. */
export interface BulkItemUpdate extends InventoryItemUpdate {
  id: number;
  current_quantity?: number;
}

export interface LowStockItem extends InventoryItem {
  percentage_remaining: number;
}

export type TransactionType = 'PURCHASE' | 'USAGE' | 'ADJUSTMENT';

export interface InventoryTransaction {
  id: number;
  item_id: number;
  item_name?: string;
  transaction_type: TransactionType;
  quantity: number;
  notes?: string;
  recorded_by: string;
  previous_quantity: number;
  new_quantity: number;
  created_at: string;
  /** The item's current mode; a yes/no item's movements read "had it → out". */
  count_mode?: CountMode;
}

export interface PurchaseItem {
  item_id: number;
  quantity: number;
  /** The TOTAL paid for the line, never a unit price. 0 is a gift and needs notes. */
  total_amount?: number | null;
  vendor_id?: number | null;
  notes?: string;
  pack_count?: number;
}

export interface PurchaseCreate {
  items: PurchaseItem[];
}

/** One saved line on a day's purchase sheet. Money comes back as strings (Decimal). */
export interface Purchase {
  id: number;
  item_id: number;
  item_name: string;
  unit: string;
  quantity: number | string;
  total_amount: number | string | null;
  unit_price: number | string | null;
  vendor_id: number | null;
  vendor_name: string | null;
  notes: string | null;
  /** How many were bought; quantity ÷ pack_count is the unit quantity. Null on old rows. */
  pack_count: number | string | null;
  recorded_by: string;
  created_at: string;
}

/** The owners' columns for one item on a day's sheet, in the item's unit. Null = not worked out. */
export interface DayItemColumns {
  opening: number | string;
  bought: number | string;
  used: number | string | null;
  remaining: number | string | null;
  day_end: number | string | null;
  wastage: number | string | null;
}

export interface PurchaseDay {
  business_date: string;
  purchases: Purchase[];
  total_amount: number | string;
  unpriced: number;
  items: Record<string, DayItemColumns>;
  /** Today's sheet; past days are read-only (and owner-only). */
  editable: boolean;
}

export interface Vendor {
  id: number;
  name: string;
}

export interface UsageItem {
  item_id: number;
  quantity: number;
  notes?: string;
}

export interface UsageCreate {
  items: UsageItem[];
}

export interface AdjustmentCreate {
  item_id: number;
  new_quantity: number;
  notes?: string;
}

export interface AdjustmentItem {
  item_id: number;
  new_quantity: number;
  notes?: string;
}

export interface BatchAdjustmentCreate {
  adjustments: AdjustmentItem[];
  recorded_by: string;
}

export interface BatchAdjustmentResponse {
  success: boolean;
  message: string;
  total_items_processed: number;
  items_changed: number;
  items_unchanged: number;
  recorded_by: string;
  changes: Array<{
    item_id: number;
    item_name: string;
    previous_quantity: number;
    new_quantity: number;
    difference: number;
  }>;
}

export interface CategorizedItems {
  [categoryId: number]: {
    category: InventoryCategory | null;
    items: InventoryItem[];
  };
}

export interface InventoryItemsResponse {
  items: InventoryItem[];
  total: number;
  low_stock_count: number;
}

export interface LowStockResponse {
  low_stock_items: LowStockItem[];
  count: number;
}

export interface TransactionsResponse {
  transactions: InventoryTransaction[];
  total: number;
  limit: number;
  offset: number;
}

// Nightly count

/** One category's items, in the owner-set count order. */
export interface CountSheetGroup {
  category: InventoryCategory | null;
  items: InventoryItem[];
}

export interface CountLine {
  item_id: number;
  /** null = not counted (skipped). */
  counted_quantity: number | null;
}

export interface CountSummary {
  id: number;
  business_date: string;
  counted_by: string;
  created_at: string | null;
  items_total: number;
  items_checked: number;
  items_changed: number;
  items_skipped: number;
}

export interface CountResult extends CountSummary {
  changes: Array<{
    item_id: number;
    item_name: string;
    previous_quantity: number;
    new_quantity: number;
    difference: number;
  }>;
  skipped_item_names: string[];
  emailed: boolean;
}
