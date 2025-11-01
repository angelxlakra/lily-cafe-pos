// ========================================
// Axios Client Configuration
// Lily Cafe POS System - Frontend
// ========================================

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type {
  LoginRequest,
  LoginResponse,
  MenuItem,
  MenuItemsResponse,
  CreateMenuItemRequest,
  UpdateMenuItemRequest,
  CategoriesResponse,
  CreateCategoryRequest,
  Category,
  Order,
  CreateOrderRequest,
  UpdateOrderRequest,
  ActiveOrdersResponse,
  AddPaymentRequest,
  PaymentResponse,
  OrderHistoryResponse,
  QueryParams,
  AppConfig,
} from '../types';

// ========================================
// Constants
// ========================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const TOKEN_KEY = 'lily_cafe_auth_token';

// ========================================
// Axios Instance
// ========================================

const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ========================================
// Token Management
// ========================================

export const getAuthToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

export const setAuthToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

export const removeAuthToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

// ========================================
// Request Interceptor
// ========================================

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add JWT token to headers if available
    const token = getAuthToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// ========================================
// Response Interceptor
// ========================================

apiClient.interceptors.response.use(
  (response) => {
    // Return response data directly
    return response;
  },
  (error: AxiosError) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      removeAuthToken();
      // Optionally redirect to login page
      // window.location.href = '/login';
    }

    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message);
    }

    return Promise.reject(error);
  }
);

// ========================================
// Authentication API
// ========================================

export const authApi = {
  /**
   * Login with username and password
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login', credentials);
    // Save token to localStorage
    if (response.data.access_token) {
      setAuthToken(response.data.access_token);
    }
    return response.data;
  },

  /**
   * Logout - clear token
   */
  logout: (): void => {
    removeAuthToken();
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: (): boolean => {
    return getAuthToken() !== null;
  },
};

// ========================================
// Menu Items API
// ========================================

export const menuApi = {
  /**
   * Get all menu items with optional filters
   */
  getMenuItems: async (params?: QueryParams): Promise<MenuItemsResponse> => {
    const response = await apiClient.get<MenuItemsResponse>('/menu', { params });
    return response.data;
  },

  /**
   * Get a single menu item by ID
   */
  getMenuItem: async (id: number): Promise<MenuItem> => {
    const response = await apiClient.get<MenuItem>(`/menu/${id}`);
    return response.data;
  },

  /**
   * Create a new menu item (requires auth)
   */
  createMenuItem: async (data: CreateMenuItemRequest): Promise<MenuItem> => {
    const response = await apiClient.post<MenuItem>('/menu', data);
    return response.data;
  },

  /**
   * Update an existing menu item (requires auth)
   */
  updateMenuItem: async (id: number, data: UpdateMenuItemRequest): Promise<MenuItem> => {
    const response = await apiClient.put<MenuItem>(`/menu/${id}`, data);
    return response.data;
  },

  /**
   * Delete (soft delete) a menu item (requires auth)
   */
  deleteMenuItem: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/menu/${id}`);
    return response.data;
  },
};

// ========================================
// Categories API
// ========================================

export const categoriesApi = {
  /**
   * Get all categories
   */
  getCategories: async (): Promise<CategoriesResponse> => {
    const response = await apiClient.get<CategoriesResponse>('/categories');
    return response.data;
  },

  /**
   * Create a new category (requires auth)
   */
  createCategory: async (data: CreateCategoryRequest): Promise<Category> => {
    const response = await apiClient.post<Category>('/categories', data);
    return response.data;
  },
};

// ========================================
// Orders API
// ========================================

export const ordersApi = {
  /**
   * Create a new order or update existing order
   */
  createOrUpdateOrder: async (data: CreateOrderRequest | UpdateOrderRequest): Promise<Order> => {
    const response = await apiClient.post<Order>('/orders', data);
    return response.data;
  },

  /**
   * Get all active (unpaid) orders
   */
  getActiveOrders: async (): Promise<ActiveOrdersResponse> => {
    const response = await apiClient.get<ActiveOrdersResponse>('/orders/active');
    return response.data;
  },

  /**
   * Get a single order by ID with full details
   */
  getOrderById: async (id: number): Promise<Order> => {
    const response = await apiClient.get<Order>(`/orders/${id}`);
    return response.data;
  },

  /**
   * Update an order (admin only, requires auth)
   */
  updateOrder: async (
    id: number,
    data: { items: Array<{ menu_item_id: number; quantity: number }> }
  ): Promise<Order> => {
    const response = await apiClient.put<Order>(`/orders/${id}`, data);
    return response.data;
  },

  /**
   * Cancel an order (admin only, requires auth)
   */
  cancelOrder: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/orders/${id}`);
    return response.data;
  },

  /**
   * Get order history with optional filters (requires auth)
   */
  getOrderHistory: async (params?: QueryParams): Promise<OrderHistoryResponse> => {
    const response = await apiClient.get<OrderHistoryResponse>('/orders/history', { params });
    return response.data;
  },
};

// ========================================
// Payments API
// ========================================

export const paymentsApi = {
  /**
   * Add payment(s) to an order (requires auth)
   */
  addPayments: async (orderId: number, data: AddPaymentRequest): Promise<PaymentResponse> => {
    const response = await apiClient.post<PaymentResponse>(`/orders/${orderId}/payments`, data);
    return response.data;
  },

  /**
   * Generate and download receipt PDF
   */
  getReceipt: async (orderId: number): Promise<Blob> => {
    const response = await apiClient.get(`/orders/${orderId}/receipt`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Print receipt (opens print dialog)
   */
  printReceipt: async (orderId: number): Promise<void> => {
    const blob = await paymentsApi.getReceipt(orderId);
    const url = window.URL.createObjectURL(blob);
    const printWindow = window.open(url, '_blank');
    if (printWindow) {
      printWindow.addEventListener('load', () => {
        printWindow.print();
        window.URL.revokeObjectURL(url);
      });
    }
  },
};

// ========================================
// Configuration API
// ========================================

export const configApi = {
  /**
   * Get app configuration
   */
  getConfig: async (): Promise<AppConfig> => {
    const response = await apiClient.get<AppConfig>('/config');
    return response.data;
  },
};

// ========================================
// Export default API client
// ========================================

export default apiClient;
