// ========================================
// Ask API Client — natural-language questions answered by fixed reports
// ========================================

import apiClient from './client';

export type PeriodOut =
  | { kind: 'named'; name: string }
  | { kind: 'month'; year: number; month: number }
  | { kind: 'range'; start: string; end: string }
  | { kind: 'since'; start: string }
  | { kind: 'day'; date: string };

/** What the model decided. Echoed back so the next question keeps context. */
export interface RouterDecision {
  action: 'report' | 'clarify' | 'unsupported';
  report: string | null;
  period: PeriodOut | null;
  dish: string | null;
  comparison: string | null;
  limit: number | null;
  message: string | null;
}

export interface AskResponse {
  kind: 'report' | 'clarify' | 'unsupported';
  report_id: string | null;
  title: string | null;
  period_label: string | null;
  dish: string | null;
  /** One sentence written by the backend from the report's own numbers. */
  caption: string | null;
  data: Record<string, unknown> | null;
  message: string | null;
  candidates: string[];
  decision: RouterDecision | null;
}

export interface AskRequest {
  question: string;
  previous?: RouterDecision | null;
  previous_question?: string | null;
}

export async function askQuestion(request: AskRequest): Promise<AskResponse> {
  const response = await apiClient.post<AskResponse>('/ask', request);
  return response.data;
}

// ========================================
// Morning digest — computed in code, no model involved
// ========================================

export interface DigestLine {
  /** 'revenue' | 'top_item' | 'cash' | 'stock' | 'month' */
  kind: string;
  text: string;
  numbers: Record<string, unknown>;
}

export interface DigestFlag {
  rule: string;
  severity: 'info' | 'warn';
  sentence: string;
  numbers: Record<string, unknown>;
}

export interface Digest {
  /** The IST calendar day the digest is about. */
  date: string;
  lines: DigestLine[];
  flags: DigestFlag[];
  email_sent_at: string | null;
}

export async function fetchDigest(): Promise<Digest | null> {
  const response = await apiClient.get<{ digest: Digest | null }>('/ask/digest');
  return response.data.digest;
}
