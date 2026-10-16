import apiClient from './client';
import type {
  CostBreakdown,
  CostingDefaults,
  DishCosting,
  DishCostingIn,
  DishCostingSummary,
} from '../types/costing';

export const costingApi = {
  /** Every dish that has a recipe, with its cost, margin and gap count. */
  list: async (): Promise<DishCostingSummary[]> => {
    const response = await apiClient.get<DishCostingSummary[]>('/costing');
    return response.data;
  },

  /** A dish's saved recipe, or null when it has none yet. */
  forMenuItem: async (menuItemId: number): Promise<DishCosting | null> => {
    try {
      const response = await apiClient.get<DishCosting>(`/costing/menu/${menuItemId}`);
      return response.data;
    } catch (error) {
      if ((error as { response?: { status?: number } }).response?.status === 404) return null;
      throw error;
    }
  },

  defaults: async (): Promise<CostingDefaults> => {
    const response = await apiClient.get<CostingDefaults>('/costing/defaults');
    return response.data;
  },

  /** Costs a recipe without saving it. */
  preview: async (data: DishCostingIn): Promise<CostBreakdown> => {
    const response = await apiClient.post<CostBreakdown>('/costing/preview', data);
    return response.data;
  },

  create: async (data: DishCostingIn): Promise<DishCosting> => {
    const response = await apiClient.post<DishCosting>('/costing', data);
    return response.data;
  },

  update: async (id: number, data: DishCostingIn): Promise<DishCosting> => {
    const response = await apiClient.patch<DishCosting>(`/costing/${id}`, data);
    return response.data;
  },

  /**
   * Sets the menu price to the suggested one. `price` is what the owner confirmed:
   * refused (409) if the cost has moved since, or while the dish has gaps.
   */
  applySuggestedPrice: async (id: number, price: number): Promise<DishCosting> => {
    const response = await apiClient.post<DishCosting>(`/costing/${id}/apply-price`, { price });
    return response.data;
  },
};
