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

/** Worth a second look before saving: 5+ units, or more than half the stock. */
export function isBigDifference(previous: number, counted: number): boolean {
  const diff = Math.abs(counted - previous);
  return diff >= 5 || (previous > 0 && diff / previous > 0.5);
}
