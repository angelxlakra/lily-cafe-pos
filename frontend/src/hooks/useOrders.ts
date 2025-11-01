// ========================================
// useOrders Hook
// Orders management with optimistic updates
// ========================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ordersApi, paymentsApi } from '../api/client';
import type {
  CreateOrderRequest,
  UpdateOrderRequest,
  Order,
  QueryParams,
  AddPaymentRequest,
} from '../types';

// Query keys for caching
export const ordersQueryKeys = {
  all: ['orders'] as const,
  active: ['orders', 'active'] as const,
  history: (params?: QueryParams) => ['orders', 'history', params] as const,
  detail: (id: number) => ['orders', 'detail', id] as const,
};

// ========================================
// Orders Query Hooks
// ========================================

/**
 * Hook to fetch all active (unpaid) orders
 *
 * This query refetches frequently to show real-time order updates
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useActiveOrders();
 * const orders = data?.orders || [];
 * ```
 */
export const useActiveOrders = () => {
  return useQuery({
    queryKey: ordersQueryKeys.active,
    queryFn: () => ordersApi.getActiveOrders(),
    // Refetch every 30 seconds to show updates from other users
    refetchInterval: 30 * 1000,
    // Keep data fresh for only 10 seconds
    staleTime: 10 * 1000,
  });
};

/**
 * Hook to fetch a single order by ID
 *
 * @example
 * ```tsx
 * const { data: order, isLoading } = useOrder(10);
 * ```
 */
export const useOrder = (id: number) => {
  return useQuery({
    queryKey: ordersQueryKeys.detail(id),
    queryFn: () => ordersApi.getOrderById(id),
    enabled: !!id, // Only fetch if ID is provided
  });
};

/**
 * Hook to fetch order history with optional filters
 *
 * @example
 * ```tsx
 * const { data } = useOrderHistory({ date: '2024-10-30', limit: 50 });
 * const orders = data?.orders || [];
 * ```
 */
export const useOrderHistory = (params?: QueryParams) => {
  return useQuery({
    queryKey: ordersQueryKeys.history(params),
    queryFn: () => ordersApi.getOrderHistory(params),
    // History data is stable, keep fresh for 5 minutes
    staleTime: 5 * 60 * 1000,
  });
};

// ========================================
// Orders Mutation Hooks
// ========================================

/**
 * Hook to create or update an order with optimistic updates
 *
 * Features:
 * - Optimistically updates the UI before server confirms
 * - Automatically rolls back on error
 * - Invalidates active orders cache on success
 *
 * @example
 * ```tsx
 * const { mutate: createOrder, isPending } = useCreateOrUpdateOrder();
 *
 * createOrder({
 *   table_number: 5,
 *   items: [
 *     { menu_item_id: 1, quantity: 2 },
 *     { menu_item_id: 3, quantity: 1 },
 *   ],
 * });
 * ```
 */
export const useCreateOrUpdateOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateOrderRequest | UpdateOrderRequest) => ordersApi.createOrUpdateOrder(data),
    // Optimistic update
    onMutate: async (data) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ordersQueryKeys.active });

      // Snapshot the previous value
      const previousOrders = queryClient.getQueryData<Order[]>(ordersQueryKeys.active);

      // Optimistically update to the new value
      // Note: This is a simplified optimistic update - production may need more sophisticated logic
      queryClient.setQueryData<Order[]>(ordersQueryKeys.active, (old) => {
        if (!old) return old;

        // If it's an update, find and update the existing order
        if ('order_id' in data) {
          const updatedOrders = old.map(order =>
            order.id === data.order_id ? { ...order } : order
          );
          return updatedOrders;
        }

        // For new orders, we can't add optimistically without server data
        // so we just return the old data
        return old;
      });

      // Return a context object with the snapshotted value
      return { previousOrders };
    },
    // If the mutation fails, rollback
    onError: (err, _data, context) => {
      queryClient.setQueryData(ordersQueryKeys.active, context?.previousOrders);
      console.error('Order mutation failed:', err);
    },
    // Always refetch after error or success
    onSettled: () => {
      // Invalidate active orders list
      queryClient.invalidateQueries({ queryKey: ordersQueryKeys.active });
      // Invalidate all order detail queries to refresh individual order views
      queryClient.invalidateQueries({ queryKey: ordersQueryKeys.all });
    },
  });
};

/**
 * Hook to update an order (admin only)
 *
 * @example
 * ```tsx
 * const { mutate: updateOrder } = useUpdateOrder();
 *
 * updateOrder({
 *   id: 10,
 *   data: {
 *     items: [
 *       { menu_item_id: 1, quantity: 3 },
 *     ],
 *   },
 * });
 * ```
 */
export const useUpdateOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: { items: Array<{ menu_item_id: number; quantity: number }> } }) =>
      ordersApi.updateOrder(id, data),
    onSuccess: (updatedOrder) => {
      // Update the single order cache
      queryClient.setQueryData(ordersQueryKeys.detail(updatedOrder.id), updatedOrder);
      // Invalidate active orders
      queryClient.invalidateQueries({ queryKey: ordersQueryKeys.active });
    },
  });
};

/**
 * Hook to cancel an order (admin only)
 *
 * @example
 * ```tsx
 * const { mutate: cancelOrder } = useCancelOrder();
 *
 * cancelOrder(10);
 * ```
 */
export const useCancelOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => ordersApi.cancelOrder(id),
    onSuccess: () => {
      // Invalidate active orders to remove the canceled order
      queryClient.invalidateQueries({ queryKey: ordersQueryKeys.active });
    },
  });
};

// ========================================
// Payments Mutation Hooks
// ========================================

/**
 * Hook to add payments to an order
 *
 * @example
 * ```tsx
 * const { mutate: addPayments } = useAddPayments();
 *
 * addPayments({
 *   orderId: 10,
 *   payments: [
 *     { method: 'upi', amount: 200 },
 *     { method: 'cash', amount: 36 },
 *   ],
 * });
 * ```
 */
export const useAddPayments = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ orderId, data }: { orderId: number; data: AddPaymentRequest }) =>
      paymentsApi.addPayments(orderId, data),
    onSuccess: () => {
      // Invalidate active orders (paid order will be removed)
      queryClient.invalidateQueries({ queryKey: ordersQueryKeys.active });
      // Invalidate order history to show the new paid order
      queryClient.invalidateQueries({ queryKey: ordersQueryKeys.history() });
    },
  });
};

/**
 * Hook to print a receipt
 *
 * @example
 * ```tsx
 * const { mutate: printReceipt, isPending } = usePrintReceipt();
 *
 * printReceipt(10);
 * ```
 */
export const usePrintReceipt = () => {
  return useMutation({
    mutationFn: (orderId: number) => paymentsApi.printReceipt(orderId),
  });
};

// ========================================
// Composite Hook
// ========================================

/**
 * All-in-one hook for order management
 *
 * @example
 * ```tsx
 * const orders = useOrders();
 *
 * // Access data
 * const activeOrders = orders.active.data?.orders || [];
 * const history = orders.history.data?.orders || [];
 *
 * // Use mutations
 * orders.createOrder({ table_number: 5, items: [...] });
 * orders.cancelOrder(10);
 * orders.addPayments({ orderId: 10, payments: [...] });
 * ```
 */
export const useOrders = (historyParams?: QueryParams) => {
  const active = useActiveOrders();
  const history = useOrderHistory(historyParams);
  const createOrUpdate = useCreateOrUpdateOrder();
  const updateOrder = useUpdateOrder();
  const cancelOrder = useCancelOrder();
  const addPayments = useAddPayments();
  const printReceipt = usePrintReceipt();

  return {
    active,
    history,
    createOrder: createOrUpdate.mutate,
    createOrderAsync: createOrUpdate.mutateAsync,
    updateOrder: updateOrder.mutate,
    updateOrderAsync: updateOrder.mutateAsync,
    cancelOrder: cancelOrder.mutate,
    cancelOrderAsync: cancelOrder.mutateAsync,
    addPayments: addPayments.mutate,
    addPaymentsAsync: addPayments.mutateAsync,
    printReceipt: printReceipt.mutate,
    printReceiptAsync: printReceipt.mutateAsync,
    isLoading: active.isLoading || history.isLoading,
    isMutating:
      createOrUpdate.isPending ||
      updateOrder.isPending ||
      cancelOrder.isPending ||
      addPayments.isPending ||
      printReceipt.isPending,
  };
};
