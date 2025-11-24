import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cashApi } from '../api/cash';
import type {
  CashCounterOpen,
  CashCounterClose,
  CashCounterVerify
} from '../types/cash';

export const cashKeys = {
  all: ['cash-counter'] as const,
  today: () => [...cashKeys.all, 'today'] as const,
  history: (params?: any) => [...cashKeys.all, 'history', params] as const,
};

export function useCashCounterToday() {
  return useQuery({
    queryKey: cashKeys.today(),
    queryFn: cashApi.getTodayCounter,
    retry: false, // Don't retry on 404 (no counter open)
  });
}

export function useCashCounterHistory(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: cashKeys.history(params),
    queryFn: () => cashApi.getHistory(params),
  });
}

export function useOpenCashCounter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CashCounterOpen) => cashApi.openCounter(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cashKeys.today() });
      queryClient.invalidateQueries({ queryKey: cashKeys.history() });
    },
  });
}

export function useCloseCashCounter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CashCounterClose) => cashApi.closeCounter(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cashKeys.today() });
      queryClient.invalidateQueries({ queryKey: cashKeys.history() });
    },
  });
}

export function useVerifyCashCounter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: CashCounterVerify }) => 
      cashApi.verifyCounter(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cashKeys.today() });
      queryClient.invalidateQueries({ queryKey: cashKeys.history() });
    },
  });
}
