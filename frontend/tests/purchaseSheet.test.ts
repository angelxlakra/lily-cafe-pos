// Run with: npm test
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { entryUnit, isPriceJump, lineColumns, parseRupees, pickItems, showQuantity } from '../src/utils/purchaseSheet.ts';

const items = [
  { id: 1, name: 'PYAJ SAAG', unit: 'g' },
  { id: 2, name: 'PYAJ', unit: 'g' },
  { id: 3, name: 'CHEST BONELESS', unit: 'pcs' },
  { id: 4, name: 'SAFED PYAJ PASTE', unit: 'pcs' },
];

test('grams are bought by the kilo and shown back that way', () => {
  assert.deepEqual(entryUnit('g'), { label: 'kg', factor: 1000 });
  assert.deepEqual(entryUnit('pcs'), { label: 'pcs', factor: 1 });
  assert.equal(showQuantity('2500.00', 'g'), '2.5 kg');
  assert.equal(showQuantity(3, 'pcs'), '3 pcs');
});

test('rupees read the way people type them', () => {
  assert.equal(parseRupees('₹1,280.50'), 1280.5);
  assert.equal(parseRupees('0'), 0);
  assert.equal(parseRupees(''), null);
  assert.equal(parseRupees('12a'), null);
});

test('no query shows what is bought often, in that order', () => {
  assert.deepEqual(pickItems(items, '', [3, 2]).map(i => i.id), [3, 2]);
});

test('a query puts often-bought and word-start matches first', () => {
  assert.deepEqual(pickItems(items, 'pya', [1]).map(i => i.id), [1, 2, 4]);
  assert.deepEqual(pickItems(items, 'pya', []).map(i => i.id), [2, 1, 4]);
  assert.deepEqual(pickItems(items, 'pyaj', [1]).map(i => i.id)[0], 2); // typed it all: that one
});

test('a price more than 30% off the last one is a jump; no history or a gift never is', () => {
  assert.equal(isPriceJump('320', 520), true);
  assert.equal(isPriceJump(320, 200), true);
  assert.equal(isPriceJump(320, 400), false);
  assert.equal(isPriceJump(null, 520), false);
  assert.equal(isPriceJump(320, 0), false);
});

test('a saved line reads back as unit quantity × count at a rate', () => {
  // Onion stored in g: 4 × 1 kg at ₹40 was saved as 4000 g for ₹160.
  assert.deepEqual(lineColumns('4000', '160', '4', 'g'), { unitQty: 1, rate: 40, count: 4 });
  // Older line with no count: one of everything.
  assert.deepEqual(lineColumns(3, 90, null, 'pcs'), { unitQty: 3, rate: 90, count: 1 });
});
