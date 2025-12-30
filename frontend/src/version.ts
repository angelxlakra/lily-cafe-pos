/**
 * Version information for Lily Cafe POS System Frontend
 */

export const VERSION = '0.1.3';

export const VERSION_INFO = {
  version: VERSION,
  major: 0,
  minor: 1,
  patch: 3,
  releaseDate: '2025-12-30',
  releaseName: 'Edit Served Quantity via Status Badge',
};

export function getVersion(): string {
  return VERSION;
}

export function getVersionInfo() {
  return VERSION_INFO;
}
