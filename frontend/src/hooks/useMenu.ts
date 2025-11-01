// ========================================
// useMenu Hook
// Menu items and categories management
// ========================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { menuApi, categoriesApi } from '../api/client';
import type {
  QueryParams,
  CreateMenuItemRequest,
  UpdateMenuItemRequest,
  Category,
  CreateCategoryRequest,
} from '../types';

// Query keys for caching
export const menuQueryKeys = {
  all: ['menu'] as const,
  items: (params?: QueryParams) => ['menu', 'items', params] as const,
  item: (id: number) => ['menu', 'item', id] as const,
  categories: ['menu', 'categories'] as const,
};

// ========================================
// Menu Items Hooks
// ========================================

/**
 * Hook to fetch menu items with optional filters
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useMenuItems({ available_only: true });
 * ```
 */
export const useMenuItems = (params?: QueryParams) => {
  return useQuery({
    queryKey: menuQueryKeys.items(params),
    queryFn: () => menuApi.getMenuItems(params),
    // Keep menu data fresh for 10 minutes
    staleTime: 10 * 60 * 1000,
  });
};

/**
 * Hook to fetch a single menu item by ID
 *
 * @example
 * ```tsx
 * const { data: menuItem, isLoading } = useMenuItem(5);
 * ```
 */
export const useMenuItem = (id: number) => {
  return useQuery({
    queryKey: menuQueryKeys.item(id),
    queryFn: () => menuApi.getMenuItem(id),
    enabled: !!id, // Only fetch if ID is provided
  });
};

/**
 * Hook to create a new menu item
 *
 * @example
 * ```tsx
 * const { mutate: createItem, isPending } = useCreateMenuItem();
 *
 * createItem({
 *   name: 'Masala Dosa',
 *   price: 80,
 *   category: 'South Indian',
 * });
 * ```
 */
export const useCreateMenuItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateMenuItemRequest) => menuApi.createMenuItem(data),
    onSuccess: () => {
      // Invalidate menu items queries to refetch
      queryClient.invalidateQueries({ queryKey: menuQueryKeys.all });
    },
  });
};

/**
 * Hook to update an existing menu item
 *
 * @example
 * ```tsx
 * const { mutate: updateItem } = useUpdateMenuItem();
 *
 * updateItem({ id: 5, data: { price: 90 } });
 * ```
 */
export const useUpdateMenuItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateMenuItemRequest }) =>
      menuApi.updateMenuItem(id, data),
    onSuccess: (data) => {
      // Invalidate all menu queries
      queryClient.invalidateQueries({ queryKey: menuQueryKeys.all });
      // Optionally update the single item cache
      queryClient.setQueryData(menuQueryKeys.item(data.id), data);
    },
  });
};

/**
 * Hook to delete (soft delete) a menu item
 *
 * @example
 * ```tsx
 * const { mutate: deleteItem } = useDeleteMenuItem();
 *
 * deleteItem(5);
 * ```
 */
export const useDeleteMenuItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => menuApi.deleteMenuItem(id),
    onSuccess: () => {
      // Invalidate menu items queries
      queryClient.invalidateQueries({ queryKey: menuQueryKeys.all });
    },
  });
};

// ========================================
// Categories Hooks
// ========================================

/**
 * Hook to fetch all categories
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useCategories();
 * const categories = data?.categories || [];
 * ```
 */
export const useCategories = () => {
  return useQuery({
    queryKey: menuQueryKeys.categories,
    queryFn: () => categoriesApi.getCategories(),
    // Categories don't change often, keep fresh for 30 minutes
    staleTime: 30 * 60 * 1000,
  });
};

/**
 * Hook to create a new category
 *
 * @example
 * ```tsx
 * const { mutate: createCategory } = useCreateCategory();
 *
 * createCategory({ name: 'North Indian' });
 * ```
 */
export const useCreateCategory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateCategoryRequest) => categoriesApi.createCategory(data),
    onSuccess: (newCategory) => {
      // Update categories cache optimistically
      queryClient.setQueryData(menuQueryKeys.categories, (old: { categories: Category[] } | undefined) => {
        if (!old) return { categories: [newCategory] };
        return { categories: [...old.categories, newCategory] };
      });
      // Also invalidate to ensure consistency
      queryClient.invalidateQueries({ queryKey: menuQueryKeys.categories });
    },
  });
};

// ========================================
// Composite Hook
// ========================================

/**
 * All-in-one hook for menu management
 *
 * @example
 * ```tsx
 * const menu = useMenu({ available_only: true });
 *
 * // Access data
 * const items = menu.items.data?.items || [];
 * const categories = menu.categories.data?.categories || [];
 *
 * // Use mutations
 * menu.createItem({ name: 'New Dish', price: 100, category: 'Main Course' });
 * menu.deleteItem(5);
 * ```
 */
export const useMenu = (params?: QueryParams) => {
  const items = useMenuItems(params);
  const categories = useCategories();
  const createItem = useCreateMenuItem();
  const updateItem = useUpdateMenuItem();
  const deleteItem = useDeleteMenuItem();
  const createCategory = useCreateCategory();

  return {
    items,
    categories,
    createItem: createItem.mutate,
    createItemAsync: createItem.mutateAsync,
    updateItem: updateItem.mutate,
    updateItemAsync: updateItem.mutateAsync,
    deleteItem: deleteItem.mutate,
    deleteItemAsync: deleteItem.mutateAsync,
    createCategory: createCategory.mutate,
    createCategoryAsync: createCategory.mutateAsync,
    isLoading: items.isLoading || categories.isLoading,
    isMutating: createItem.isPending || updateItem.isPending || deleteItem.isPending || createCategory.isPending,
  };
};
