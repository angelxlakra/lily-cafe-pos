// Run with: npm test (Node's built-in runner; types are stripped, no build step).
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { bigDifferenceItems, describeChange, hadIt, haveIt } from '../src/utils/countQuantity.ts';

const item = (id: number, current_quantity: number, count_mode: 'number' | 'presence' = 'number') =>
  ({ id, current_quantity, count_mode });

test('yes/no items are never big differences, even when every one ran out', () => {
  const sauces = [1, 2, 3, 4, 5, 6].map(id => item(id, 1, 'presence'));
  const onions = item(10, 4);
  const counts: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 10: 1 };
  assert.deepEqual(bigDifferenceItems([...sauces, onions], counts).map(i => i.id), [10]);
});

test('a yes/no flip back to have it is not a big difference either', () => {
  assert.deepEqual(bigDifferenceItems([item(1, 0, 'presence')], { 1: 1 }), []);
});

test('yes/no items are excluded outright, not just scored low', () => {
  // A draft typed as ½ before the owner switched the item to yes/no: a number
  // item going 1 → 0.4 is a big difference, a yes/no item must not be.
  assert.deepEqual(bigDifferenceItems([item(1, 1)], { 1: 0.4 }).map(i => i.id), [1]);
  assert.deepEqual(bigDifferenceItems([item(1, 1, 'presence')], { 1: 0.4 }), []);
});

test('number items still qualify', () => {
  assert.deepEqual(bigDifferenceItems([item(1, 10), item(2, 10)], { 1: 4, 2: 9 }).map(i => i.id), [1]);
});

test('a yes/no change reads as words, never 1 → 0', () => {
  assert.equal(describeChange({ count_mode: 'presence' }, 1, 0), 'had it → out');
  assert.equal(describeChange({ count_mode: 'presence' }, 0, 1), 'out → have it');
  assert.equal(describeChange({ count_mode: 'number' }, 3, 2.5), '3 → 2½');
  assert.equal(hadIt('1.00'), 'had it');
  assert.equal(haveIt('0.00'), 'out');
});
