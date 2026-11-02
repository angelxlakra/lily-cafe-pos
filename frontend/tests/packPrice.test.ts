// Run with: npm test
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { formatPackPrice, parsePackPrice, usesPackForm } from '../src/ops/packPrice.ts';

test('parsePackPrice reads the forms the owners type', () => {
  assert.deepEqual(parsePackPrice('₹99 / 10 g'), { price: 99, quantity: 10, unit: 'g' });
  assert.deepEqual(parsePackPrice('99/10g'), { price: 99, quantity: 10, unit: 'g' });
  assert.deepEqual(parsePackPrice('60 / 250 g'), { price: 60, quantity: 250, unit: 'g' });
  assert.deepEqual(parsePackPrice('439/500ml'), { price: 439, quantity: 500, unit: 'ml' });
  assert.deepEqual(parsePackPrice('75 / kg'), { price: 75, quantity: 1, unit: 'kg' });
  assert.deepEqual(parsePackPrice('₹35/500 g'), { price: 35, quantity: 500, unit: 'g' });
  assert.deepEqual(parsePackPrice('₹1,541 / kg'), { price: 1541, quantity: 1, unit: 'kg' });
});

test('parsePackPrice refuses anything else', () => {
  assert.equal(parsePackPrice('abc'), null);
  assert.equal(parsePackPrice('99'), null);
  assert.equal(parsePackPrice(''), null);
  assert.equal(parsePackPrice('99 / 0 g'), null);
  assert.equal(parsePackPrice('0 / kg'), null);
});

test('formatPackPrice writes it the way it is typed', () => {
  assert.equal(formatPackPrice(99, 10, 'g'), '₹99 / 10 g');
  assert.equal(formatPackPrice(40, 1, 'kg'), '₹40 / kg');
  assert.equal(formatPackPrice(1541.25, 1, 'kg'), '₹1,541.25 / kg');
  assert.deepEqual(parsePackPrice(formatPackPrice(220, 400, 'g')), { price: 220, quantity: 400, unit: 'g' });
});

test('usesPackForm is for packets priced by weight, not a kg item priced per 500 g', () => {
  assert.equal(usesPackForm({ unit: 'pcs', pack_size: 52, pack_unit: 'g' }), true);
  assert.equal(usesPackForm({ unit: 'pkt', pack_size: '100', pack_unit: 'g' }), true);
  assert.equal(usesPackForm({ unit: 'kg', pack_size: 0.5, pack_unit: 'kg' }), false);
  assert.equal(usesPackForm({ unit: 'g', pack_size: 500, pack_unit: 'kg' }), false);
  assert.equal(usesPackForm({ unit: 'g', pack_size: null, pack_unit: null }), false);
});
