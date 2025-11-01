// ========================================
// Date/Time Formatting Utility
// Formats ISO timestamps for display
// ========================================

/**
 * Format an ISO timestamp to a readable date/time string
 *
 * @param isoString - ISO 8601 date string
 * @returns Formatted date/time string
 *
 * @example
 * formatDateTime('2024-10-30T14:30:00') // "30 Oct 2024, 02:30 PM"
 */
export function formatDateTime(isoString: string): string {
  const date = new Date(isoString);

  const dateOptions: Intl.DateTimeFormatOptions = {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  };

  const timeOptions: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  };

  const formattedDate = date.toLocaleDateString('en-IN', dateOptions);
  const formattedTime = date.toLocaleTimeString('en-IN', timeOptions);

  return `${formattedDate}, ${formattedTime}`;
}

/**
 * Format an ISO timestamp to just the time
 *
 * @param isoString - ISO 8601 date string
 * @returns Formatted time string
 *
 * @example
 * formatTime('2024-10-30T14:30:00') // "02:30 PM"
 */
export function formatTime(isoString: string): string {
  const date = new Date(isoString);

  return date.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });
}

/**
 * Format an ISO timestamp to just the date
 *
 * @param isoString - ISO 8601 date string
 * @returns Formatted date string
 *
 * @example
 * formatDate('2024-10-30T14:30:00') // "30 Oct 2024"
 */
export function formatDate(isoString: string): string {
  const date = new Date(isoString);

  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}
