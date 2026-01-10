// ========================================
// Protected Route Component
// Requires authentication to access
// ========================================

import { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import type { UserRole } from '../types';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: UserRole;
}

/**
 * Wrapper component that protects routes requiring authentication.
 * Redirects to login page if user is not authenticated.
 * Optionally checks for specific role requirements.
 *
 * @example
 * ```tsx
 * // Basic authentication protection
 * <Route
 *   path="/admin/orders"
 *   element={
 *     <ProtectedRoute>
 *       <AdminOrdersPage />
 *     </ProtectedRoute>
 *   }
 * />
 *
 * // Owner-only route protection
 * <Route
 *   path="/admin/analytics"
 *   element={
 *     <ProtectedRoute requiredRole="owner">
 *       <AnalyticsPage />
 *     </ProtectedRoute>
 *   }
 * />
 * ```
 */
export default function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { isAuthenticated, role } = useAuth();

  if (!isAuthenticated) {
    // Redirect to login page if not authenticated
    return <Navigate to="/login" replace />;
  }

  // Check role requirement if specified
  if (requiredRole && role !== requiredRole) {
    // Redirect to active orders page if user doesn't have required role
    return <Navigate to="/admin/active-orders" replace />;
  }

  // Render children if authenticated and has required role (if specified)
  return <>{children}</>;
}
