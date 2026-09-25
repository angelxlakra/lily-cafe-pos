import apiClient from './client';
import type {
  InventoryCategory,
  InventoryCategoryCreate,
  InventoryCategoryUpdate,
  InventoryItem,
  InventoryItemCreate,
  InventoryItemUpdate,
  BulkItemUpdate,
  InventoryItemsResponse,
  LowStockResponse,
  PurchaseCreate,
  UsageCreate,
  AdjustmentCreate,
  BatchAdjustmentCreate,
  BatchAdjustmentResponse,
  CategorizedItems,
  CountLine,
  CountResult,
  CountSheetGroup,
  CountSummary,
  TransactionsResponse,
  TransactionType
} from '../types/inventory';

export const inventoryApi = {
  // Categories
  getCategories: async (): Promise<InventoryCategory[]> => {
    const response = await apiClient.get<InventoryCategory[]>('/inventory/categories');
    return response.data;
  },

  createCategory: async (data: InventoryCategoryCreate): Promise<InventoryCategory> => {
    const response = await apiClient.post<InventoryCategory>('/inventory/categories', data);
    return response.data;
  },

  updateCategory: async (id: number, data: InventoryCategoryUpdate): Promise<InventoryCategory> => {
    const response = await apiClient.patch<InventoryCategory>(`/inventory/categories/${id}`, data);
    return response.data;
  },

  deleteCategory: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/inventory/categories/${id}`);
    return response.data;
  },

  // Items
  getItems: async (params?: {
    category_id?: number;
    is_active?: boolean;
    low_stock?: boolean;
    search?: string;
  }): Promise<InventoryItemsResponse> => {
    const response = await apiClient.get<InventoryItemsResponse>('/inventory/items', { params });
    return response.data;
  },

  getLowStockItems: async (): Promise<LowStockResponse> => {
    const response = await apiClient.get<LowStockResponse>('/inventory/items/low-stock');
    return response.data;
  },

  getItem: async (id: number): Promise<InventoryItem> => {
    const response = await apiClient.get<InventoryItem>(`/inventory/items/${id}`);
    return response.data;
  },

  createItem: async (data: InventoryItemCreate): Promise<InventoryItem> => {
    const response = await apiClient.post<InventoryItem>('/inventory/items', data);
    return response.data;
  },

  updateItem: async (id: number, data: InventoryItemUpdate): Promise<InventoryItem> => {
    const response = await apiClient.patch<InventoryItem>(`/inventory/items/${id}`, data);
    return response.data;
  },

  /** The setup grid's one Save: all changed rows in one commit. */
  bulkUpdateItems: async (items: BulkItemUpdate[]): Promise<{ updated: number; adjusted: number }> => {
    const response = await apiClient.patch<{ updated: number; adjusted: number }>('/inventory/items', { items });
    return response.data;
  },

  deleteItem: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/inventory/items/${id}`);
    return response.data;
  },

  // Transactions
  recordPurchase: async (data: PurchaseCreate): Promise<any> => {
    const response = await apiClient.post('/inventory/transactions/purchase', data);
    return response.data;
  },

  recordUsage: async (data: UsageCreate): Promise<any> => {
    const response = await apiClient.post('/inventory/transactions/usage', data);
    return response.data;
  },

  recordAdjustment: async (data: AdjustmentCreate): Promise<any> => {
    const response = await apiClient.post('/inventory/transactions/adjustment', data);
    return response.data;
  },

  recordBatchAdjustment: async (data: BatchAdjustmentCreate): Promise<BatchAdjustmentResponse> => {
    const response = await apiClient.post<BatchAdjustmentResponse>('/inventory/transactions/batch-adjustment', data);
    return response.data;
  },

  getItemsByCategory: async (): Promise<CategorizedItems> => {
    const itemsResponse = await inventoryApi.getItems({ is_active: true });
    const categories = await inventoryApi.getCategories();

    // Group items by category
    const grouped: CategorizedItems = {};

    // Add uncategorized category
    grouped[0] = {
      category: null,
      items: []
    };

    // Create category entries
    categories.forEach(cat => {
      grouped[cat.id] = {
        category: cat,
        items: []
      };
    });

    // Group items
    itemsResponse.items.forEach(item => {
      const catId = item.category_id || 0;
      if (grouped[catId]) {
        grouped[catId].items.push(item);
      }
    });

    return grouped;
  },

  /** Active items grouped by category, both in count order; uncategorized last. */
  getCountSheet: async (): Promise<CountSheetGroup[]> => {
    const [itemsResponse, categories] = await Promise.all([
      inventoryApi.getItems({ is_active: true }),
      inventoryApi.getCategories(),
    ]);
    const groups: CountSheetGroup[] = categories.map(category => ({ category, items: [] }));
    const byId = new Map(groups.map(group => [group.category!.id, group]));
    const uncategorized: CountSheetGroup = { category: null, items: [] };
    // The API already returns items in count order.
    itemsResponse.items.forEach(item => {
      (byId.get(item.category_id ?? -1) ?? uncategorized).items.push(item);
    });
    return [...groups, uncategorized].filter(group => group.items.length > 0);
  },

  saveCount: async (lines: CountLine[]): Promise<CountResult> => {
    const response = await apiClient.post<CountResult>('/inventory/counts', { lines });
    return response.data;
  },

  getTodaysCount: async (): Promise<CountSummary | null> => {
    const response = await apiClient.get<CountSummary | null>('/inventory/counts/today');
    return response.data;
  },

  getCounts: async (limit = 7): Promise<CountSummary[]> => {
    const response = await apiClient.get<CountSummary[]>('/inventory/counts', { params: { limit } });
    return response.data;
  },

  reorderCategories: async (ids: number[]): Promise<void> => {
    await apiClient.put('/inventory/categories/order', { ids });
  },

  reorderItems: async (ids: number[]): Promise<void> => {
    await apiClient.put('/inventory/items/order', { ids });
  },

  getTransactions: async (params?: {
    item_id?: number;
    transaction_type?: TransactionType;
    limit?: number;
    offset?: number;
  }): Promise<TransactionsResponse> => {
    const response = await apiClient.get<TransactionsResponse>('/inventory/transactions', { params });
    return response.data;
  },
};
