import apiClient from './client';
import type {
  DailyCashCounter,
  CashCounterOpen,
  CashCounterClose,
  CashCounterVerify,
  CashCounterHistoryResponse
} from '../types/cash';

export const cashApi = {
  openCounter: async (data: CashCounterOpen): Promise<DailyCashCounter> => {
    const response = await apiClient.post<DailyCashCounter>('/cash-counter/open', data);
    return response.data;
  },

  closeCounter: async (data: CashCounterClose): Promise<DailyCashCounter> => {
    const response = await apiClient.post<DailyCashCounter>('/cash-counter/close', data);
    return response.data;
  },

  verifyCounter: async (id: number, data: CashCounterVerify): Promise<DailyCashCounter> => {
    const response = await apiClient.post<DailyCashCounter>(`/cash-counter/verify/${id}`, data);
    return response.data;
  },

  getTodayCounter: async (): Promise<DailyCashCounter | null> => {
    try {
      const response = await apiClient.get<any>('/cash-counter/today');
      // Backend returns 200 OK with a message if not open, so we check for id
      if (!response.data.id) {
        return null;
      }
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  getHistory: async (params?: { limit?: number; offset?: number }): Promise<CashCounterHistoryResponse> => {
    const response = await apiClient.get<CashCounterHistoryResponse>('/cash-counter/history', { params });
    return response.data;
  },
};
