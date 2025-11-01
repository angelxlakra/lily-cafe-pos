// ========================================
// useAuth Hook
// Authentication state and operations
// ========================================

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../api/client';
import type { LoginRequest, LoginResponse } from '../types';
import { useState, useEffect } from 'react';

interface UseAuthReturn {
  // State
  isAuthenticated: boolean;
  isLoggingIn: boolean;
  loginError: string | null;

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
 *
 * @example
 * ```tsx
 * const { isAuthenticated, login, logout, isLoggingIn, loginError } = useAuth();
 *
 * const handleLogin = async () => {
 *   try {
 *     await login({ username: 'admin', password: 'changeme123' });
 *     // Success - redirect or show success message
 *   } catch (error) {
 *     // Error is handled internally
 *   }
 * };
 * ```
 */
export const useAuth = (): UseAuthReturn => {
  const queryClient = useQueryClient();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(authApi.isAuthenticated());

  // Check authentication status on mount and when localStorage changes
  useEffect(() => {
    const checkAuth = () => {
      setIsAuthenticated(authApi.isAuthenticated());
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
    onSuccess: () => {
      // Update authentication state
      setIsAuthenticated(true);
      // Invalidate all queries to refetch with new auth
      queryClient.invalidateQueries();
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
    // Update authentication state
    setIsAuthenticated(false);
    // Clear all cached data
    queryClient.clear();
  };

  return {
    isAuthenticated,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error ? (loginMutation.error as Error).message : null,
    login: loginMutation.mutateAsync,
    logout,
  };
};
