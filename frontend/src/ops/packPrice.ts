// "₹99 / 10 g": a price and the pack it buys, as the owners write it. Pure, tested in tests/packPrice.test.ts.

export interface PackPrice {
  price: number;
  quantity: number;
  unit: string;
}

const FORM = /^\s*(?:₹|rs\.?)?\s*([\d,]+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)?\s*([a-zA-Z]+)\s*$/i;

/** "₹99 / 10 g", "99/10g", "75 / kg" (one kg). Anything else is null. */
export function parsePackPrice(text: string): PackPrice | null {
  const match = FORM.exec(text);
  if (!match) return null;
  const price = Number(match[1].replace(/,/g, ''));
  const quantity = match[2] === undefined ? 1 : Number(match[2]);
  if (!(price > 0) || !(quantity > 0)) return null;
  return { price, quantity, unit: match[3].toLowerCase() };
}

const number = (value: number) => value.toLocaleString('en-IN', { maximumFractionDigits: 4 });

/** The same form back: "₹99 / 10 g", or "₹40 / kg" for one. */
export function formatPackPrice(price: number, packQuantity: number, packUnit: string): string {
  const pack = packQuantity === 1 ? packUnit : `${number(packQuantity)} ${packUnit}`;
  return `₹${number(price)} / ${pack}`;
}
