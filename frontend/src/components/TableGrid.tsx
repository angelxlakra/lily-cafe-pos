// ========================================
// Table Grid Component
// Displays all tables with empty/active states
// ========================================

import { useNavigate } from 'react-router-dom';
import type { Order } from '../types';

interface TableGridProps {
  maxTables: number;
  activeOrders: Order[];
  isLoading?: boolean;
}

export default function TableGrid({
  maxTables,
  activeOrders,
  isLoading = false,
}: TableGridProps) {
  const navigate = useNavigate();

  // Create a map of table numbers to active orders for quick lookup
  const activeTableMap = new Map<number, Order>();
  activeOrders.forEach((order) => {
    activeTableMap.set(order.table_number, order);
  });

  // Generate array of table numbers
  const tables = Array.from({ length: maxTables }, (_, i) => i + 1);

  const handleTableClick = (tableNumber: number) => {
    navigate(`/order/${tableNumber}`);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-coffee-brown border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-neutral-text-light">Loading tables...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 p-4 pb-24 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
      {tables.map((tableNumber) => {
        const isActive = activeTableMap.has(tableNumber);
        const order = activeTableMap.get(tableNumber);

        return (
          <button
            key={tableNumber}
            onClick={() => handleTableClick(tableNumber)}
            className={`
              w-full h-[130px] rounded-xl
              flex flex-col items-center justify-center
              smooth-transition
              relative overflow-hidden
              ${
                isActive
                  ? 'bg-gradient-to-br from-lily-green/25 to-lily-green/15 border-2 border-lily-green shadow-medium hover:shadow-strong'
                  : 'card-interactive border-2 border-transparent'
              }
            `}
            aria-label={`Table ${tableNumber}${isActive ? ' - Active' : ' - Empty'}`}
          >
            {/* Decorative background element for active tables */}
            {isActive && (
              <div className="absolute top-0 right-0 w-16 h-16 bg-lily-green/10 rounded-full blur-2xl"></div>
            )}

            <span className="text-3xl font-bold font-heading text-neutral-text-dark mb-2 relative z-10">
              {tableNumber}
            </span>

            <div className={`
              badge px-3 py-1
              ${isActive
                ? 'bg-lily-green text-white'
                : 'bg-neutral-border text-neutral-text-dark'
              }
            `}>
              {isActive ? 'Active' : 'Empty'}
            </div>

            {isActive && order && (
              <span className="text-xs text-neutral-text-light mt-2 font-medium relative z-10">
                {order.order_items?.length || 0} {(order.order_items?.length || 0) === 1 ? 'item' : 'items'}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
