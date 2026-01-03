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
  // v0.2 Patch - Denomination counts
  opening_500s: number;
  opening_200s: number;
  opening_100s: number;
  opening_50s: number;
  opening_20s: number;
  opening_10s: number;
  closing_500s: number | null;
  closing_200s: number | null;
  closing_100s: number | null;
  closing_50s: number | null;
  closing_20s: number | null;
  closing_10s: number | null;
}

export interface CashCounterOpen {
  date: string; // ISO date format (YYYY-MM-DD)
  // v0.2 Patch - Denomination counting replaces single balance
  opening_500s: number;
  opening_200s: number;
  opening_100s: number;
  opening_50s: number;
  opening_20s: number;
  opening_10s: number;
  notes?: string;
}

export interface CashCounterClose {
  date: string; // ISO date format (YYYY-MM-DD)
  // v0.2 Patch - Denomination counting replaces single balance
  closing_500s: number;
  closing_200s: number;
  closing_100s: number;
  closing_50s: number;
  closing_20s: number;
  closing_10s: number;
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
