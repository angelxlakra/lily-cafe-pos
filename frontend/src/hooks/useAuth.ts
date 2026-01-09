// ========================================
// useAuth Hook
// Authentication state and operations
// ========================================

import { useMutation, useQueryClient, QueryClient } from '@tanstack/react-query';
import { authApi } from '../api/client';
import type { LoginRequest, LoginResponse, User, UserRole } from '../types';
import { useState, useEffect } from 'react';

interface UseAuthReturn {
  // State
  isAuthenticated: boolean;
  isLoggingIn: boolean;
  loginError: string | null;
  user: User | null;
  role: UserRole | null;

  // Actions
  login: (credentials: LoginRequest) => Promise<LoginResponse>;
  logout: () => void;
}

/**
 * Custom hook for authentication
 *
 * Features:
 * - Login mutation with error handling
 * - Logout with cache invalidation
 * - Authentication state tracking
 * - User role management
 *
 * @example
 * ```tsx
 * const { isAuthenticated, login, logout, isLoggingIn, loginError, user, role } = useAuth();
 *
 * const handleLogin = async () => {
 *   try {
 *     await login({ username: 'admin', password: 'changeme123' });
 *     // Success - redirect or show success message
 *   } catch (error) {
 *     // Error is handled internally
 *   }
 * };
 *
 * // Check if user is owner
 * if (role === 'owner') {
 *   // Show analytics link
 * }
 * ```
 */
export const useAuth = (): UseAuthReturn => {
  // Get queryClient but handle case where it might not be available
  let queryClient: QueryClient | undefined;
  try {
    queryClient = useQueryClient();
  } catch (error) {
    // QueryClient not available in context - that's ok, we'll work without it
    console.warn('QueryClient not available in useAuth context');
  }

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(authApi.isAuthenticated());
  const [user, setUser] = useState<User | null>(null);
  const role = user?.role || null;

  // Fetch user data if authenticated
  const fetchUser = async () => {
    if (authApi.isAuthenticated()) {
      try {
        const userData = await authApi.verifyToken();
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        // Token is invalid or expired
        console.error('Failed to verify token:', error);
        authApi.logout();
        setUser(null);
        setIsAuthenticated(false);
      }
    } else {
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  // Check authentication status on mount and when localStorage changes
  useEffect(() => {
    const checkAuth = () => {
      fetchUser();
    };

    // Check on mount
    checkAuth();

    // Listen for storage events (login/logout in other tabs)
    window.addEventListener('storage', checkAuth);

    return () => {
      window.removeEventListener('storage', checkAuth);
    };
  }, []);

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: (credentials: LoginRequest) => authApi.login(credentials),
    onSuccess: async () => {
      // Fetch user data including role
      await fetchUser();
      // Invalidate all queries to refetch with new auth (if queryClient available)
      if (queryClient) {
        queryClient.invalidateQueries();
      }
    },
    onError: (error) => {
      // Error is captured in the mutation state
      console.error('Login failed:', error);
    },
  });

  // Logout function
  const logout = () => {
    // Clear token
    authApi.logout();
    // Clear user and role
    setUser(null);
    // Update authentication state
    setIsAuthenticated(false);
    // Clear all cached data (if queryClient available)
    if (queryClient) {
      queryClient.clear();
    }
  };

  return {
    isAuthenticated,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error ? (loginMutation.error as Error).message : null,
    user,
    role,
    login: loginMutation.mutateAsync,
    logout,
  };
};
