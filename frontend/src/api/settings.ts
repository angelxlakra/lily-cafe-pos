// frontend/src/api/settings.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from './client'

export type Settings = Record<string, string>

interface SettingsResponse {
  settings: Settings
}

// ============================================================================
// API functions
// ============================================================================

async function fetchSettings(): Promise<Settings> {
  const response = await apiClient.get<SettingsResponse>('/settings')
  return response.data.settings
}

async function patchSettings(updates: Settings): Promise<Settings> {
  const response = await apiClient.put<SettingsResponse>('/settings', { settings: updates })
  return response.data.settings
}

// ============================================================================
// TanStack Query hooks
// ============================================================================

export function useSettings() {
  return useQuery<Settings>({
    queryKey: ['settings'],
    queryFn: fetchSettings,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

export function useUpdateSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: patchSettings,
    onSuccess: () => {
      // Invalidate both settings and public config (config reads from same store)
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      queryClient.invalidateQueries({ queryKey: ['config'] })
    },
  })
}
