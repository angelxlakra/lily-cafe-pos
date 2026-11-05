// Run with: npm test
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { greeting, groupOrders, parseOrderQuantity, renderMessage, suggestQuantity, unitFor } from '../src/utils/orderMessage.ts';

const item = (over: Record<string, unknown>) => ({
  id: 1, name: 'Chicken boneless', unit: 'kg', current_quantity: '1', min_threshold: '3',
  count_mode: 'number' as const, is_active: true, is_low_stock: true, default_vendor_id: null, ...over,
});

test('a suggestion gets back to twice the alert level, in amounts a vendor sells', () => {
  // Alert at 3 kg, 1 kg left: 5 kg brings it to 6.
  assert.equal(suggestQuantity(item({})), 5);
  assert.equal(suggestQuantity(item({ current_quantity: '1.5' })), 5); // 4.5 rounds up
  // Grams are bought by the hundred.
  assert.equal(suggestQuantity(item({ unit: 'g', current_quantity: '120', min_threshold: '250' })), 400);
  // A yes/no item is asked for by name alone.
  assert.equal(suggestQuantity(item({ count_mode: 'presence', unit: 'yes/no' })), null);
});

test('low items group by vendor, by name, with Unassigned last', () => {
  const vendors = [{ id: 7, name: 'Raju Chicken Centre' }, { id: 3, name: 'Lakshmi Dairy' }];
  const groups = groupOrders([
    item({ id: 1, name: 'Chicken boneless', default_vendor_id: 7 }),
    item({ id: 2, name: 'Paneer', default_vendor_id: 3 }),
    item({ id: 3, name: 'Garbage bags' }),
    item({ id: 4, name: 'Milk', default_vendor_id: 3 }),
    item({ id: 5, name: 'Plenty of salt', is_low_stock: false, default_vendor_id: 3 }),
    item({ id: 6, name: 'Retired', is_active: false }),
    item({ id: 7, name: 'Vendor since deleted', default_vendor_id: 99 }),
  ], vendors);

  assert.deepEqual(groups.map(g => g.vendor?.name ?? 'Unassigned'), ['Lakshmi Dairy', 'Raju Chicken Centre', 'Unassigned']);
  assert.deepEqual(groups[0].items.map(i => i.name), ['Paneer', 'Milk']);
  assert.deepEqual(groups[2].items.map(i => i.name), ['Garbage bags', 'Vendor since deleted']);
});

test('nothing low, nothing to order', () => {
  assert.deepEqual(groupOrders([item({ is_low_stock: false })], []), []);
});

test('the message reads like the owner wrote it', () => {
  assert.equal(
    renderMessage([
      { name: 'Chicken boneless', unit: 'kg', quantity: 5 },
      { name: 'Paneer', unit: 'kg', quantity: 1.5 },
      { name: 'Coriander', unit: 'yes/no', quantity: null },
    ], 22),
    'Good evening. Please send tomorrow:\n• Chicken boneless — 5 kg\n• Paneer — 1.5 kg\n• Coriander',
  );
  assert.equal(greeting(9), 'Good morning');
  assert.equal(greeting(14), 'Good afternoon');
  assert.equal(greeting(1), 'Good evening'); // a count that runs past midnight
});

test('units read the way a vendor says them', () => {
  assert.equal(unitFor('bottle', 3), 'bottles');
  assert.equal(unitFor('bottle', 1), 'bottle');
  assert.equal(unitFor('portion', 6), 'portions');
  assert.equal(unitFor('box', 2), 'boxes');
  assert.equal(unitFor('kg', 5), 'kg');
  assert.equal(unitFor('L', 2), 'L');
  assert.equal(unitFor('pcs', 40), 'pcs');
  assert.equal(
    renderMessage([{ name: 'Hot sauce', unit: 'bottle', quantity: 3 }], 22),
    'Good evening. Please send tomorrow:\n• Hot sauce — 3 bottles',
  );
});

test('quantities read the way people type them', () => {
  assert.equal(parseOrderQuantity('5'), 5);
  assert.equal(parseOrderQuantity('1,5'), 1.5);
  assert.equal(parseOrderQuantity(''), null);
  assert.equal(parseOrderQuantity('0'), null);
});
