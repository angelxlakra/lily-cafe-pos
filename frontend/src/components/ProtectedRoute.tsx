// ========================================
// Protected Route Component
// Requires authentication to access
// ========================================

import { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface ProtectedRouteProps {
  children: ReactNode;
}

/**
 * Wrapper component that protects routes requiring authentication.
 * Redirects to login page if user is not authenticated.
 *
 * @example
 * ```tsx
 * <Route
 *   path="/admin/orders"
 *   element={
 *     <ProtectedRoute>
 *       <AdminOrdersPage />
 *     </ProtectedRoute>
 *   }
 * />
 * ```
 */
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    // Redirect to login page if not authenticated
    return <Navigate to="/login" replace />;
  }

  // Render children if authenticated
  return <>{children}</>;
}
