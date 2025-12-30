/**
 * Unit Parser Utility
 *
 * Parses mixed unit formats from WhatsApp inventory templates into
 * standardized values for the database.
 *
 * Handles:
 * - Fractions: ½, ¼, ¾ → 0.5, 0.25, 0.75
 * - YES/NO → 1/0 (unit: pcs)
 * - Weights: 50g → 0.05 (unit: kg), 4kg → 4 (unit: kg)
 * - Complex strings: "XL-1 L-1 M-1" → store as notes
 */

export interface ParsedQuantity {
  value: number;
  unit: string;
  notes?: string;
}

// Fraction mappings
const FRACTION_MAP: Record<string, number> = {
  '½': 0.5,
  '¼': 0.25,
  '¾': 0.75,
  '⅓': 0.33,
  '⅔': 0.67,
  '⅛': 0.125,
  '⅜': 0.375,
  '⅝': 0.625,
  '⅞': 0.875,
};

/**
 * Parse a quantity string from WhatsApp format
 */
export function parseQuantity(input: string | number, defaultUnit: string = 'pcs'): ParsedQuantity {
  // Handle numeric input
  if (typeof input === 'number') {
    return { value: input, unit: defaultUnit };
  }

  // Convert to string and trim
  const str = String(input).trim().toUpperCase();

  // Handle empty or invalid input
  if (!str || str === 'NULL' || str === 'UNDEFINED' || str === 'N/A') {
    return { value: 0, unit: defaultUnit };
  }

  // Handle YES/NO
  if (str === 'YES' || str === 'Y') {
    return { value: 1, unit: 'pcs' };
  }
  if (str === 'NO' || str === 'N') {
    return { value: 0, unit: 'pcs' };
  }

  // Handle fractions
  for (const [fraction, value] of Object.entries(FRACTION_MAP)) {
    if (str.includes(fraction)) {
      return {
        value,
        unit: defaultUnit,
        notes: `Original: ${input}`
      };
    }
  }

  // Try to parse weight formats (50g, 4kg, 500ml, 2L)
  const weightMatch = str.match(/^(\d+(?:\.\d+)?)\s*(G|KG|ML|L)$/);
  if (weightMatch) {
    const [, number, unit] = weightMatch;
    const value = parseFloat(number);

    // Convert grams to kg
    if (unit === 'G') {
      return { value: value / 1000, unit: 'kg' };
    }

    // Convert ml to L
    if (unit === 'ML') {
      return { value: value / 1000, unit: 'L' };
    }

    // kg and L stay as-is
    return { value, unit: unit.toLowerCase() };
  }

  // Try to parse simple numbers
  const numberMatch = str.match(/^(\d+(?:\.\d+)?)$/);
  if (numberMatch) {
    return { value: parseFloat(numberMatch[1]), unit: defaultUnit };
  }

  // Handle complex strings (e.g., "XL-1 L-1 M-1", "2+1")
  // These go to notes and value=0
  return {
    value: 0,
    unit: defaultUnit,
    notes: `Complex format: ${input}`
  };
}

/**
 * Parse a WhatsApp template line
 */
export interface ParsedItem {
  name: string;
  category: string;
  unit: string;
  quantity: number;
  minThreshold: number;
  notes?: string;
}

export function parseWhatsAppLine(
  line: string,
  currentCategory: string
): ParsedItem | null {
  // Skip empty lines, headers, or category markers
  if (!line.trim() || line.startsWith('_#') || line.startsWith('#') || line.startsWith('*')) {
    return null;
  }

  // Try to split by colon or tab first
  let parts = line.split(/[::\t]+/).map(p => p.trim());

  // If no colon/tab, try splitting by last space (for "ITEM NAME QUANTITY" format)
  if (parts.length < 2) {
    const lastSpaceIndex = line.trim().lastIndexOf(' ');
    if (lastSpaceIndex > 0) {
      parts = [
        line.substring(0, lastSpaceIndex).trim(),
        line.substring(lastSpaceIndex + 1).trim()
      ];
    }
  }

  if (parts.length < 2) {
    return null;
  }

  const [name, quantityStr] = parts;

  // Skip if name is empty
  if (!name) {
    return null;
  }

  // Parse quantity
  const parsed = parseQuantity(quantityStr);

  // Set minThreshold to 10% of initial quantity (or 1 minimum)
  const minThreshold = Math.max(1, Math.round(parsed.value * 0.1));

  return {
    name: name.trim(),
    category: currentCategory,
    unit: parsed.unit,
    quantity: parsed.value,
    minThreshold,
    notes: parsed.notes
  };
}

/**
 * Extract category name from a line like "_#DRY GROCERY#_" or "*DRY GROCERY*"
 */
export function extractCategory(line: string): string | null {
  // Try format: _#CATEGORY#_ or #CATEGORY# or _#CATEGORY# or #CATEGORY#_
  let match = line.match(/_?#(.+?)#_?/);
  if (match) {
    return match[1].trim();
  }

  // Try format: *CATEGORY* (asterisk format)
  match = line.match(/^\*(.+?)\*?\s*$/);
  if (match) {
    return match[1].trim();
  }

  return null;
}

/**
 * Parse entire WhatsApp template
 */
export function parseWhatsAppTemplate(template: string): ParsedItem[] {
  const lines = template.split('\n');
  const items: ParsedItem[] = [];
  let currentCategory = 'Uncategorized';

  for (const line of lines) {
    // Check if this is a category header
    const category = extractCategory(line);
    if (category) {
      currentCategory = category;
      continue;
    }

    // Try to parse as item
    const item = parseWhatsAppLine(line, currentCategory);
    if (item) {
      items.push(item);
    }
  }

  return items;
}

/**
 * Example usage:
 *
 * const template = `
 * _#DRY GROCERY#_
 *
 * RAMEN NOODLES	: 46
 * GLASS NOODLES	: 3
 * BLACK PEPPER POWDER : ½
 * MAYONNAISE       : 0
 * EGGS : 20
 *
 * _#VEGETABLES#_
 * ADRAK		: 50g
 * PYAJ : 4kg
 * COFFEE BEANS : YES
 * GARBAGE BAGS : XL-1 L-1 M-1
 * `;
 *
 * const items = parseWhatsAppTemplate(template);
 * // Returns array of ParsedItem objects
 */
