// ========================================
// useOrders Hook
// Orders management with optimistic updates
// ========================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ordersApi, paymentsApi } from '../api/client';
import type {
  CreateOrderRequest,
  Order,
  QueryParams,
  AddPaymentRequest,
  OrderItemsUpdateRequest,
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
 * const orders = data || [];
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
 * const { data } = useOrderHistory({ date: '2024-10-30' });
 * const orders = data || [];
 * ```
 */
export const useOrderHistory = (params?: QueryParams) => {
  return useQuery({
    queryKey: ordersQueryKeys.history(params),
    queryFn: () => ordersApi.getOrderHistory(params),
    // History data is stable, keep fresh for 5 minutes
    staleTime: 5 * 60 * 1000,
    // Don't retry on validation errors (422)
    retry: (failureCount, error: any) => {
      // Don't retry on 422 Unprocessable Entity or 404 Not Found
      if (error?.response?.status === 422 || error?.response?.status === 404) {
        return false;
      }
      return failureCount < 3;
    },
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
    mutationFn: (data: CreateOrderRequest) => ordersApi.createOrUpdateOrder(data),
    // Optimistic update
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ordersQueryKeys.active });

      // Snapshot the previous value
      const previousOrders = queryClient.getQueryData<Order[]>(ordersQueryKeys.active);

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
    mutationFn: ({ id, data }: { id: number; data: OrderItemsUpdateRequest }) =>
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

/**
 * Hook to update the served status of an order item
 *
 * @example
 * ```tsx
 * const { mutate: updateServedStatus } = useUpdateItemServedStatus();
 *
 * updateServedStatus({ orderId: 10, itemId: 5, isServed: true });
 * ```
 */
export const useUpdateItemServedStatus = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ orderId, itemId, isServed }: { orderId: number; itemId: number; isServed: boolean }) =>
      ordersApi.updateItemServedStatus(orderId, itemId, isServed),
    onSuccess: () => {
      // Invalidate active orders to refresh the list with updated served status
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
 *     { payment_method: 'upi', amount: 20000 },
 *     { payment_method: 'cash', amount: 3600 },
 *   ],
 * });
 * ```
 */
export const useAddPayments = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ orderId, data }: { orderId: number; data: AddPaymentRequest }) =>
      paymentsApi.addPayments(orderId, data),
    onSuccess: (_payments, variables) => {
      // Invalidate active orders (paid order will be removed)
      queryClient.invalidateQueries({ queryKey: ordersQueryKeys.active });
      // Invalidate order history to show the new paid order
      queryClient.invalidateQueries({ queryKey: ordersQueryKeys.history() });
      // Refresh order detail cache
      queryClient.invalidateQueries({ queryKey: ordersQueryKeys.detail(variables.orderId) });
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
 * const activeOrders = orders.active.data || [];
 * const history = orders.history.data || [];
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
