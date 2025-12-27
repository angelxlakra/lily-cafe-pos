/**
 * Version information for Lily Cafe POS System Frontend
 */

export const VERSION = '0.1.2';

export const VERSION_INFO = {
  version: VERSION,
  major: 0,
  minor: 1,
  patch: 2,
  releaseDate: '2025-12-27',
  releaseName: 'Partial Serving & Payment Editing',
};

export function getVersion(): string {
  return VERSION;
}

export function getVersionInfo() {
  return VERSION_INFO;
}
