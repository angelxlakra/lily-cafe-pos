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
  price: number; // Price in paise
  category_id: number;
  category: Category;
  is_vegetarian: boolean;
  is_available: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateMenuItemRequest {
  name: string;
  description?: string | null;
  price: number; // Price in paise
  category_id: number;
  is_vegetarian?: boolean;
}

export interface UpdateMenuItemRequest {
  name?: string;
  description?: string | null;
  price?: number; // Price in paise
  category_id?: number;
  is_vegetarian?: boolean;
  is_available?: boolean;
}

// ========================================
// Category Types
// ========================================

export interface Category {
  id: number;
  name: string;
  created_at: string;
}

export interface CreateCategoryRequest {
  name: string;
}

// ========================================
// Order Types
// ========================================

export interface OrderItem {
  id: number;
  menu_item_id: number;
  menu_item_name: string;
  quantity: number;
  quantity_served: number;
  unit_price: number; // Price in paise
  subtotal: number; // Price in paise
  is_served: boolean;
  is_parcel: boolean;
}

export interface Order {
  id: number;
  order_number: string;
  table_number: number;
  customer_name: string | null;
  status: 'active' | 'paid' | 'canceled';
  order_items: OrderItem[];
  subtotal: number;
  gst_amount: number;
  total_amount: number;
  created_at: string;
  updated_at: string;
  payments: Payment[];
}

export interface CreateOrderRequest {
  table_number: number;
  customer_name?: string | null;
  items: Array<{
    menu_item_id: number;
    quantity: number;
    is_parcel?: boolean;
  }>;
}

export interface UpdateOrderRequest {
  status?: 'active' | 'paid' | 'canceled';
  customer_name?: string | null;
}

export interface OrderItemsUpdateRequest {
  items: Array<{
    menu_item_id: number;
    quantity: number;
    is_parcel?: boolean;
  }>;
  customer_name?: string | null;
  table_number?: number; // Optional - change table number
}

// ========================================
// Payment Types
// ========================================

export type PaymentMethod = 'upi' | 'cash' | 'card';

export interface Payment {
  id: number;
  payment_method: PaymentMethod;
  amount: number;
  created_at: string;
}

export interface PaymentCreateRequest {
  payment_method: PaymentMethod;
  amount: number;
}

export interface AddPaymentRequest {
  payments: PaymentCreateRequest[];
}

// ========================================
// Order History Types
// ========================================

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
  available_only?: boolean;
  category_id?: number;
  search?: string;
  status?: 'active' | 'paid' | 'canceled';
  table_number?: number;
  today_only?: boolean;
  date?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
