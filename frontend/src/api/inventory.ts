import apiClient from './client';
import type {
  InventoryCategory,
  InventoryCategoryCreate,
  InventoryCategoryUpdate,
  InventoryItem,
  InventoryItemCreate,
  InventoryItemUpdate,
  InventoryItemsResponse,
  LowStockResponse,
  PurchaseCreate,
  UsageCreate,
  AdjustmentCreate,
  BatchAdjustmentCreate,
  BatchAdjustmentResponse,
  CategorizedItems,
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
