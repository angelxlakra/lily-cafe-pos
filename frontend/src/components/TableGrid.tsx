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
              w-full h-[120px] rounded-lg
              flex flex-col items-center justify-center
              transition-all duration-200
              border-2
              ${
                isActive
                  ? 'bg-lily-green/20 border-lily-green shadow-md hover:shadow-lg'
                  : 'bg-cream border-neutral-border hover:border-coffee-light'
              }
              hover:scale-105 active:scale-100
              cursor-pointer
            `}
            aria-label={`Table ${tableNumber}${isActive ? ' - Active' : ' - Empty'}`}
          >
            <span className="text-2xl font-semibold font-heading text-neutral-text-dark mb-1">
              Table {tableNumber}
            </span>
            <span
              className={`text-sm font-medium ${
                isActive ? 'text-lily-green' : 'text-neutral-text-light'
              }`}
            >
              {isActive ? 'Active' : 'Empty'}
            </span>
            {isActive && order && (
              <span className="text-xs text-neutral-text-light mt-1">
                {order.order_items?.length || 0} {(order.order_items?.length || 0) === 1 ? 'item' : 'items'}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
