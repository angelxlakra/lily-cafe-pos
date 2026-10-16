// Pure helpers for the dish costing screen. No React, no API: tested in tests/costing.test.ts.

import type { DishCostingSummary, GapReason, IngredientLine } from '../types/costing';

interface UnitItem {
  unit: string;
  pack_size?: number | string | null;
  pack_unit?: string | null;
}

// Mirrors backend/app/utils/units.py: the units a recipe can convert between.
const FAMILIES: Record<string, string[]> = { mass: ['g', 'kg'], volume: ['ml', 'l'], count: ['pcs'] };
const ALIASES: Record<string, string> = {
  gm: 'g', gms: 'g', gram: 'g', grams: 'g', kgs: 'kg', kilo: 'kg', kilogram: 'kg', kilograms: 'kg',
  mls: 'ml', millilitre: 'ml', milliliter: 'ml', lt: 'l', ltr: 'l', litre: 'l', liter: 'l', litres: 'l',
  pc: 'pcs', piece: 'pcs', pieces: 'pcs', no: 'pcs', nos: 'pcs',
};

function normalize(unit: string | null | undefined): string | null {
  const key = (unit ?? '').trim().toLowerCase();
  const known = ALIASES[key] ?? key;
  return Object.values(FAMILIES).some(units => units.includes(known)) ? known : null;
}

function familyOf(unit: string | null | undefined): string[] | null {
  const known = normalize(unit);
  return known ? Object.values(FAMILIES).find(units => units.includes(known))! : null;
}

/**
 * The units a recipe line can use for an item, the likeliest first: the small
 * unit of the item's own family (250 g of something bought by the kg), then the
 * pack's family (ml of a sauce counted in bottles), then the item's own unit.
 */
export function unitOptions(item: UnitItem): string[] {
  const options: string[] = [];
  const add = (unit: string) => { if (!options.includes(unit)) options.push(unit); };
  familyOf(item.unit)?.forEach(add);
  if (Number(item.pack_size) > 0) familyOf(item.pack_unit)?.forEach(add);
  add(normalize(item.unit) ?? item.unit);
  return options;
}

/** Where a price came from and when, for the line under its rate. */
export function describeSource(line: Pick<IngredientLine, 'price_source' | 'price_as_of'>): string | null {
  if (line.price_source === 'typed') return 'typed price';
  if (line.price_source === 'purchase' && line.price_as_of) {
    const date = new Date(line.price_as_of);
    return `bought ${date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}`;
  }
  return null;
}

const STALE_DAYS = 30;

/** A purchase price more than a month old: worth a fresh look. */
export function isStalePrice(line: Pick<IngredientLine, 'price_source' | 'price_as_of'>, now = new Date()): boolean {
  if (line.price_source !== 'purchase' || !line.price_as_of) return false;
  return now.getTime() - new Date(line.price_as_of).getTime() > STALE_DAYS * 86_400_000;
}

/** What a gap says on its line, and what to do about it. */
export function describeGap(reason: GapReason, line: Pick<IngredientLine, 'unit' | 'stock_unit'>): { title: string; fix: string } {
  switch (reason) {
    case 'retired':
      return { title: 'This item was retired', fix: 'Swap it for an active item.' };
    case 'needs_pack_size':
      return { title: 'Needs a pack size', fix: `How many ${line.unit} are in 1 ${line.stock_unit}?` };
    case 'unknown_unit':
      return { title: `"${line.unit}" can't be converted`, fix: 'Change the unit to g, ml or pcs.' };
    case 'no_price':
      return { title: 'No price yet', fix: 'Log a purchase, or type a price in Inventory → Items.' };
  }
}

export type CostStatus =
  | { kind: 'none'; label: string }
  | { kind: 'gaps'; label: string; margin: number | null }
  | { kind: 'below'; label: string; margin: number | null }
  | { kind: 'ok'; label: string; margin: number | null };

const percent = (value: number) => `${Math.round(value)}%`;

/** A dish's margin as the Menu page's chip reads it. */
export function costStatus(summary: DishCostingSummary | undefined): CostStatus {
  if (!summary) return { kind: 'none', label: 'No recipe' };
  const margin = summary.margin_percent == null ? null : Number(summary.margin_percent);
  const shown = margin == null ? 'No price' : percent(margin);
  if (!summary.is_complete) {
    const gaps = summary.gap_count === 1 ? '1 gap' : `${summary.gap_count} gaps`;
    // With gaps the real cost is higher, so the margin shown is a ceiling. With
    // nothing costed at all, a ceiling of 100% says nothing, so leave it out.
    const known = margin != null && Number(summary.cost_per_unit) > 0;
    return { kind: 'gaps', label: known ? `≤ ${shown} · ${gaps}` : gaps, margin: known ? margin : null };
  }
  if (summary.below_target) {
    return { kind: 'below', label: `${shown} · below ${percent(Number(summary.target_margin_percent))}`, margin };
  }
  return { kind: 'ok', label: shown, margin };
}

/**
 * Order for "needs attention": below target (worst margin first), then dishes
 * with gaps (most gaps first), then dishes with no recipe. Fine dishes last.
 */
export function attentionRank(status: CostStatus, gapCount = 0): [number, number] {
  switch (status.kind) {
    case 'below': return [0, status.margin ?? 0];
    case 'gaps': return [1, -gapCount];
    case 'none': return [2, 0];
    case 'ok': return [3, -(status.margin ?? 0)];
  }
}

export const needsAttention = (status: CostStatus) => status.kind !== 'ok';

/** A rupee amount for the readout: ₹128.70, ₹90, ₹1,280. */
export function rupees(amount: number | string | null | undefined): string {
  if (amount == null) return '—';
  const value = Number(amount);
  // Whole rupees stay whole; anything with paise shows both digits, as money does.
  const digits = Number.isInteger(value) ? 0 : 2;
  return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: digits, maximumFractionDigits: digits })}`;
}

/** A recipe quantity as typed: a positive number, or null for blank or unreadable. */
export function parseQuantity(text: string): number | null {
  const cleaned = text.trim().replace(/,/g, '.');
  if (!/^\d*\.?\d+$/.test(cleaned)) return null;
  const value = Number(cleaned);
  return value > 0 ? value : null;
}
