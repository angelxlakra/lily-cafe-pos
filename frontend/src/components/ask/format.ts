// Formatting for figures the owner reads on a phone. Amounts arrive from the
// backend already in rupees; nothing here converts, only presents.

const inrFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

const inrPreciseFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const numberFormatter = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 });

export function inr(value: number | null | undefined, precise = false): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return (precise ? inrPreciseFormatter : inrFormatter).format(value);
}

export function num(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return numberFormatter.format(value);
}

export function pct(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return `${value.toFixed(digits)}%`;
}

/** "2026-09-19" → "Sat 19 Sep" */
export function dayLabel(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  const date = new Date(y, m - 1, d);
  return date.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' });
}

/** "2026-09-19" → "19 Sep" */
export function shortDay(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

/** snake_case_rupees → "Snake case" (unit suffixes dropped; shown via formatting) */
export function humanize(key: string): string {
  const cleaned = key.replace(/_rupees$/, '').replace(/_percentage$/, ' %').replace(/_/g, ' ');
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

export function isRupeeKey(key: string): boolean {
  return key.endsWith('_rupees');
}

export function isPercentKey(key: string): boolean {
  return key.endsWith('_percentage') || key.endsWith('_rate') || key.endsWith('_ratio');
}
