// Self-check for the count quantity helpers. Run: node src/utils/countQuantity.check.ts
import { formatQty, isBigDifference, parseQty } from './countQuantity.ts';

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

assert.equal(isBigDifference(8, 2), true);   // more than half gone
assert.equal(isBigDifference(46, 41), true); // 5 units
assert.equal(isBigDifference(46, 44), false);
assert.equal(isBigDifference(0, 1), false);

console.log('countQuantity: ok');
