// Pure helpers for the daily purchase sheet.

interface PickableItem {
  id: number;
  name: string;
  unit: string;
}

/**
 * The unit a purchase is typed in. Items still stored in g or ml are bought
 * by the kilo or litre ("2 kg onions"), so the sheet takes kg/L and stores
 * ×1000 rather than make a tired person type 2000.
 */
export function entryUnit(unit: string): { label: string; factor: number } {
  if (unit === 'g') return { label: 'kg', factor: 1000 };
  if (unit === 'ml') return { label: 'L', factor: 1000 };
  return { label: unit, factor: 1 };
}

/** A stored quantity as the sheet shows it: 2000 g → "2 kg". */
export function showQuantity(quantity: number | string, unit: string): string {
  const { label, factor } = entryUnit(unit);
  return `${Math.round((Number(quantity) / factor) * 1000) / 1000} ${label}`;
}

/** A number for a cell: at most 3 decimals, no trailing zeros. */
export const trim = (n: number) => String(Math.round(n * 1000) / 1000);

/**
 * A saved line back in the sheet's columns: unit quantity (in the entry unit),
 * rate per unit quantity, and how many. Stored are only the totals and the
 * count; a line saved before counts existed reads as one of its whole quantity.
 */
export function lineColumns(quantity: number | string, total: number | string | null, packCount: number | string | null, unit: string) {
  const count = Number(packCount) > 0 ? Number(packCount) : 1;
  return {
    unitQty: Number(quantity) / count / entryUnit(unit).factor,
    rate: total == null ? null : Number(total) / count,
    count,
  };
}

/** Reads "480", "₹480", "1,280.50". Null for blank or unreadable. */
export function parseRupees(text: string): number | null {
  const cleaned = text.replace(/[₹,\s]/g, '');
  if (!/^\d*\.?\d+$/.test(cleaned)) return null;
  return Number(cleaned);
}

/** Mirrors PRICE_JUMP_THRESHOLD in backend/app/utils/pricing.py: more than 30% off the last price. */
const PRICE_JUMP = 0.3;

/** Worth asking about before saving. A gift (₹0) or an item with no price yet never is. */
export function isPriceJump(previous: number | string | null | undefined, next: number): boolean {
  const before = Number(previous);
  if (previous == null || !(before > 0) || !(next > 0)) return false;
  return Math.abs(next / before - 1) > PRICE_JUMP;
}

export const rupees = (amount: number | string) =>
  `₹${Number(amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;

/**
 * What the picker offers. With no query: the items bought most often. With
 * one: every item whose name contains it, often-bought first, then names
 * that start with it, then the rest alphabetically.
 */
export function pickItems<T extends PickableItem>(items: T[], query: string, frequent: number[], limit = 8): T[] {
  const rank = new Map(frequent.map((id, index) => [id, index]));
  const q = query.trim().toLowerCase();
  if (!q) {
    return items.filter(item => rank.has(item.id)).sort((a, b) => rank.get(a.id)! - rank.get(b.id)!).slice(0, limit);
  }
  const score = (item: T) => {
    const name = item.name.toLowerCase();
    const often = rank.get(item.id) ?? frequent.length;
    // The exact name wins, then word start beats mid-word: "pya" should find PYAJ before a name that merely contains it.
    const starts = name === q ? -1 : name.startsWith(q) ? 0 : name.split(/[\s(]+/).some(word => word.startsWith(q)) ? 1 : 2;
    return [starts, often] as const;
  };
  return items
    .filter(item => item.name.toLowerCase().includes(q))
    .map(item => ({ item, score: score(item) }))
    .sort((a, b) => a.score[0] - b.score[0] || a.score[1] - b.score[1] || a.item.name.localeCompare(b.item.name))
    .slice(0, limit)
    .map(entry => entry.item);
}
