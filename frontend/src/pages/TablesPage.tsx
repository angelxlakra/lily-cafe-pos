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
        <h1 className="text-xl font-semibold text-center">Lily Cafe - Tables</h1>
      </header>

      {/* Error State */}
      {error && (
        <div className="mx-4 mt-4 bg-error/10 border border-error rounded-lg p-4">
          <p className="text-error font-medium">
            {error instanceof Error ? error.message : 'Failed to load active orders'}
          </p>
        </div>
      )}

      {/* Table Grid */}
      <main>
        <TableGrid
          maxTables={MAX_TABLES}
          activeOrders={orders}
          isLoading={isLoading}
        />
      </main>

      {/* Bottom Navigation */}
      <BottomNav />
    </div>
  );
}
