// Pure helpers for the end-of-count order messages. Tested in tests/orderMessage.test.ts.
//
// Low stock exists to drive ordering: the low items, grouped by each one's
// default vendor, become one paste-ready message per vendor. Items with no
// vendor collect under "Unassigned" at the bottom: still visible, still
// orderable. Quantities are suggestions to edit, never a calculation to trust.

export interface OrderItem {
  id: number;
  name: string;
  unit: string;
  current_quantity: number | string;
  min_threshold: number | string;
  count_mode: 'number' | 'presence';
  is_active: boolean;
  is_low_stock: boolean;
  default_vendor_id?: number | null;
}

export interface OrderVendor {
  id: number;
  name: string;
  phone?: string | null;
}

export interface OrderGroup<T extends OrderItem = OrderItem> {
  /** null = Unassigned. */
  vendor: OrderVendor | null;
  items: T[];
}

/** Units bought by the hundred rather than one at a time. */
const SMALL_UNITS = new Set(['g', 'ml']);

/**
 * Enough to get back to twice the alert level, rounded up to something a
 * vendor would sell: whole units, or hundreds of g/ml. A yes/no item has no
 * quantity, just a name.
 */
export function suggestQuantity(item: Pick<OrderItem, 'unit' | 'current_quantity' | 'min_threshold' | 'count_mode'>): number | null {
  if (item.count_mode === 'presence') return null;
  const threshold = Number(item.min_threshold);
  const short = 2 * threshold - Number(item.current_quantity);
  const step = SMALL_UNITS.has(item.unit.trim().toLowerCase()) ? 100 : 1;
  const rounded = Math.ceil(short / step) * step;
  return rounded > 0 ? rounded : step;
}

/** Low, active items grouped by default vendor: vendors by name, Unassigned last. */
export function groupOrders<T extends OrderItem>(items: T[], vendors: OrderVendor[]): OrderGroup<T>[] {
  const known = new Map(vendors.map(vendor => [vendor.id, vendor]));
  const groups = new Map<number | null, T[]>();
  for (const item of items) {
    if (!item.is_active || !item.is_low_stock) continue;
    const key = item.default_vendor_id != null && known.has(item.default_vendor_id) ? item.default_vendor_id : null;
    groups.set(key, [...(groups.get(key) ?? []), item]);
  }
  const named = [...groups.entries()]
    .filter(([key]) => key !== null)
    .map(([key, groupItems]) => ({ vendor: known.get(key as number)!, items: groupItems }))
    .sort((a, b) => a.vendor.name.localeCompare(b.vendor.name));
  const unassigned = groups.get(null);
  return unassigned ? [...named, { vendor: null, items: unassigned }] : named;
}

/** "Good evening" at the end of the night's count, whatever time it is. */
export function greeting(hour: number): string {
  if (hour >= 4 && hour < 12) return 'Good morning';
  if (hour >= 12 && hour < 17) return 'Good afternoon';
  return 'Good evening';
}

// Abbreviations read the same for any amount: 1 kg, 5 kg, 40 pcs.
const ABBREVIATIONS = new Set(['g', 'kg', 'ml', 'l', 'pcs', 'pc', 'nos', 'no', 'pkt', 'pkts']);

/** The unit as a vendor reads it: 3 bottles, 1 bottle, 6 portions, 2 boxes, 5 kg. */
export function unitFor(unit: string, quantity: number): string {
  const word = unit.trim();
  if (quantity === 1 || ABBREVIATIONS.has(word.toLowerCase()) || /s$/i.test(word)) return word;
  return /(x|ch|sh)$/i.test(word) ? `${word}es` : `${word}s`;
}

/** A quantity as a person writes it: 5, 1.5, 500. */
const showNumber = (value: number) => String(Math.round(value * 1000) / 1000);

export interface OrderLine {
  name: string;
  unit: string;
  /** null = no quantity (a yes/no item, or the owner cleared it): the name alone. */
  quantity: number | null;
}

/** The message as it is pasted into WhatsApp or Telegram. */
export function renderMessage(lines: OrderLine[], hour: number): string {
  const body = lines.map(line =>
    line.quantity == null ? `• ${line.name}` : `• ${line.name} — ${showNumber(line.quantity)} ${unitFor(line.unit, line.quantity)}`,
  );
  return [`${greeting(hour)}. Please send tomorrow:`, ...body].join('\n');
}

/** A quantity as typed into the order: a positive number, or null when blank. */
export function parseOrderQuantity(text: string): number | null {
  const cleaned = text.trim().replace(/,/g, '.');
  if (!/^\d*\.?\d+$/.test(cleaned)) return null;
  const value = Number(cleaned);
  return value > 0 ? value : null;
}
