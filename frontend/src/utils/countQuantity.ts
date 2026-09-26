// Stock quantities as staff wrote them on the WhatsApp checklist: whole
// numbers and halves/quarters (½, ¼, ¾), never "0.50".

const FRACTION_GLYPHS: Record<string, string> = { '0.25': '¼', '0.5': '½', '0.75': '¾' };
const GLYPH_VALUES: Record<string, number> = { '¼': 0.25, '½': 0.5, '¾': 0.75 };

/** 1.5 → "1½", 0.5 → "½", 2 → "2", 0.3 → "0.3". */
export function formatQty(value: number | string): string {
  const n = Number(value);
  if (!Number.isFinite(n)) return '';
  const whole = Math.trunc(n);
  const fraction = FRACTION_GLYPHS[String(Math.round((n - whole) * 100) / 100)];
  if (fraction) return whole === 0 ? fraction : `${whole}${fraction}`;
  return String(Math.round(n * 100) / 100);
}

/**
 * Reads what someone types into a count field: "3", "2.5", "½", "1½",
 * "1/2", "1 1/2". Returns null for empty or unreadable input, and never a
 * negative number (callers show that as an error).
 */
export function parseQty(input: string): number | null {
  const text = input.trim();
  if (text === '') return null;

  let match = text.match(/^(\d+)?\s*([¼½¾])$/);
  if (match) return Number(match[1] ?? 0) + GLYPH_VALUES[match[2]];

  match = text.match(/^(?:(\d+)\s+)?(\d+)\/(\d+)$/);
  if (match) {
    const denominator = Number(match[3]);
    if (denominator === 0) return null;
    return Number(match[1] ?? 0) + Number(match[2]) / denominator;
  }

  if (!/^-?\d*\.?\d+$/.test(text)) return null;
  return Number(text);
}

/** Flag a change only if the count at least doubled or halved... */
export const BIG_DIFFERENCE_RATIO = 2;
/** ...and only the few most extreme, so the list stays short enough to read. */
export const BIG_DIFFERENCE_LIMIT = 5;

/**
 * How far off a count is, independent of unit: |log(counted / previous)|,
 * so 1000→2000 g and 5→10 pcs score the same, and doubling scores the same as
 * halving. Running out (x→0) and restocking (0→x) are normal and score 0.
 */
export function differenceScore(previous: number, counted: number): number {
  if (previous <= 0 || counted <= 0) return 0;
  return Math.abs(Math.log(counted / previous));
}

/**
 * The changes worth a second look before saving: at most
 * BIG_DIFFERENCE_LIMIT, each at least doubled or halved, most extreme first.
 * On a quiet night that is one or two, or none.
 */
export function pickBigDifferences<T extends { previous: number; counted: number }>(changes: T[]): T[] {
  const bar = Math.log(BIG_DIFFERENCE_RATIO) - 1e-9;
  return changes
    .map(change => ({ change, score: differenceScore(change.previous, change.counted) }))
    .filter(({ score }) => score >= bar)
    .sort((a, b) => b.score - a.score)
    .slice(0, BIG_DIFFERENCE_LIMIT)
    .map(({ change }) => change);
}

/**
 * pickBigDifferences over a count in progress: the counted items that changed, most extreme first.
 * Yes/no items never qualify: an answer can't be mistyped, and a run-out (1→0) would otherwise
 * crowd the one real variance off the list.
 */
export function bigDifferenceItems<T extends { id: number; current_quantity: number | string; count_mode?: string }>(
  items: T[],
  counts: Record<number, number>,
): T[] {
  const changes = items
    .filter(item => !isPresence(item))
    .filter(item => item.id in counts && counts[item.id] !== Number(item.current_quantity))
    .map(item => ({ item, previous: Number(item.current_quantity), counted: counts[item.id] }));
  return pickBigDifferences(changes).map(change => change.item);
}

// Yes/no items: stored as 1 (have it) or 0 (out), never shown as a number.

export const isPresence = (item: { count_mode?: string }) => item.count_mode === 'presence';

/** What the system held, in the past tense the count reads in: "had it" / "out". */
export const hadIt = (value: number | string) => (Number(value) > 0 ? 'had it' : 'out');

/** What was answered tonight: "have it" / "out". */
export const haveIt = (value: number | string) => (Number(value) > 0 ? 'have it' : 'out');

/** A change as a person would say it: "had it → out" for yes/no, "3 → 2½" otherwise. */
export function describeChange(item: { count_mode?: string }, previous: number | string, next: number | string): string {
  return isPresence(item) ? `${hadIt(previous)} → ${haveIt(next)}` : `${formatQty(previous)} → ${formatQty(next)}`;
}
