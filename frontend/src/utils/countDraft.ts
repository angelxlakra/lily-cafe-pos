// Unsaved nightly-count entries live on this device so a tab switch, reload
// or closed browser never loses a half-finished count.

const DRAFT_KEY = 'lily.inventoryCountDraft';
// ponytail: expiry by age of the last entry, not by business date, so a count
// that runs past midnight survives; stale drafts from a previous night expire.
const DRAFT_MAX_AGE_MS = 12 * 60 * 60 * 1000;

/** Counted quantity per item id. A ✓ stores the system quantity. */
export type CountEntries = Record<number, number>;
export type CountDraft = { startedAt: number; savedAt: number; counts: CountEntries };

export function loadCountDraft(): CountDraft | null {
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    if (!raw) return null;
    const draft = JSON.parse(raw) as Partial<CountDraft>;
    if (!draft?.counts || !draft.savedAt || Date.now() - draft.savedAt > DRAFT_MAX_AGE_MS) {
      localStorage.removeItem(DRAFT_KEY);
      return null;
    }
    return { startedAt: draft.startedAt ?? draft.savedAt, savedAt: draft.savedAt, counts: draft.counts };
  } catch {
    return null;
  }
}

/** Returns false when the browser won't let us store the draft. */
export function saveCountDraft(counts: CountEntries, startedAt: number): boolean {
  try {
    if (Object.keys(counts).length === 0) localStorage.removeItem(DRAFT_KEY);
    else localStorage.setItem(DRAFT_KEY, JSON.stringify({ startedAt, savedAt: Date.now(), counts }));
    return true;
  } catch {
    return false;
  }
}

export function clearCountDraft(): void {
  try {
    localStorage.removeItem(DRAFT_KEY);
  } catch {
    // Nothing stored, or storage unavailable: nothing to clear.
  }
}
