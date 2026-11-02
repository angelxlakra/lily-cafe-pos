// Run with: npm test
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { legacyInventoryPath } from '../src/utils/legacyInventory.ts';

test('old inventory tabs land on their ops page', () => {
  assert.equal(legacyInventoryPath('daily-count'), '/admin/ops/inventory');
  assert.equal(legacyInventoryPath('order'), '/admin/ops/order');
  assert.equal(legacyInventoryPath('purchases'), '/admin/ops/sheet');
  assert.equal(legacyInventoryPath('items'), '/admin/ops/setup');
  assert.equal(legacyInventoryPath('categories'), '/admin/ops/setup');
  assert.equal(legacyInventoryPath('transactions'), '/admin/ops/log');
});

test('no tab, an unknown tab or a prototype key goes to the inventory page', () => {
  assert.equal(legacyInventoryPath(null), '/admin/ops/inventory');
  assert.equal(legacyInventoryPath('nonsense'), '/admin/ops/inventory');
  assert.equal(legacyInventoryPath('constructor'), '/admin/ops/inventory');
});
