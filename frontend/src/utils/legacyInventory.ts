// Where an old /admin/inventory?tab=X link goes now.
const TAB_PATHS: Record<string, string> = {
  order: '/admin/ops/order',
  purchases: '/admin/ops/sheet',
  items: '/admin/ops/setup',
  categories: '/admin/ops/setup',
  transactions: '/admin/ops/log',
};

export function legacyInventoryPath(tab: string | null): string {
  return (tab && Object.prototype.hasOwnProperty.call(TAB_PATHS, tab) && TAB_PATHS[tab]) || '/admin/ops/inventory';
}
