// Run with: npm test
import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  attentionRank, clearCostingDrafts, costStatus, describeGap, describeSource, isStalePrice, parseQuantity, percent, rupees, unitOptions,
} from '../src/utils/costing.ts';

const summary = (over: Record<string, unknown> = {}) => ({
  id: 1, menu_item_id: 1, menu_item_name: 'Wings', cost_per_unit: '128.70', selling_price: '280',
  margin_percent: '54.04', target_margin_percent: '65', below_target: true, is_complete: true, gap_count: 0,
  ...over,
});

test('a recipe line offers the units that will convert, likeliest first', () => {
  assert.deepEqual(unitOptions({ unit: 'kg' }), ['g', 'kg']);
  assert.deepEqual(unitOptions({ unit: 'L' }), ['ml', 'l']);
  assert.deepEqual(unitOptions({ unit: 'bottle', pack_size: '700', pack_unit: 'ml' }), ['ml', 'l', 'bottle']);
  assert.deepEqual(unitOptions({ unit: 'portion', pack_size: 6, pack_unit: 'pcs' }), ['pcs', 'portion']);
  // A pack size means recipes use the pack's unit: butter in 100 g packs defaults to g, not 100 packs.
  assert.deepEqual(unitOptions({ unit: 'pcs', pack_size: 100, pack_unit: 'g' }), ['g', 'kg', 'pcs']);
  // Counted in pieces or packs with no pack size yet: weight and volume are offered too,
  // so 25 g of butter bought by the pack becomes a named gap that asks for the pack size.
  assert.deepEqual(unitOptions({ unit: 'bottle', pack_size: null, pack_unit: 'ml' }), ['bottle', 'g', 'kg', 'ml', 'l']);
  assert.deepEqual(unitOptions({ unit: 'pcs' }), ['pcs', 'g', 'kg', 'ml', 'l']);
  // Bought by weight: never offered ml or pcs.
  assert.deepEqual(unitOptions({ unit: 'kg', pack_size: null }), ['g', 'kg']);
});

test('a margin never reads as reaching a target it misses', () => {
  assert.equal(percent(64.9), '64%');
  assert.equal(percent(65), '65%');
  assert.equal(costStatus(summary({ margin_percent: '64.9', below_target: true })).label, '64% · below 65%');
});

test('a price says where it came from, and a month-old purchase is stale', () => {
  assert.equal(describeSource({ price_source: 'typed', price_as_of: null }), 'typed price');
  assert.match(describeSource({ price_source: 'purchase', price_as_of: '2026-10-12T05:00:00' })!, /^bought 12 Oct$/);
  assert.equal(describeSource({ price_source: null, price_as_of: null }), null);
  const now = new Date('2026-10-16T12:00:00');
  assert.equal(isStalePrice({ price_source: 'purchase', price_as_of: '2026-09-10T05:00:00' }, now), true);
  assert.equal(isStalePrice({ price_source: 'purchase', price_as_of: '2026-10-12T05:00:00' }, now), false);
  assert.equal(isStalePrice({ price_source: 'typed', price_as_of: null }, now), false);
});

test('every gap names the fix', () => {
  assert.equal(describeGap('needs_pack_size', { unit: 'ml', stock_unit: 'bottle' }).fix, 'How many ml are in 1 bottle?');
  assert.match(describeGap('unknown_unit', { unit: 'tbsp', stock_unit: 'kg' }).title, /tbsp/);
  assert.match(describeGap('no_price', { unit: 'g', stock_unit: 'kg' }).fix, /purchase/);
});

test('the menu chip reads honestly', () => {
  assert.deepEqual(costStatus(undefined), { kind: 'none', label: 'No recipe' });
  assert.equal(costStatus(summary({ below_target: false, margin_percent: '68.2' })).label, '68%');
  assert.equal(costStatus(summary()).label, '54% · below 65%');
  // Gaps mean the real cost is higher, so the margin is at most this.
  assert.equal(costStatus(summary({ is_complete: false, gap_count: 2 })).label, '≤ 54% · 2 gaps');
  assert.equal(costStatus(summary({ is_complete: false, gap_count: 1, margin_percent: null })).label, '1 gap');
  // Nothing costed yet: "≤ 100%" would be noise.
  assert.equal(costStatus(summary({ is_complete: false, gap_count: 2, cost_per_unit: '0.00', margin_percent: '100' })).label, '2 gaps');
});

test('needs attention puts the worst margin first and fine dishes last', () => {
  const rows = [
    { name: 'fine', status: costStatus(summary({ below_target: false, margin_percent: '70' })) },
    { name: 'none', status: costStatus(undefined) },
    { name: 'gaps', status: costStatus(summary({ is_complete: false, gap_count: 2 })) },
    { name: 'below 50', status: costStatus(summary({ margin_percent: '50' })) },
    { name: 'below 30', status: costStatus(summary({ margin_percent: '30' })) },
  ];
  const sorted = [...rows].sort((a, b) => {
    const [ra, sa] = attentionRank(a.status, 2), [rb, sb] = attentionRank(b.status, 2);
    return ra - rb || sa - sb;
  });
  assert.deepEqual(sorted.map(r => r.name), ['below 30', 'below 50', 'gaps', 'none', 'fine']);
});

test('quantities and rupees read the way people type and expect them', () => {
  assert.equal(parseQuantity('250'), 250);
  assert.equal(parseQuantity('0,5'), 0.5);
  assert.equal(parseQuantity('0'), null);
  assert.equal(parseQuantity('abc'), null);
  assert.equal(rupees('128.70'), '₹128.70');
  assert.equal(rupees('90.00'), '₹90');
  assert.equal(rupees(1280), '₹1,280');
  assert.equal(rupees(null), '—');
});

test('signing out forgets unsaved recipes and nothing else', () => {
  const data = new Map<string, string>([['lily.costing-draft.4', '{}'], ['lily.costing-draft.9', '{}'], ['lily-cafe-theme', 'dark']]);
  const storage = {
    get length() { return data.size; },
    key: (i: number) => [...data.keys()][i] ?? null,
    removeItem: (key: string) => { data.delete(key); },
  } as unknown as Storage;
  clearCostingDrafts(storage);
  assert.deepEqual([...data.keys()], ['lily-cafe-theme']);
});
