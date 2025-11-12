/**
 * Version information for Lily Cafe POS System Frontend
 */

export const VERSION = '0.1.0';

export const VERSION_INFO = {
  version: VERSION,
  major: 0,
  minor: 1,
  patch: 0,
  releaseDate: '2025-11-11',
  releaseName: 'Initial MVP',
};

export function getVersion(): string {
  return VERSION;
}

export function getVersionInfo() {
  return VERSION_INFO;
}
