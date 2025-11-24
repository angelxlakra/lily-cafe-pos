export interface DailyCashCounter {
  id: number;
  date: string;
  opening_balance: number;
  closing_balance: number | null;
  expected_closing: number | null;
  variance: number | null;
  notes: string | null;
  opened_by: string;
  closed_by: string | null;
  verified_by: string | null;
  opened_at: string;
  closed_at: string | null;
  verified_at: string | null;
  is_verified: boolean;
  status: 'open' | 'closed_pending_verification' | 'verified';
}

export interface CashCounterOpen {
  opening_balance: number;
  notes?: string;
}

export interface CashCounterClose {
  closing_balance: number;
  notes?: string;
}

export interface CashCounterVerify {
  owner_password: string;
  notes?: string;
}

export interface CashCounterHistoryResponse {
  history: DailyCashCounter[];
  total: number;
  limit: number;
  offset: number;
}
