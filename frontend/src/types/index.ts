// ========================================
// TypeScript Type Definitions
// Lily Cafe POS System - Frontend
// ========================================

// ========================================
// Authentication Types
// ========================================

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// ========================================
// Menu Item Types
// ========================================

export interface MenuItem {
  id: number;
  name: string;
  description: string | null;
  price: number; // Price in rupees (display value)
  category: string;
  is_available: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface MenuItemsResponse {
  items: MenuItem[];
}

export interface CreateMenuItemRequest {
  name: string;
  description?: string | null;
  price: number;
  category: string;
  is_available?: boolean;
}

export interface UpdateMenuItemRequest {
  name?: string;
  description?: string | null;
  price?: number;
  category?: string;
  is_available?: boolean;
}

// ========================================
// Category Types
// ========================================

export interface Category {
  id: number;
  name: string;
  created_at?: string;
}

export interface CategoriesResponse {
  categories: Category[];
}

export interface CreateCategoryRequest {
  name: string;
}

// ========================================
// Order Types
// ========================================

export interface OrderItem {
  id?: number;
  menu_item_id?: number;
  menu_item_name: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface Order {
  id: number;
  order_number: string;
  table_number: number;
  customer_name: string | null;
  status: 'active' | 'paid' | 'canceled';
  items: OrderItem[];
  subtotal: number;
  gst_amount: number;
  total_amount: number;
  created_at: string;
  updated_at?: string;
}

export interface CreateOrderRequest {
  table_number: number;
  customer_name?: string | null;
  items: Array<{
    menu_item_id: number;
    quantity: number;
  }>;
}

export interface UpdateOrderRequest {
  order_id: number;
  items: Array<{
    menu_item_id: number;
    quantity: number;
  }>;
}

export interface ActiveOrderSummary {
  id: number;
  order_number: string;
  table_number: number;
  customer_name: string | null;
  item_count: number;
  total_amount: number;
  created_at: string;
}

export interface ActiveOrdersResponse {
  orders: ActiveOrderSummary[];
}

// ========================================
// Payment Types
// ========================================

export type PaymentMethod = 'upi' | 'cash' | 'card';

export interface Payment {
  method: PaymentMethod;
  amount: number;
}

export interface AddPaymentRequest {
  payments: Payment[];
}

export interface PaymentResponse {
  order_id: number;
  total_amount: number;
  total_paid: number;
  payments: Payment[];
  status: string;
}

// ========================================
// Order History Types
// ========================================

export interface OrderHistoryItem {
  id: number;
  order_number: string;
  table_number: number;
  customer_name: string | null;
  total_amount: number;
  payment_methods: PaymentMethod[];
  created_at: string;
}

export interface OrderHistoryResponse {
  orders: OrderHistoryItem[];
  total: number;
  date: string;
}

// ========================================
// Configuration Types
// ========================================

export interface AppConfig {
  restaurant_name: string;
  max_tables: number;
  gst_rate: number;
}

// ========================================
// Error Response Types
// ========================================

export interface ErrorResponse {
  detail: string;
}

// ========================================
// API Request Options
// ========================================

export interface QueryParams {
  category?: string;
  available_only?: boolean;
  date?: string;
  limit?: number;
  skip?: number;
}
