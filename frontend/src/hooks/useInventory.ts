import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryApi } from '../api/inventory';
import type {
  InventoryCategoryCreate,
  InventoryCategoryUpdate,
  InventoryItemCreate,
  InventoryItemUpdate,
  PurchaseCreate,
  UsageCreate,
  AdjustmentCreate,
  TransactionType
} from '../types/inventory';

// Keys
export const inventoryKeys = {
  all: ['inventory'] as const,
  categories: () => [...inventoryKeys.all, 'categories'] as const,
  items: (filters?: any) => [...inventoryKeys.all, 'items', filters] as const,
  item: (id: number) => [...inventoryKeys.all, 'item', id] as const,
  lowStock: () => [...inventoryKeys.all, 'low-stock'] as const,
  transactions: (filters?: any) => [...inventoryKeys.all, 'transactions', filters] as const,
};

// Categories Hooks
export function useInventoryCategories() {
  return useQuery({
    queryKey: inventoryKeys.categories(),
    queryFn: inventoryApi.getCategories,
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InventoryCategoryCreate) => inventoryApi.createCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.categories() });
    },
  });
}

export function useUpdateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: InventoryCategoryUpdate }) => 
      inventoryApi.updateCategory(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.categories() });
    },
  });
}

export function useDeleteCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => inventoryApi.deleteCategory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.categories() });
    },
  });
}

// Items Hooks
export function useInventoryItems(filters?: {
  category_id?: number;
  is_active?: boolean;
  low_stock?: boolean;
  search?: string;
}) {
  return useQuery({
    queryKey: inventoryKeys.items(filters),
    queryFn: () => inventoryApi.getItems(filters),
  });
}

export function useLowStockItems() {
  return useQuery({
    queryKey: inventoryKeys.lowStock(),
    queryFn: inventoryApi.getLowStockItems,
  });
}

export function useCreateItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InventoryItemCreate) => inventoryApi.createItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.items() });
      queryClient.invalidateQueries({ queryKey: inventoryKeys.lowStock() });
    },
  });
}

export function useUpdateItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: InventoryItemUpdate }) => 
      inventoryApi.updateItem(id, data),
    onMutate: async ({ id, data }) => {
      // Cancel any outgoing refetches (so they don't overwrite our optimistic update)
      await queryClient.cancelQueries({ queryKey: ['inventory', 'items'] });
      await queryClient.cancelQueries({ queryKey: inventoryKeys.item(id) });

      // Snapshot the previous value
      const previousItems = queryClient.getQueriesData({ queryKey: ['inventory', 'items'] });
      const previousItem = queryClient.getQueryData(inventoryKeys.item(id));

      // Optimistically update the items list
      queryClient.setQueriesData({ queryKey: ['inventory', 'items'] }, (old: any) => {
        if (!old?.items) return old;
        return {
          ...old,
          items: old.items.map((item: any) => 
            item.id === id ? { ...item, ...data } : item
          )
        };
      });

      // Optimistically update the individual item
      queryClient.setQueryData(inventoryKeys.item(id), (old: any) => {
        if (!old) return old;
        return { ...old, ...data };
      });

      // Return a context object with the snapshotted value
      return { previousItems, previousItem };
    },
    onError: (_err, newTodo, context) => {
      // Rollback on error
      if (context?.previousItems) {
        context.previousItems.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      if (context?.previousItem) {
        queryClient.setQueryData(inventoryKeys.item(newTodo.id), context.previousItem);
      }
    },
    onSettled: (data) => {
      // Always refetch after error or success
      queryClient.invalidateQueries({ queryKey: ['inventory', 'items'] });
      if (data) {
        queryClient.invalidateQueries({ queryKey: inventoryKeys.item(data.id) });
      }
      queryClient.invalidateQueries({ queryKey: inventoryKeys.lowStock() });
    },
  });
}

export function useDeleteItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => inventoryApi.deleteItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.items() });
      queryClient.invalidateQueries({ queryKey: inventoryKeys.lowStock() });
    },
  });
}

// Transactions Hooks
export function useRecordPurchase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PurchaseCreate) => inventoryApi.recordPurchase(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.items() });
      queryClient.invalidateQueries({ queryKey: inventoryKeys.transactions() });
    },
  });
}

export function useRecordUsage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UsageCreate) => inventoryApi.recordUsage(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.items() });
      queryClient.invalidateQueries({ queryKey: inventoryKeys.lowStock() });
      queryClient.invalidateQueries({ queryKey: inventoryKeys.transactions() });
    },
  });
}

export function useRecordAdjustment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AdjustmentCreate) => inventoryApi.recordAdjustment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.items() });
      queryClient.invalidateQueries({ queryKey: inventoryKeys.lowStock() });
      queryClient.invalidateQueries({ queryKey: inventoryKeys.transactions() });
    },
  });
}

export function useInventoryTransactions(filters?: {
  item_id?: number;
  transaction_type?: TransactionType;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: inventoryKeys.transactions(filters),
    queryFn: () => inventoryApi.getTransactions(filters),
  });
}
