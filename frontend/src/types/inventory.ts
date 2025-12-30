export interface InventoryCategory {
  id: number;
  name: string;
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
  created_at: string;
  updated_at?: string;
}

export interface InventoryItemCreate {
  name: string;
  unit: string;
  current_quantity: number;
  min_threshold: number;
  cost_per_unit?: number;
  category_id?: number;
}

export interface InventoryItemUpdate {
  name?: string;
  unit?: string;
  min_threshold?: number;
  cost_per_unit?: number;
  category_id?: number;
  is_active?: boolean;
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
}

export interface PurchaseItem {
  item_id: number;
  quantity: number;
  notes?: string;
}

export interface PurchaseCreate {
  items: PurchaseItem[];
}

export interface UsageItem {
  item_id: number;
  quantity: number;
  notes?: string;
}

export interface UsageCreate {
  items: UsageItem[];
  recorded_by: string;
}

export interface AdjustmentCreate {
  item_id: number;
  new_quantity: number;
  notes: string;
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
