// ========================================
// Analytics API Client
// Lily Cafe POS System - Frontend
// ========================================

import apiClient from './client';

// ========================================
// Types
// ========================================

export interface RevenueData {
  total_revenue: number;
  total_orders: number;
  average_order_value: number;
  revenue_by_payment_method: Record<string, number>;
  revenue_trend: Array<{
    date: string;
    revenue: number;
  }>;
}

export interface ProductPerformance {
  top_products: Array<{
    name: string;
    quantity_sold: number;
    revenue: number;
  }>;
  revenue_by_category: Record<string, number>;
}

export interface OrderStatistics {
  total_orders: number;
  active_orders: number;
  completed_orders: number;
  canceled_orders: number;
  average_order_value: number;
  peak_hours: Array<{
    hour: number;
    order_count: number;
  }>;
}

export interface HeatmapPoint {
  day_of_week: number;
  hour: number;
  order_count: number;
  revenue: number;
}

export interface HeatmapResponse {
  data: HeatmapPoint[];
}

export interface CalendarHeatmapPoint {
  date: string;
  value: number;
  count: number;
}

export interface CalendarHeatmapResponse {
  data: CalendarHeatmapPoint[];
}

export interface C1QueryRequest {
  prompt: string;
  c1_response?: string;
}

export interface C1QueryResponse {
  content: string;
}

export interface AnalyticsQueryParams {
  start_date?: string;
  end_date?: string;
  limit?: number;
  group_by?: string;
  date?: string;
}

// ========================================
// New Chart Types
// ========================================

export interface BaseCategoryStat {
  name: string;
  revenue_rupees: number;
  order_count: number;
  avg_order_value_rupees: number;
  items_count: number;
  top_item: any;
  vegetarian_ratio: number;
  beverage_ratio: number;
  revenue_percentage: number;
}

export interface CategoryPerformanceResponse {
  categories: BaseCategoryStat[];
  total_categories: number;
}

export interface LowStockItem {
  name: string;
  current_quantity: number;
  unit: string;
  min_threshold: number;
  shortage: number;
  category: string;
  value_rupees: number;
}

export interface InventoryStatusResponse {
  items: LowStockItem[];
  low_stock_items: LowStockItem[];
  low_stock_count: number;
  out_of_stock_count: number;
  total_inventory_value_rupees: number;
}

export interface ProductPerformanceItem {
  name: string;
  quantity_sold: number;
  revenue_rupees: number;
  order_count: number;
  avg_quantity_per_order: number;
  frequency: number;
}

export interface ProductPerformanceDetailedResponse {
  top_products: ProductPerformanceItem[];
}

export interface PaymentMethodStat {
  total_amount_rupees: number;
  transaction_count: number;
  avg_transaction_rupees: number;
  percentage_revenue: number;
  percentage_count: number;
}

export interface PaymentTrendsResponse {
  payment_methods: Record<string, PaymentMethodStat>;
  total_revenue_rupees: number;
  highest_avg_transaction_method: string | null;
}

export interface OrderStatsDetailedResponse {
  total_orders: number;
  active_orders: number;
  completed_orders: number;
  average_order_value_rupees: number;
  active_rate: number;
  completion_rate: number;
  cancellation_rate: number;
}

export interface RevenueCompositionItem {
  date: string;
  category: string;
  revenue: number;
}

export interface RevenueCompositionResponse {
  data: RevenueCompositionItem[];
}

export interface OrderStatusFlowItem {
  date: string;
  status: string;
  count: number;
}

export interface OrderStatusFlowResponse {
  data: OrderStatusFlowItem[];
}

export interface DayOfWeekStat {
  day: string;
  day_index: number;
  revenue_rupees: number;
  order_count: number;
  avg_order_value_rupees: number;
  payment_diversity: number;
  parcel_ratio: number;
}

export interface DayOfWeekStatsResponse {
  data: DayOfWeekStat[];
}

export interface BoxPlotData {
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
}

export interface OrderValueDistributionItem {
  group: string;
  stats: BoxPlotData;
}

export interface OrderValueDistributionResponse {
  data: OrderValueDistributionItem[];
}

export interface ItemQuantityDistributionItem {
  item_name: string;
  stats: BoxPlotData;
}

export interface ItemQuantityDistributionResponse {
  data: ItemQuantityDistributionItem[];
}

export interface SankeyNode {
  name: string;
}

export interface SankeyLink {
  source: number;
  target: number;
  value: number;
}

export interface SankeyData {
  nodes: SankeyNode[];
  links: SankeyLink[];
}

export interface WaterfallItem {
  name: string;
  value: number;
  is_total: boolean;
  color?: string;
}

export interface WaterfallResponse {
  data: WaterfallItem[];
}

export interface OrdersTimelineItem {
  order_number: string;
  table_number: number;
  created_at: string;
  amount: number;
  paid_at?: string;
  duration_minutes?: number;
}

export interface OrdersTimelineResponse {
  data: OrdersTimelineItem[];
}


// ========================================
// API Functions
// ========================================

export const analyticsApi = {
  /**
   * Get revenue analytics
   */
  async getRevenue(params?: AnalyticsQueryParams): Promise<RevenueData> {
    const response = await apiClient.get(`/analytics/revenue`, {
      params,
    });
    return response.data;
  },

  /**
   * Get product performance analytics
   */
  async getProducts(params?: AnalyticsQueryParams): Promise<ProductPerformance> {
    const response = await apiClient.get(`/analytics/products`, {
      params,
    });
    return response.data;
  },

  /**
   * Get order statistics
   */
  async getOrderStats(params?: AnalyticsQueryParams): Promise<OrderStatistics> {
    const response = await apiClient.get(`/analytics/orders`, {
      params,
    });
    return response.data;
  },

  /**
   * Get heatmap analytics
   */
  async getHeatmap(params?: AnalyticsQueryParams): Promise<HeatmapResponse> {
    const response = await apiClient.get(`/analytics/heatmap`, {
      params,
    });
    return response.data;
  },

  /**
   * Get calendar heatmap analytics
   */
  async getCalendarHeatmap(params?: AnalyticsQueryParams): Promise<CalendarHeatmapResponse> {
    const response = await apiClient.get(`/analytics/calendar-heatmap`, {
      params,
    });
    return response.data;
  },

  // Group 1
  async getCategoryPerformance(params?: AnalyticsQueryParams): Promise<CategoryPerformanceResponse> {
    const response = await apiClient.get(`/analytics/category-performance`, { params });
    return response.data;
  },
  async getInventoryValuation(params?: AnalyticsQueryParams): Promise<InventoryStatusResponse> {
    const response = await apiClient.get(`/analytics/inventory-valuation`, { params });
    return response.data;
  },
  async getProductPerformanceDetailed(params?: AnalyticsQueryParams): Promise<ProductPerformanceDetailedResponse> {
    const response = await apiClient.get(`/analytics/product-performance-detailed`, { params });
    return response.data;
  },
  async getPaymentTrends(params?: AnalyticsQueryParams): Promise<PaymentTrendsResponse> {
    const response = await apiClient.get(`/analytics/payment-trends`, { params });
    return response.data;
  },
  async getOrderStatsDetailed(params?: AnalyticsQueryParams): Promise<OrderStatsDetailedResponse> {
    const response = await apiClient.get(`/analytics/order-stats-detailed`, { params });
    return response.data;
  },

  // Group 2
  async getRevenueComposition(params?: AnalyticsQueryParams): Promise<RevenueCompositionResponse> {
    const response = await apiClient.get(`/analytics/revenue-composition`, { params });
    return response.data;
  },
  async getOrderStatusFlow(params?: AnalyticsQueryParams): Promise<OrderStatusFlowResponse> {
    const response = await apiClient.get(`/analytics/order-status-flow`, { params });
    return response.data;
  },
  async getDayOfWeekStats(params?: AnalyticsQueryParams): Promise<DayOfWeekStatsResponse> {
    const response = await apiClient.get(`/analytics/day-of-week-stats`, { params });
    return response.data;
  },
  async getOrderValueDistribution(params?: AnalyticsQueryParams & { group_by?: string }): Promise<OrderValueDistributionResponse> {
    const response = await apiClient.get(`/analytics/order-value-distribution`, { params });
    return response.data;
  },
  async getItemQuantityDistribution(params?: AnalyticsQueryParams): Promise<ItemQuantityDistributionResponse> {
    const response = await apiClient.get(`/analytics/item-quantity-distribution`, { params });
    return response.data;
  },

  // Group 3
  async getOrderFlow(params?: AnalyticsQueryParams): Promise<SankeyData> {
    const response = await apiClient.get(`/analytics/order-flow`, { params });
    return response.data;
  },
  async getRevenueWaterfall(params?: AnalyticsQueryParams & { date?: string }): Promise<WaterfallResponse> {
    const response = await apiClient.get(`/analytics/revenue-waterfall`, { params });
    return response.data;
  },
  async getInventoryWaterfall(params?: AnalyticsQueryParams & { date?: string }): Promise<WaterfallResponse> {
    const response = await apiClient.get(`/analytics/inventory-waterfall`, { params });
    return response.data;
  },
  async getOrderTimeline(params?: AnalyticsQueryParams & { date?: string }): Promise<OrdersTimelineResponse> {
    const response = await apiClient.get(`/analytics/order-timeline`, { params });
    return response.data;
  },

  /**
   * Query Thesys C1 for conversational analytics
   */
  async queryC1(request: C1QueryRequest): Promise<C1QueryResponse> {
    const response = await apiClient.post(
      `/analytics/query`,
      request
    );
    return response.data;
  },
};
