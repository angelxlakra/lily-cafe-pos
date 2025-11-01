// ========================================
// useConfig Hook
// Fetches application configuration from backend
// ========================================

import { useQuery } from '@tanstack/react-query';
import { configApi } from '../api/client';

export const configQueryKeys = {
  all: ['config'] as const,
};

/**
 * Retrieves application configuration (restaurant details, GST rate, etc.).
 */
export const useAppConfig = () => {
  return useQuery({
    queryKey: configQueryKeys.all,
    queryFn: () => configApi.getConfig(),
    // Configuration changes rarely, cache for an hour
    staleTime: 60 * 60 * 1000,
  });
};
