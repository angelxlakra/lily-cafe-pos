// ========================================
// Currency Formatting Utility
// Formats numbers as Indian Rupees (₹)
// ========================================

/**
 * Format a number as Indian Rupees currency
 *
 * @param amount - Amount in paise
 * @returns Formatted string with ₹ symbol
 *
 * @example
 * formatCurrency(10000) // "₹100"
 * formatCurrency(8050) // "₹80.5"
 * formatCurrency(123456) // "₹1,234.56"
*/
export function formatCurrency(amount: number): string {
  return `₹${(amount).toLocaleString("en-IN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}
