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
 * Hook to query Thesys C1 conversational analytics
 */
export function useC1Query() {
  return useMutation({
    mutationFn: (request: C1QueryRequest) => analyticsApi.queryC1(request),
  });
}
