import { useState } from 'react';
import { ArrowsLeftRight } from '@phosphor-icons/react';
import { useUpdateOrder } from '../hooks/useOrders';
import { useAppConfig } from '../hooks/useConfig';
import { toast } from 'sonner';
import type { Order } from '../types';

interface MoveTableModalProps {
  order: Order;
  onClose: () => void;
}

export default function MoveTableModal({ order, onClose }: MoveTableModalProps) {
  const { data: config } = useAppConfig();
  const updateOrder = useUpdateOrder();
  const maxTables = config?.max_tables || 50;

  const [selectedTable, setSelectedTable] = useState(order.table_number);

  const isSameTable = selectedTable === order.table_number;

  const handleMove = async () => {
    try {
      await updateOrder.mutateAsync({
        id: order.id,
        data: {
          items: order.order_items.map(i => ({
            menu_item_id: i.menu_item_id,
            quantity: i.quantity,
            is_parcel: i.is_parcel,
          })),
          table_number: selectedTable,
        },
      });
      toast.success(`Order moved to Table ${selectedTable}`);
      onClose();
    } catch (err) {
      toast.error('Failed to move table', {
        description: err instanceof Error ? err.message : 'Please try again.',
      });
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                   w-full max-w-xs bg-off-white rounded-2xl shadow-2xl z-60
                   border border-neutral-border overflow-hidden"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{ background: 'linear-gradient(135deg, #3d7a50, #2e6040)' }}
          className="flex items-center gap-3 px-5 py-4"
        >
          <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
            <ArrowsLeftRight size={20} weight="duotone" color="white" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-white font-heading italic text-base font-bold leading-tight">
              Move Table
            </h2>
            <p className="text-white/70 text-xs mt-0.5">
              Table {order.table_number} · {order.order_number}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-white/60 hover:text-white text-xl leading-none ml-auto flex-shrink-0"
          >
            &times;
          </button>
        </div>

        {/* Body */}
        <div className="p-5">
          <label className="block text-sm font-semibold text-neutral-text-dark mb-2">
            Move to table
          </label>
          <select
            value={selectedTable}
            onChange={(e) => setSelectedTable(Number(e.target.value))}
            className="w-full px-4 py-3 bg-white border border-neutral-border rounded-lg
                       focus:outline-none focus:ring-2 focus:ring-lily-green text-neutral-text-dark"
          >
            {Array.from({ length: maxTables }, (_, i) => i + 1).map(num => (
              <option key={num} value={num}>Table {num}</option>
            ))}
          </select>
          {isSameTable && (
            <p className="text-xs text-neutral-text-muted mt-1.5">
              Already on Table {order.table_number} — select a different table to move.
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-neutral-border p-4 flex gap-2 bg-off-white">
          <button
            onClick={onClose}
            className="btn btn-secondary flex-1"
          >
            Cancel
          </button>
          <button
            onClick={handleMove}
            disabled={isSameTable || updateOrder.isPending}
            className="flex-1 py-2 px-4 rounded-lg font-semibold text-sm text-white
                       bg-lily-green hover:bg-lily-green-light
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {updateOrder.isPending ? 'Moving…' : `Move to Table ${selectedTable}`}
          </button>
        </div>
      </div>
    </>
  );
}
