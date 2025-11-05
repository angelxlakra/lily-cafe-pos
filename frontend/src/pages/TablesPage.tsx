// ========================================
// Tables Page Component
// Landing page showing table grid
// ========================================

import { useActiveOrders } from '../hooks/useOrders';
import TableGrid from '../components/TableGrid';
import BottomNav from '../components/BottomNav';
import BackgroundPattern from '../components/BackgroundPattern';

const MAX_TABLES = 15; // From config

export default function TablesPage() {
  const { data: activeOrders, isLoading, error } = useActiveOrders();

  const orders = activeOrders || [];

  return (
    <div className="min-h-screen bg-neutral-background pb-16 relative">
      {/* Background Pattern */}
      <BackgroundPattern opacity={0.04} density="light" />

      {/* Header */}
      <header className="bg-gradient-primary text-cream p-6 sticky top-0 z-30 shadow-medium">
        <h1 className="font-heading heading-sub text-center">Lily Cafe – Tables</h1>
        <p className="text-center text-cream/80 text-sm mt-1">Select a table to take an order</p>
      </header>

      {/* Error State */}
      {error && (
        <div className="px-4 mt-6 fade-in">
          <div className="max-w-3xl mx-auto bg-error/10 border-2 border-error rounded-xl p-5 shadow-soft">
            <div className="flex items-start gap-3">
              <svg className="w-6 h-6 text-error flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-error font-semibold">
                {error instanceof Error ? error.message : 'Failed to load active orders'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Table Grid */}
      <main className="px-2 py-6 relative z-10">
        <div className="max-w-6xl mx-auto">
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
