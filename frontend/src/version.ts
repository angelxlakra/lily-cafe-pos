/**
 * Version information for Lily Cafe POS System Frontend
 */

export const VERSION = '0.2.0';

export const VERSION_INFO = {
  version: VERSION,
  major: 0,
  minor: 2,
  patch: 0,
  releaseDate: '2025-12-30',
  releaseName: 'Inventory Management & Cash Counter',
};

export function getVersion(): string {
  return VERSION;
}

export function getVersionInfo() {
  return VERSION_INFO;
}
