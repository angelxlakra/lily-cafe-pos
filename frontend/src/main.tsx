import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import { ThemeProvider } from './contexts/ThemeContext.tsx'
import App from './App.tsx'
import ApiTestPage from './pages/ApiTestPage.tsx'
import TablesPage from './pages/TablesPage.tsx'
import OrderPage from './pages/OrderPage.tsx'
import ActiveOrdersPage from './pages/ActiveOrdersPage.tsx'
import LoginPage from './pages/LoginPage.tsx'
import AdminActiveOrdersPage from './pages/AdminActiveOrdersPage.tsx'
import MenuManagementPage from './pages/MenuManagementPage.tsx'
import OrderHistoryPage from './pages/OrderHistoryPage.tsx'
import InventoryPage from './pages/InventoryPage.tsx'
import CashCounterPage from './pages/CashCounterPage.tsx'
import ProtectedRoute from './components/ProtectedRoute.tsx'
import './index.css'

// Configure TanStack Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Retry failed requests 3 times before giving up
      retry: 3,
      // Retry with exponential backoff (1s, 2s, 4s)
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      // Stale time: Data is considered fresh for 5 minutes
      staleTime: 5 * 60 * 1000,
      // Cache time: Keep unused data in cache for 10 minutes
      gcTime: 10 * 60 * 1000,
      // Refetch on window focus for active orders and menu
      refetchOnWindowFocus: true,
      // Don't refetch on mount if data is fresh
      refetchOnMount: false,
    },
    mutations: {
      // Retry mutations once on failure
      retry: 1,
      // Retry after 1 second
      retryDelay: 1000,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <Toaster
            position="top-center"
            expand={false}
            richColors
            closeButton
            duration={3000}
          />
          <Routes>
            {/* Redirect root to tables page */}
            <Route path="/" element={<Navigate to="/tables" replace />} />

            {/* Waiter Interface Routes */}
            <Route path="/tables" element={<TablesPage />} />
            <Route path="/order/:tableNumber" element={<OrderPage />} />
            <Route path="/active-orders" element={<ActiveOrdersPage />} />

            {/* Admin Authentication */}
            <Route path="/login" element={<LoginPage />} />

            {/* Admin Protected Routes */}
            <Route
              path="/admin/active-orders"
              element={
                <ProtectedRoute>
                  <AdminActiveOrdersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/menu"
              element={
                <ProtectedRoute>
                  <MenuManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/order-history"
              element={
                <ProtectedRoute>
                  <OrderHistoryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/inventory"
              element={
                <ProtectedRoute>
                  <InventoryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/cash-counter"
              element={
                <ProtectedRoute>
                  <CashCounterPage />
                </ProtectedRoute>
              }
            />

            {/* Dev/Testing Routes */}
            <Route path="/test" element={<App />} />
            <Route path="/api-test" element={<ApiTestPage />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
