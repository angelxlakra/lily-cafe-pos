import { test } from 'node:test';
import assert from 'node:assert/strict';

process.env.TZ = 'Asia/Kolkata';
const { localDate } = await import('../src/utils/formatDateTime.ts');

test("a date is the cafe's, not UTC's, after midnight IST", () => {
  const at0235Ist = new Date('2026-10-18T21:05:00Z');
  assert.equal(at0235Ist.toISOString().slice(0, 10), '2026-10-18'); // the old, wrong answer
  assert.equal(localDate(at0235Ist), '2026-10-19');
});
