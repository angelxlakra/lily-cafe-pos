// Run with: npm test (Node's built-in runner; types are stripped, no build step).
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { clearCountDraft, loadCountDraft, saveCountDraft } from '../src/utils/countDraft.ts';

const store = new Map<string, string>();
Object.assign(globalThis, {
  localStorage: {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => void store.set(key, value),
    removeItem: (key: string) => void store.delete(key),
  },
});

test('an entry saved loads back unchanged', () => {
  const startedAt = Date.now() - 60_000;
  assert.equal(saveCountDraft({ 7: 2.5, 9: 0 }, startedAt), true);
  const draft = loadCountDraft();
  assert.deepEqual(draft?.counts, { 7: 2.5, 9: 0 });
  assert.equal(draft?.startedAt, startedAt);
});

test('clearing, or saving nothing, leaves no draft', () => {
  saveCountDraft({ 1: 1 }, Date.now());
  clearCountDraft();
  assert.equal(loadCountDraft(), null);
  saveCountDraft({ 1: 1 }, Date.now());
  saveCountDraft({}, Date.now());
  assert.equal(loadCountDraft(), null);
});
