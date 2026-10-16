import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { costingApi } from '../api/costing';
import { menuQueryKeys } from './useMenu';
import type { DishCostingIn } from '../types/costing';

export const costingKeys = {
  all: ['costing'] as const,
  list: () => [...costingKeys.all, 'list'] as const,
  forMenuItem: (menuItemId: number) => [...costingKeys.all, 'menu', menuItemId] as const,
  defaults: () => [...costingKeys.all, 'defaults'] as const,
  preview: (draft: DishCostingIn) => [...costingKeys.all, 'preview', draft] as const,
};

/** Recipes and margins are the owner's; pass enabled=false for anyone else. */
export function useCostingList(enabled: boolean) {
  return useQuery({ queryKey: costingKeys.list(), queryFn: costingApi.list, enabled });
}

/** A dish's saved recipe. Pass hasRecipe=false (from the list) to skip asking for one that doesn't exist. */
export function useMenuItemCosting(menuItemId: number, hasRecipe = true) {
  return useQuery({
    queryKey: costingKeys.forMenuItem(menuItemId),
    queryFn: () => costingApi.forMenuItem(menuItemId),
    enabled: hasRecipe,
  });
}

export function useCostingDefaults() {
  return useQuery({ queryKey: costingKeys.defaults(), queryFn: costingApi.defaults, staleTime: 5 * 60_000 });
}

/** The live cost of a recipe being edited. Keeps the last answer on screen while the next one loads. */
export function useCostingPreview(draft: DishCostingIn | null) {
  return useQuery({
    queryKey: costingKeys.preview(draft ?? { menu_item_id: 0, yield_units: 1, ingredients: [] }),
    queryFn: () => costingApi.preview(draft!),
    enabled: draft !== null,
    placeholderData: keepPreviousData,
  });
}

export function useSaveCosting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number | null; data: DishCostingIn }) =>
      id === null ? costingApi.create(data) : costingApi.update(id, data),
    onSuccess: saved => {
      // The open sheet has its recipe straight away, without a refetch flashing a spinner.
      queryClient.setQueryData(costingKeys.forMenuItem(saved.menu_item_id), saved);
      queryClient.invalidateQueries({ queryKey: costingKeys.all });
    },
  });
}

export function useApplySuggestedPrice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ costingId, price }: { costingId: number; price: number }) =>
      costingApi.applySuggestedPrice(costingId, price),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: costingKeys.all });
      queryClient.invalidateQueries({ queryKey: menuQueryKeys.all });
    },
    // Refused because the cost moved: fetch the new cost so the sheet shows the new price.
    onError: () => queryClient.invalidateQueries({ queryKey: costingKeys.all }),
  });
}
