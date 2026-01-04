// ========================================
// Analytics API Client
// Lily Cafe POS System - Frontend
// ========================================

import axios from 'axios';

// Get API base URL
const getApiBaseUrl = (): string => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  const currentHost =
    typeof window !== 'undefined' ? window.location.hostname : 'localhost';

  const backendHost =
    currentHost === '127.0.0.1' || currentHost === 'localhost'
      ? 'localhost'
      : currentHost;

  return `http://${backendHost}:8000`;
};

const API_BASE_URL = getApiBaseUrl();

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
}

// ========================================
// API Functions
// ========================================

export const analyticsApi = {
  /**
   * Get revenue analytics
   */
  async getRevenue(params?: AnalyticsQueryParams): Promise<RevenueData> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/analytics/revenue`, {
      params,
    });
    return response.data;
  },

  /**
   * Get product performance analytics
   */
  async getProducts(params?: AnalyticsQueryParams): Promise<ProductPerformance> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/analytics/products`, {
      params,
    });
    return response.data;
  },

  /**
   * Get order statistics
   */
  async getOrderStats(params?: AnalyticsQueryParams): Promise<OrderStatistics> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/analytics/orders`, {
      params,
    });
    return response.data;
  },

  /**
   * Query Thesys C1 for conversational analytics
   */
  async queryC1(request: C1QueryRequest): Promise<C1QueryResponse> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/analytics/query`,
      request
    );
    return response.data;
  },
};
