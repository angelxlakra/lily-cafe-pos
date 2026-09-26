// Self-check for the count quantity helpers. Run: node src/utils/countQuantity.check.ts
import { bigDifferenceItems, differenceScore, formatQty, parseQty, pickBigDifferences } from './countQuantity.ts';

const assert = {
  equal(actual: unknown, expected: unknown) {
    if (actual !== expected) throw new Error(`Expected ${String(expected)}, got ${String(actual)}`);
  },
};

assert.equal(formatQty(0.5), '½');
assert.equal(formatQty('1.50'), '1½');
assert.equal(formatQty(2.75), '2¾');
assert.equal(formatQty('46.00'), '46');
assert.equal(formatQty(0.3), '0.3');
assert.equal(formatQty(0), '0');

assert.equal(parseQty(''), null);
assert.equal(parseQty('3'), 3);
assert.equal(parseQty('2.5'), 2.5);
assert.equal(parseQty('½'), 0.5);
assert.equal(parseQty('1½'), 1.5);
assert.equal(parseQty('1 ½'), 1.5);
assert.equal(parseQty('1/2'), 0.5);
assert.equal(parseQty('1 3/4'), 1.75);
assert.equal(parseQty('1/0'), null);
assert.equal(parseQty('abc'), null);
assert.equal(parseQty('-2'), -2); // caller rejects negatives with a message

// Unit-blind: the same relative change scores the same, grams or pieces,
// and doubling scores the same as halving.
assert.equal(differenceScore(1000, 2000), differenceScore(5, 10));
assert.equal(differenceScore(2000, 1000), differenceScore(1000, 2000));
// Running out and restocking are normal.
assert.equal(differenceScore(100, 0), 0);
assert.equal(differenceScore(0, 40), 0);

// Last night's real count.
const lastNight = [
  { name: 'CHEST BONELESS', previous: 1000, counted: 2000 },
  { name: 'LEG BONELESS', previous: 2300, counted: 2000 },
  { name: 'AALU', previous: 500, counted: 1500 },
  { name: 'PYAJ', previous: 2000, counted: 3000 },
  { name: 'ADRAK', previous: 100, counted: 0 },
  { name: 'GREEN CHILLI', previous: 100, counted: 150 },
  { name: 'THAI RED CHILLI', previous: 60, counted: 150 },
  { name: 'LEMON', previous: 5, counted: 12 },
  { name: 'EGGS', previous: 0, counted: 40 },
  { name: 'SOONTH', previous: 2, counted: 0 },
  { name: 'TINGMO', previous: 10, counted: 19 },
  { name: 'KARAGE', previous: 3, counted: 5 },
  { name: 'SWEET CHILLI MAYO', previous: 0, counted: 1 },
  { name: 'MIE GORENG', previous: 50, counted: 20 },
  { name: 'TOMATO', previous: 350, counted: 0 },
  { name: 'FRIES', previous: 1800, counted: 1500 },
  { name: 'KHEERA', previous: 1000, counted: 1500 },
];
const names = (changes: { name: string }[]) => changes.map(change => change.name).join(', ');
assert.equal(
  names(pickBigDifferences(lastNight)),
  'AALU, THAI RED CHILLI, MIE GORENG, LEMON, CHEST BONELESS',
);

// A quiet night shows only what clears the bar, not a forced five.
const quiet = lastNight.filter(change => !['AALU', 'THAI RED CHILLI', 'MIE GORENG', 'LEMON'].includes(change.name));
assert.equal(names(pickBigDifferences(quiet)), 'CHEST BONELESS');
assert.equal(names(pickBigDifferences(lastNight.filter(change => change.name === 'TINGMO'))), '');

// A night with many big changes still shows only five.
const wild = Array.from({ length: 12 }, (_, i) => ({ name: `X${i}`, previous: 10, counted: 30 + i }));
assert.equal(pickBigDifferences(wild).length, 5);
assert.equal(pickBigDifferences(wild)[0].name, 'X11');

// Over a count in progress: only counted, changed items take part.
const items = [
  { id: 1, current_quantity: 500 },  // AALU, counted 1500
  { id: 2, current_quantity: 100 },  // counted 0: ran out
  { id: 3, current_quantity: 8 },    // not counted
  { id: 4, current_quantity: 12 },   // matches
];
const flagged = bigDifferenceItems(items, { 1: 1500, 2: 0, 4: 12 });
assert.equal(flagged.map(item => item.id).join(), '1');

console.log('countQuantity: ok');
