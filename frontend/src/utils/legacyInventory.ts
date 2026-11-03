// Where an old /admin/inventory?tab=X link goes now.
const TAB_PATHS: Record<string, string> = {
  order: '/admin/ops/order',
  purchases: '/admin/ops/sheet',
  items: '/admin/ops/setup',
  categories: '/admin/ops/setup',
  transactions: '/admin/ops/log',
};

// Setup is owner-only, so a manager's old Items or Categories link lands on Inventory instead.
export function legacyInventoryPath(tab: string | null, isOwner = true): string {
  const path = tab && Object.prototype.hasOwnProperty.call(TAB_PATHS, tab) && TAB_PATHS[tab];
  return path && (isOwner || path !== '/admin/ops/setup') ? path : '/admin/ops/inventory';
}
