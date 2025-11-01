// ========================================
// Currency Formatting Utility
// Formats numbers as Indian Rupees (�)
// ========================================

/**
 * Format a number as Indian Rupees currency
 *
 * @param amount - Amount in rupees (not paise)
 * @returns Formatted string with � symbol
 *
 * @example
 * formatCurrency(100) // "�100"
 * formatCurrency(80.50) // "�80.50"
 * formatCurrency(1234.56) // "�1,234.56"
 */
export function formatCurrency(amount: number): string {
  return `₹${(amount / 100).toLocaleString("en-IN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}
