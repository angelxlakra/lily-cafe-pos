// ========================================
// Tables Page Component
// Landing page showing table grid
// ========================================

import { useActiveOrders } from '../hooks/useOrders';
import TableGrid from '../components/TableGrid';
import BottomNav from '../components/BottomNav';

const MAX_TABLES = 15; // From config

export default function TablesPage() {
  const { data: activeOrders, isLoading, error } = useActiveOrders();

  const orders = activeOrders || [];

  return (
    <div className="min-h-screen bg-neutral-background pb-16">
      {/* Header */}
      <header className="bg-coffee-brown text-cream p-4 sticky top-0 z-30 shadow-md">
        <h1 className="font-heading heading-sub text-center">Lily Cafe – Tables</h1>
      </header>

      {/* Error State */}
      {error && (
        <div className="px-4 mt-4">
          <div className="max-w-3xl mx-auto bg-error/10 border border-error rounded-lg p-4">
            <p className="text-error font-medium">
              {error instanceof Error ? error.message : 'Failed to load active orders'}
            </p>
          </div>
        </div>
      )}

      {/* Table Grid */}
      <main className="px-4 py-6">
        <div className="max-w-5xl mx-auto">
          <TableGrid
            maxTables={MAX_TABLES}
            activeOrders={orders}
            isLoading={isLoading}
          />
        </div>
      </main>

      {/* Bottom Navigation */}
      <BottomNav />
    </div>
  );
}
