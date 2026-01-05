// ========================================
// Analytics Hooks
// Custom hooks for analytics data fetching
// ========================================

import { useQuery, useMutation } from '@tanstack/react-query';
import { analyticsApi, type AnalyticsQueryParams, type C1QueryRequest } from '../api/analytics';

/**
 * Hook to fetch revenue analytics
 */
export function useRevenue(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'revenue', params],
    queryFn: () => analyticsApi.getRevenue(params),
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook to fetch product performance analytics
 */
export function useProductPerformance(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'products', params],
    queryFn: () => analyticsApi.getProducts(params),
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook to fetch order statistics
 */
export function useOrderStatistics(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'orders', params],
    queryFn: () => analyticsApi.getOrderStats(params),
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook to fetchheatmap analytics
 */
export function useHeatmap(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'heatmap', params],
    queryFn: () => analyticsApi.getHeatmap(params),
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook to fetch calendar heatmap analytics
 */
export function useCalendarHeatmap(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'calendar-heatmap', params],
    queryFn: () => analyticsApi.getCalendarHeatmap(params),
    staleTime: 60000, // 1 minute
  });
}

// ========================================
// Group 1 Hooks
// ========================================

export function useCategoryPerformance(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'category-performance', params],
    queryFn: () => analyticsApi.getCategoryPerformance(params),
    staleTime: 60000,
  });
}

export function useInventoryValuation(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'inventory-valuation', params],
    queryFn: () => analyticsApi.getInventoryValuation(params),
    staleTime: 60000,
  });
}

export function useProductPerformanceDetailed(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'product-performance-detailed', params],
    queryFn: () => analyticsApi.getProductPerformanceDetailed(params),
    staleTime: 60000,
  });
}

export function usePaymentTrends(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'payment-trends', params],
    queryFn: () => analyticsApi.getPaymentTrends(params),
    staleTime: 60000,
  });
}

export function useOrderStatsDetailed(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'order-stats-detailed', params],
    queryFn: () => analyticsApi.getOrderStatsDetailed(params),
    staleTime: 60000,
  });
}


// ========================================
// Group 2 Hooks
// ========================================

export function useRevenueComposition(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'revenue-composition', params],
    queryFn: () => analyticsApi.getRevenueComposition(params),
    staleTime: 60000,
  });
}

export function useOrderStatusFlow(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'order-status-flow', params],
    queryFn: () => analyticsApi.getOrderStatusFlow(params),
    staleTime: 60000,
  });
}

export function useDayOfWeekStats(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'day-of-week-stats', params],
    queryFn: () => analyticsApi.getDayOfWeekStats(params),
    staleTime: 60000,
  });
}

export function useOrderValueDistribution(params?: AnalyticsQueryParams & { group_by?: string }) {
  return useQuery({
    queryKey: ['analytics', 'order-value-distribution', params],
    queryFn: () => analyticsApi.getOrderValueDistribution(params),
    staleTime: 60000,
  });
}

export function useItemQuantityDistribution(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'item-quantity-distribution', params],
    queryFn: () => analyticsApi.getItemQuantityDistribution(params),
    staleTime: 60000,
  });
}


// ========================================
// Group 3 Hooks
// ========================================

export function useOrderFlow(params?: AnalyticsQueryParams) {
  return useQuery({
    queryKey: ['analytics', 'order-flow', params],
    queryFn: () => analyticsApi.getOrderFlow(params),
    staleTime: 60000,
  });
}

export function useRevenueWaterfall(params?: AnalyticsQueryParams & { date?: string }) {
  return useQuery({
    queryKey: ['analytics', 'revenue-waterfall', params],
    queryFn: () => analyticsApi.getRevenueWaterfall(params),
    staleTime: 60000,
  });
}

export function useInventoryWaterfall(params?: AnalyticsQueryParams & { date?: string }) {
  return useQuery({
    queryKey: ['analytics', 'inventory-waterfall', params],
    queryFn: () => analyticsApi.getInventoryWaterfall(params),
    staleTime: 60000,
  });
}

export function useOrderTimeline(params?: AnalyticsQueryParams & { date?: string }) {
  return useQuery({
    queryKey: ['analytics', 'order-timeline', params],
    queryFn: () => analyticsApi.getOrderTimeline(params),
    staleTime: 60000,
  });
}


/**
 * Hook to query Thesys C1 conversational analytics
 */
export function useC1Query() {
  return useMutation({
    mutationFn: (request: C1QueryRequest) => analyticsApi.queryC1(request),
  });
}
