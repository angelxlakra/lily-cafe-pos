// ========================================
// Axios Client Configuration
// Lily Cafe POS System - Frontend
// ========================================

import axios, {
  AxiosError,
  AxiosInstance,
  InternalAxiosRequestConfig,
} from "axios";
import type {
  LoginRequest,
  LoginResponse,
  MenuItem,
  CreateMenuItemRequest,
  UpdateMenuItemRequest,
  CreateCategoryRequest,
  Category,
  Order,
  CreateOrderRequest,
  UpdateOrderRequest,
  OrderItemsUpdateRequest,
  AddPaymentRequest,
  Payment,
  QueryParams,
  AppConfig,
} from "../types";

// ========================================
// Constants
// ========================================

/**
 * Get the backend API base URL dynamically based on the current hostname.
 * If running on localhost, uses localhost. Otherwise uses the same IP/hostname.
 */
const getApiBaseUrl = (): string => {
  // Allow manual override via environment variable
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  // Detect current hostname from window location
  const currentHost =
    typeof window !== "undefined" ? window.location.hostname : "localhost";

  // Use localhost for 127.0.0.1 or localhost
  const backendHost =
    currentHost === "127.0.0.1" || currentHost === "localhost"
      ? "localhost"
      : currentHost;

  // Backend runs on port 8000
  return `http://${backendHost}:8000`;
};

const API_BASE_URL = getApiBaseUrl();
const TOKEN_KEY = "lily_cafe_auth_token";

// ========================================
// Axios Instance
// ========================================

const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
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
      console.error("Network error:", error.message);
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
    const response = await apiClient.post<LoginResponse>(
      "/auth/login",
      credentials
    );
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
  getMenuItems: async (params?: QueryParams): Promise<MenuItem[]> => {
    const response = await apiClient.get<MenuItem[]>("/menu", {
      params,
    });
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
    const response = await apiClient.post<MenuItem>("/menu", data);
    return response.data;
  },

  /**
   * Update an existing menu item (requires auth)
   */
  updateMenuItem: async (
    id: number,
    data: UpdateMenuItemRequest
  ): Promise<MenuItem> => {
    const response = await apiClient.patch<MenuItem>(`/menu/${id}`, data);
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
  getCategories: async (): Promise<Category[]> => {
    const response = await apiClient.get<Category[]>("/categories");
    return response.data;
  },

  /**
   * Create a new category (requires auth)
   */
  createCategory: async (data: CreateCategoryRequest): Promise<Category> => {
    const response = await apiClient.post<Category>("/categories", data);
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
  createOrUpdateOrder: async (
    data: CreateOrderRequest
  ): Promise<Order> => {
    const response = await apiClient.post<Order>("/orders", data);
    return response.data;
  },

  /**
   * Get all active (unpaid) orders
   */
  getActiveOrders: async (): Promise<Order[]> => {
    const response = await apiClient.get<Order[]>(
      "/orders/active"
    );
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
    data: OrderItemsUpdateRequest
  ): Promise<Order> => {
    const response = await apiClient.put<Order>(`/orders/${id}`, data);
    return response.data;
  },

  /**
   * Cancel an order (admin only, requires auth)
   */
  cancelOrder: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(
      `/orders/${id}`
    );
    return response.data;
  },

  /**
   * Get order history with optional filters (requires auth)
   */
  getOrderHistory: async (
    params?: QueryParams
  ): Promise<Order[]> => {
    const response = await apiClient.get<Order[]>("/orders/history", {
      params,
    });
    return response.data;
  },

  /**
   * Update order status or customer name
   */
  patchOrder: async (id: number, data: UpdateOrderRequest): Promise<Order> => {
    const response = await apiClient.patch<Order>(`/orders/${id}`, data);
    return response.data;
  },

  /**
   * Update the served quantity of an order item (supports partial serving)
   */
  updateItemServedStatus: async (
    orderId: number,
    itemId: number,
    quantityToServe: number
  ): Promise<{ message: string; item_id: number; quantity_served: number; is_served: boolean }> => {
    const response = await apiClient.patch<{ message: string; item_id: number; quantity_served: number; is_served: boolean }>(
      `/orders/${orderId}/items/${itemId}/served?quantity_to_serve=${quantityToServe}`
    );
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
  addPayments: async (
    orderId: number,
    data: AddPaymentRequest
  ): Promise<Payment[]> => {
    const response = await apiClient.post<Payment[]>(
      `/orders/${orderId}/payments/batch`,
      data
    );
    return response.data;
  },

  /**
   * Update/replace all payments for an order (requires auth)
   */
  updatePayments: async (
    orderId: number,
    data: AddPaymentRequest
  ): Promise<Payment[]> => {
    const response = await apiClient.put<Payment[]>(
      `/orders/${orderId}/payments`,
      data
    );
    return response.data;
  },

  /**
   * Generate and download receipt PDF
   */
  getReceipt: async (orderId: number): Promise<Blob> => {
    const response = await apiClient.get(`/orders/${orderId}/receipt`, {
      responseType: "blob",
    });
    return response.data;
  },

  /**
   * Print receipt (opens print dialog)
   */
  printReceipt: async (orderId: number): Promise<void> => {
    const blob = await paymentsApi.getReceipt(orderId);
    const url = window.URL.createObjectURL(blob);
    const printWindow = window.open(url, "_blank");
    if (printWindow) {
      printWindow.addEventListener("load", () => {
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
    const response = await apiClient.get<AppConfig>("/config");
    return response.data;
  },
};

// ========================================
// Export default API client
// ========================================

export default apiClient;
