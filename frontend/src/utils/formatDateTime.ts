// ========================================
// Date/Time Formatting Utility
// Formats ISO timestamps for display
// ========================================

/**
 * Helper to ensure the timestamp is treated as UTC if it lacks timezone info
 */
function ensureUtc(isoString: string): string {
  // If string doesn't end in Z and doesn't have an offset (e.g. +05:30), append Z
  if (isoString && !isoString.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(isoString)) {
    return isoString + 'Z';
  }
  return isoString;
}

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
  const date = new Date(ensureUtc(isoString));

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
  const date = new Date(ensureUtc(isoString));

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
  const date = new Date(ensureUtc(isoString));

  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

