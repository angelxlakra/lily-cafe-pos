// Typed calls and React Query hooks for the ops pages: recipes and the overview, pack prices,
// brands, the daily purchase sheet and the owner's price approvals. Built on the existing
// client and types; Tasks 5-7 (inventory, sheet, recipes list) use these as they are.

import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import { costingApi } from '../api/costing';
import { inventoryApi } from '../api/inventory';
import { costingKeys } from '../hooks/useCosting';
import { inventoryKeys } from '../hooks/useInventory';
import type { CostBreakdown, DishCosting, DishCostingIn } from '../types/costing';
import type { InventoryItem, PurchaseDay } from '../types/inventory';

type Num = number | string;

// ---------- Costing ----------

export interface OverviewRow {
  kind: 'dish' | 'made';
  costing_id: number | null;
  menu_item_id: number | null;
  inventory_item_id: number | null;
  name: string;
  category: string | null;
  cost_per_unit: Num | null;
  unit: string | null;
  selling_price: Num | null;
  margin_percent: Num | null;
  target_margin_percent: Num | null;
  /** Best margin possible while prices are missing. */
  margin_ceiling: Num | null;
  missing_count: number;
  cost_last_week: Num | null;
  status: 'below_target' | 'missing_prices' | 'no_recipe' | 'on_target' | 'costed';
}

export interface Overview {
  rows: OverviewRow[];
  totals: { below_target: number; missing_prices: number; no_recipe: number; average_margin: Num | null };
}

export interface UsedIn {
  costing_id: number;
  name: string;
  kind: 'dish' | 'made';
}

/** A saved recipe: a dish's, or a kitchen-made item's. */
export interface Recipe extends Omit<DishCosting, 'menu_item_id' | 'menu_item_name'> {
  menu_item_id: number | null;
  menu_item_name: string | null;
  inventory_item_id: number | null;
  kind: 'dish' | 'made';
  name: string;
  unit: string | null;
  used_in: UsedIn[];
}

const opsKeys = {
  overview: () => [...costingKeys.all, 'overview'] as const,
  recipeDish: (menuItemId: number) => [...costingKeys.all, 'recipe', 'dish', menuItemId] as const,
  recipeMade: (itemId: number) => [...costingKeys.all, 'recipe', 'made', itemId] as const,
  recipePreview: (draft: DishCostingIn | null) => [...costingKeys.all, 'recipe-preview', draft] as const,
  purchases: (businessDate?: string) => [...inventoryKeys.all, 'purchases', businessDate ?? 'today'] as const,
  pending: () => [...inventoryKeys.all, 'pending-prices'] as const,
};

const notFound = (error: unknown) => (error as { response?: { status?: number } }).response?.status === 404;

async function getRecipe(path: string): Promise<Recipe | null> {
  try {
    return (await apiClient.get<Recipe>(path)).data;
  } catch (error) {
    if (notFound(error)) return null;
    throw error;
  }
}

/** Every dish and made item with cost, margin and status (owner). */
export function useOverview(enabled = true) {
  return useQuery({
    queryKey: opsKeys.overview(),
    queryFn: async () => (await apiClient.get<Overview>('/costing/overview')).data,
    enabled,
  });
}

/** A dish's recipe, or null when it has none yet (owner). */
export function useDishRecipe(menuItemId: number, enabled = true) {
  return useQuery({
    queryKey: opsKeys.recipeDish(menuItemId),
    queryFn: () => getRecipe(`/costing/menu/${menuItemId}`),
    enabled,
  });
}

/** A kitchen-made item's recipe, or null when it has none yet (owner). */
export function useMadeRecipe(itemId: number, enabled = true) {
  return useQuery({
    queryKey: opsKeys.recipeMade(itemId),
    queryFn: () => getRecipe(`/costing/item/${itemId}`),
    enabled,
  });
}

/** The live cost of a recipe being edited; keeps the last answer on screen while the next loads. */
export function useRecipePreview(draft: DishCostingIn | null) {
  return useQuery({
    queryKey: opsKeys.recipePreview(draft),
    queryFn: () => costingApi.preview(draft!),
    enabled: draft !== null,
    placeholderData: keepPreviousData,
    staleTime: 0,
  });
}

export { useCostingDefaults } from '../hooks/useCosting';

/** Creates the recipe, or updates it when it already has an id. */
export function useSaveRecipe() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number | null; data: DishCostingIn }): Promise<Recipe> =>
      id === null
        ? apiClient.post<Recipe>('/costing', data).then(r => r.data)
        : apiClient.patch<Recipe>(`/costing/${id}`, data).then(r => r.data),
    onSuccess: () => {
      // A made item's new cost ripples into every dish that uses it.
      queryClient.invalidateQueries({ queryKey: costingKeys.all });
      queryClient.invalidateQueries({ queryKey: inventoryKeys.all });
    },
  });
}

// ---------- Items: brand and pack price ----------

export interface PackPriceIn {
  price: number;
  pack_quantity: number;
  pack_unit: string;
}

export function useSetBrand() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, brand }: { id: number; brand: string }) => inventoryApi.updateItem(id, { brand }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: inventoryKeys.all }),
  });
}

/** "₹99 / 10 g" on an item (owner). 400 for an unknown unit or a yes/no item. */
export function useSetPackPrice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...data }: PackPriceIn & { id: number }) =>
      (await apiClient.post<InventoryItem>(`/inventory/items/${id}/pack-price`, data)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.all });
      queryClient.invalidateQueries({ queryKey: costingKeys.all });
    },
  });
}

// ---------- Purchases and price approvals ----------

/** A day's purchase sheet (default today). Lines carry price_status. Other days: owner only. */
export function usePurchaseDay(businessDate?: string) {
  return useQuery({
    queryKey: opsKeys.purchases(businessDate),
    queryFn: (): Promise<PurchaseDay> => inventoryApi.getPurchases(businessDate),
  });
}

export interface RippleDish {
  costing_id: number;
  menu_item_name: string;
  cost_before: Num;
  cost_after: Num;
  margin_before: Num | null;
  margin_after: Num | null;
  crosses_below_target: boolean;
  /** Kitchen-made items the change passed through to reach this dish. */
  via: string[];
}

export interface RippleMade {
  item_id: number;
  name: string;
  unit: string;
  cost_before: Num;
  cost_after: Num;
}

export interface Ripple {
  affected_dishes: RippleDish[];
  unaffected_count: number;
  made_items: RippleMade[];
}

export interface PendingPrice {
  purchase_id: number;
  item_id: number;
  item_name: string;
  brand: string | null;
  unit: string;
  recorded_by: string;
  created_at: string;
  quantity: Num;
  total_amount: Num;
  pack_count: Num | null;
  old_price: Num | null;
  new_price: Num | null;
  /** A fraction: 0.25 is 25% up. */
  change: Num | null;
  is_new_item: boolean;
  ripple: Ripple | null;
}

/** Purchase prices waiting for the owner, oldest first. */
export function usePendingPrices(enabled = true) {
  return useQuery({
    queryKey: opsKeys.pending(),
    queryFn: async () => (await apiClient.get<PendingPrice[]>('/inventory/purchases/pending-prices')).data,
    enabled,
  });
}

function useAfterReview() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: inventoryKeys.all });
    queryClient.invalidateQueries({ queryKey: costingKeys.all });
  };
}

/** Approve (the price becomes the item's) or reject (stock stays, price doesn't). */
export function useReviewPrice() {
  const after = useAfterReview();
  return useMutation({
    mutationFn: async ({ purchaseId, action }: { purchaseId: number; action: 'approve' | 'reject' }) =>
      (await apiClient.post(`/inventory/purchases/${purchaseId}/price-review`, { action })).data,
    onSuccess: after,
  });
}

export function useApproveAllPrices() {
  const after = useAfterReview();
  return useMutation({
    mutationFn: async () => (await apiClient.post<{ approved: number }>('/inventory/purchases/price-review/approve-all')).data,
    onSuccess: after,
  });
}

export type { CostBreakdown };
