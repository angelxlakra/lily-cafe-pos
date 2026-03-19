// frontend/src/pages/AdminActiveOrdersPage.tsx
import { useState, useEffect, useMemo } from 'react';
import { toast } from 'sonner';
import { ClipboardText, CurrencyInr as _CurrencyInr, PencilSimple as _PencilSimple, ArrowsLeftRight as _ArrowsLeftRight } from '@phosphor-icons/react';
import {
  useActiveOrders,
  useCancelOrder,
  useUpdateItemServedStatus,
  useSetItemServedQuantity
} from '../hooks/useOrders';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcut';
import PageHeader from '../components/PageHeader';
import AdminStatsBar from '../components/AdminStatsBar';
import EmptyState from '../components/EmptyState';
import EditOrderModal from '../components/EditOrderModal';
import PaymentModal from '../components/PaymentModal';
import ConfirmDialog from '../components/ConfirmDialog';
import PartialServeModal from '../components/PartialServeModal';
import EditServedQuantityModal from '../components/EditServedQuantityModal';
import MoveTableModal from '../components/MoveTableModal';
import KeyboardShortcutsHelp from '../components/KeyboardShortcutsHelp';
import { formatCurrency } from '../utils/formatCurrency';
import type { Order, OrderItem } from '../types';

// ── helpers ──────────────────────────────────────────────────────────────────

function getOrderAgeMinutes(createdAt: string): number {
  return Math.floor((Date.now() - new Date(createdAt).getTime()) / 60_000);
}

function ageClass(minutes: number) {
  if (minutes >= 60) return 'border-error bg-[rgba(244,67,54,0.04)]';
  if (minutes >= 30) return 'border-amber bg-[rgba(194,122,42,0.04)]';
  return 'border-lily-green';
}

function AgeBadge({ minutes }: { minutes: number }) {
  if (minutes >= 60)
    return (
      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-error/10 text-error">
        ⚠ {minutes}m
      </span>
    );
  if (minutes >= 30)
    return (
      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-amber/10 text-amber">
        ⚑ {minutes}m
      </span>
    );
  return (
    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-lily-green/10 text-lily-green">
      {minutes}m
    </span>
  );
}

// ── skeleton ──────────────────────────────────────────────────────────────────

function Skeleton() {
  return (
    <div className="flex flex-1 overflow-hidden">
      {/* List skeleton */}
      <div className="w-60 flex-shrink-0 border-r border-neutral-border flex flex-col gap-0">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="p-3 border-b border-neutral-border animate-pulse">
            <div className="h-3 w-24 bg-neutral-border/50 rounded mb-2" />
            <div className="h-2.5 w-16 bg-neutral-border/50 rounded" />
          </div>
        ))}
      </div>
      {/* Detail skeleton — hidden on mobile */}
      <div className="hidden lg:flex flex-1 flex-col gap-3 p-6 animate-pulse">
        <div className="h-5 w-32 bg-neutral-border/50 rounded" />
        <div className="h-3 w-48 bg-neutral-border/50 rounded" />
        <div className="h-40 w-full bg-neutral-border/50 rounded mt-4" />
      </div>
    </div>
  );
}

// ── order list row ────────────────────────────────────────────────────────────

interface OrderRowProps {
  order: Order;
  isSelected: boolean;
  onClick: () => void;
}

function OrderRow({ order, isSelected, onClick }: OrderRowProps) {
  const age = getOrderAgeMinutes(order.created_at);
  const items = order.order_items || [];
  const servedCount = items.filter(i => i.is_served).length;
  const pendingCount = items.length - servedCount;

  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left px-3 py-3 border-b border-neutral-border/60
        border-l-[3px] transition-colors
        ${isSelected
          ? 'bg-white border-l-coffee-brown'
          : `bg-off-white hover:bg-cream/40 ${ageClass(age)}`
        }
      `}
    >
      <div className="flex items-start justify-between gap-1">
        <div className="min-w-0">
          <p className="text-sm font-bold text-coffee-dark truncate">
            Table {order.table_number}
            {order.customer_name && (
              <span className="font-normal text-neutral-text-light"> — {order.customer_name}</span>
            )}
          </p>
          <p className="text-xs text-neutral-text-light mt-0.5">
            {items.length} item{items.length !== 1 ? 's' : ''}
          </p>
        </div>
        <AgeBadge minutes={age} />
      </div>
      <div className="flex gap-1.5 mt-1.5 flex-wrap">
        {servedCount > 0 && (
          <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-lily-green/10 text-lily-green">
            {servedCount} served
          </span>
        )}
        {pendingCount > 0 && (
          <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-amber/10 text-amber">
            {pendingCount} pending
          </span>
        )}
      </div>
    </button>
  );
}

// ── item row ──────────────────────────────────────────────────────────────────

interface ItemRowProps {
  item: OrderItem;
  onOpenServeModal: (item: OrderItem) => void;
  onOpenEditModal: (item: OrderItem) => void;
}

function ItemRow({ item, onOpenServeModal, onOpenEditModal }: ItemRowProps) {
  return (
    <tr className="border-b border-[#F5E6D3] last:border-0">
      <td className="py-2 px-3 text-sm text-coffee-dark">{item.menu_item_name}</td>
      <td className="py-2 px-3 text-sm text-center text-neutral-text-light">{item.quantity}</td>
      <td className="py-2 px-3 text-center">
        {item.is_served ? (
          <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-lily-green/10 text-lily-green">
            ✓ Served
          </span>
        ) : (
          <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-amber/10 text-amber">
            Pending
          </span>
        )}
      </td>
      <td className="py-2 px-3 text-right">
        {!item.is_served && (
          <button
            onClick={() => onOpenServeModal(item)}
            className="text-xs font-semibold text-lily-green hover:text-lily-green/80 transition-colors"
          >
            Serve
          </button>
        )}
        {item.is_served && (
          <button
            onClick={() => onOpenEditModal(item)}
            className="text-xs text-neutral-text-light hover:text-coffee-brown transition-colors"
          >
            Edit
          </button>
        )}
      </td>
    </tr>
  );
}

// ── detail panel ──────────────────────────────────────────────────────────────

interface DetailPanelProps {
  order: Order;
  onGenerateBill: () => void;
  onEdit: () => void;
  onCancel: () => void;
  onOpenServeModal: (item: OrderItem) => void;
  onOpenEditModal: (item: OrderItem) => void;
}

function DetailPanel({
  order,
  onGenerateBill,
  onEdit,
  onCancel,
  onOpenServeModal,
  onOpenEditModal,
}: DetailPanelProps) {
  const age = getOrderAgeMinutes(order.created_at);
  const items = order.order_items || [];
  const dineInItems = items.filter(i => !i.is_parcel);
  const parcelItems = items.filter(i => i.is_parcel);

  return (
    <div className="flex flex-col h-full w-full">
      {/* Detail header */}
      <div className="px-5 py-4 border-b border-neutral-border bg-off-white/80">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="font-heading italic text-xl text-coffee-dark">
              Table {order.table_number}
            </h2>
            <p className="text-xs text-neutral-text-light mt-0.5 flex items-center gap-1.5">
              {order.order_number}
              {order.customer_name && ` · ${order.customer_name}`}
              {' · '}
              <AgeBadge minutes={age} />
            </p>
          </div>
          <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
            parcelItems.length > 0
              ? 'bg-amber/10 text-amber border border-amber/20'
              : 'bg-lily-green/10 text-lily-green border border-lily-green/20'
          }`}>
            {parcelItems.length > 0 ? 'Dine-in + Parcel' : 'Dine-in'}
          </span>
        </div>
      </div>

      {/* Items */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        {/* Dine-in section */}
        {dineInItems.length > 0 && (
          <div>
            {parcelItems.length > 0 && (
              <p className="text-xs font-bold uppercase tracking-widest text-neutral-text-light mb-2">
                Dine-in
              </p>
            )}
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-border">
                  <th className="pb-1 px-3 text-left text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Item</th>
                  <th className="pb-1 px-3 text-center text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Qty</th>
                  <th className="pb-1 px-3 text-center text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Status</th>
                  <th className="pb-1 px-3 text-right text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Action</th>
                </tr>
              </thead>
              <tbody>
                {dineInItems.map(item => <ItemRow key={item.id} item={item} onOpenServeModal={onOpenServeModal} onOpenEditModal={onOpenEditModal} />)}
              </tbody>
            </table>
          </div>
        )}

        {/* Parcel section */}
        {parcelItems.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-1 h-4 bg-amber rounded-full" />
              <p className="text-xs font-bold uppercase tracking-widest text-amber">
                Parcel
              </p>
            </div>
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-border">
                  <th className="pb-1 px-3 text-left text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Item</th>
                  <th className="pb-1 px-3 text-center text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Qty</th>
                  <th className="pb-1 px-3 text-center text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Status</th>
                  <th className="pb-1 px-3" />
                </tr>
              </thead>
              <tbody>
                {parcelItems.map(item => <ItemRow key={item.id} item={item} onOpenServeModal={onOpenServeModal} onOpenEditModal={onOpenEditModal} />)}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-neutral-border bg-off-white/80">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-neutral-text-light">Total</span>
          <span className="font-heading italic text-xl text-coffee-dark">
            {formatCurrency(order.total_amount)}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onGenerateBill}
            className="flex-1 bg-coffee-brown text-cream text-sm font-semibold py-2 rounded-lg hover:bg-coffee-dark transition-colors"
          >
            Generate Bill
          </button>
          <button
            onClick={onEdit}
            className="px-4 bg-cream border border-neutral-border text-coffee-dark text-sm font-semibold py-2 rounded-lg hover:bg-neutral-border/30 transition-colors"
          >
            Edit
          </button>
        </div>
        <div className="mt-2 text-center">
          <button
            onClick={onCancel}
            className="text-xs text-neutral-text-light underline hover:text-error transition-colors"
          >
            cancel order
          </button>
        </div>
      </div>
    </div>
  );
}

// ── empty detail state ────────────────────────────────────────────────────────

function EmptyDetailPanel() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center bg-off-white/60 gap-3">
      <div className="w-12 h-12 rounded-full bg-coffee-brown/10 flex items-center justify-center">
        <ClipboardText size={24} weight="duotone" className="text-coffee-brown" />
      </div>
      <p className="text-sm font-semibold text-coffee-dark">Select an order</p>
      <p className="text-xs text-neutral-text-light text-center max-w-[180px]">
        Click any table on the left to view its details here
      </p>
    </div>
  );
}

// ── page ──────────────────────────────────────────────────────────────────────

export default function AdminActiveOrdersPage() {
  const { data: activeOrders, isLoading, error } = useActiveOrders();
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);
  const [paymentOrderId, setPaymentOrderId] = useState<number | null>(null);
  const [editOrder, setEditOrder] = useState<Order | null>(null);
  const [cancelOrderId, setCancelOrderId] = useState<number | null>(null);
  const [serveModalData, setServeModalData] = useState<{ item: OrderItem; orderId: number } | null>(null);
  const [editModalData, setEditModalData] = useState<{ item: OrderItem; orderId: number } | null>(null);
  const [moveOrderId, setMoveOrderId] = useState<number | null>(null);

  const cancelMutation = useCancelOrder();
  const updateServedMutation = useUpdateItemServedStatus();
  const setServedQuantityMutation = useSetItemServedQuantity();

  const orders = activeOrders || [];
  const selectedOrder = orders.find(o => o.id === selectedOrderId) ?? null;

  // Auto-select first order when none selected or selected order disappears
  useEffect(() => {
    if (orders.length === 0) {
      setSelectedOrderId(null);
      return;
    }
    const stillExists = orders.some(o => o.id === selectedOrderId);
    if (!stillExists) {
      setSelectedOrderId(orders[0].id);
    }
  }, [orders, selectedOrderId]);

  // Stats
  const stats = useMemo(() => {
    const liveTotal = orders.reduce((sum, o) => sum + o.total_amount, 0);
    const pendingServe = orders.filter(o =>
      (o.order_items || []).some(i => !i.is_served)
    ).length;
    const readyToBill = orders.filter(o =>
      (o.order_items || []).length > 0 &&
      (o.order_items || []).every(i => i.is_served)
    ).length;
    return [
      { label: 'Active', value: String(orders.length) },
      { label: 'Live Total', value: formatCurrency(liveTotal) },
      { label: 'Pending Serve', value: String(pendingServe) },
      { label: 'Ready to Bill', value: String(readyToBill) },
    ];
  }, [orders]);

  // Modal guards
  const isAnyModalOpen =
    paymentOrderId !== null ||
    editOrder !== null ||
    cancelOrderId !== null ||
    serveModalData !== null ||
    editModalData !== null ||
    moveOrderId !== null;

  // Keyboard shortcuts
  const shortcuts = useMemo(() => ({
    ArrowUp: {
      handler: () => {
        if (orders.length === 0) return;
        const idx = orders.findIndex(o => o.id === selectedOrderId);
        const prev = orders[Math.max(0, idx - 1)];
        setSelectedOrderId(prev.id);
      },
      enabled: !isAnyModalOpen,
    },
    ArrowDown: {
      handler: () => {
        if (orders.length === 0) return;
        const idx = orders.findIndex(o => o.id === selectedOrderId);
        const next = orders[Math.min(orders.length - 1, idx + 1)];
        setSelectedOrderId(next.id);
      },
      enabled: !isAnyModalOpen,
    },
    b: {
      handler: () => {
        if (selectedOrderId !== null) setPaymentOrderId(selectedOrderId);
      },
      enabled: !isAnyModalOpen && selectedOrderId !== null,
    },
    e: {
      handler: () => {
        if (selectedOrder) setEditOrder(selectedOrder);
      },
      enabled: !isAnyModalOpen && selectedOrderId !== null,
    },
  }), [selectedOrderId, orders, isAnyModalOpen, selectedOrder]);

  useKeyboardShortcuts(shortcuts);

  // Handlers
  const handleServeItem = (orderId: number, itemId: number, quantityToServe: number) => {
    updateServedMutation.mutate(
      { orderId, itemId, quantityToServe },
      {
        onError: (error) => {
          toast.error('Failed to update served quantity', {
            description: error instanceof Error ? error.message : 'Please try again.',
          });
        },
        onSuccess: () => toast.success('Served quantity updated successfully'),
      }
    );
  };

  const handleEditServedQuantity = (orderId: number, itemId: number, quantityServed: number) => {
    setServedQuantityMutation.mutate(
      { orderId, itemId, quantityServed },
      {
        onError: (error) => {
          toast.error('Failed to update served quantity', {
            description: error instanceof Error ? error.message : 'Please try again.',
          });
        },
        onSuccess: () => toast.success('Served quantity updated successfully'),
      }
    );
  };

  const handleCancelOrder = () => {
    if (!cancelOrderId) return;
    cancelMutation.mutate(cancelOrderId, {
      onSuccess: () => {
        toast.success('Order cancelled successfully');
        setCancelOrderId(null);
        setSelectedOrderId(null); // triggers auto-select via useEffect
      },
      onError: (error) => {
        toast.error('Failed to cancel order', {
          description: error instanceof Error ? error.message : 'Please try again.',
        });
      },
    });
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <PageHeader
        title="Active Orders"
        subtitle="Manage ongoing orders, generate bills, and process payments"
      />

      <AdminStatsBar stats={stats} />

      {/* Loading */}
      {isLoading && <Skeleton />}

      {/* Error */}
      {!isLoading && error && (
        <div className="p-6">
          <div className="bg-error/10 border border-error rounded-lg p-4">
            <p className="text-error font-medium">
              {error instanceof Error ? error.message : 'Failed to load active orders'}
            </p>
          </div>
        </div>
      )}

      {/* Empty */}
      {!isLoading && !error && orders.length === 0 && (
        <div className="flex-1 flex items-center justify-center">
          <EmptyState
            icon={<ClipboardText size={32} weight="duotone" />}
            title="No active orders"
            description="Once tables send orders, you'll see them listed here ready for billing."
          />
        </div>
      )}

      {/* Master–detail */}
      {!isLoading && orders.length > 0 && (
        <div className="flex flex-1 overflow-hidden">
          {/* Order list — left panel */}
          <div className="w-full lg:w-60 flex-shrink-0 border-r border-neutral-border overflow-y-auto">
            {orders.map(order => (
              <OrderRow
                key={order.id}
                order={order}
                isSelected={order.id === selectedOrderId}
                onClick={() => setSelectedOrderId(order.id)}
              />
            ))}
          </div>

          {/* Detail panel — right panel, hidden on mobile */}
          <div className="hidden lg:flex flex-1 overflow-hidden">
            {selectedOrder ? (
              <DetailPanel
                order={selectedOrder}
                onGenerateBill={() => setPaymentOrderId(selectedOrder.id)}
                onEdit={() => setEditOrder(selectedOrder)}
                onCancel={() => setCancelOrderId(selectedOrder.id)}
                onOpenServeModal={(item) => setServeModalData({ item, orderId: selectedOrder.id })}
                onOpenEditModal={(item) => setEditModalData({ item, orderId: selectedOrder.id })}
              />
            ) : (
              <EmptyDetailPanel />
            )}
          </div>
        </div>
      )}

      {/* Modals */}
      {editOrder && (
        <EditOrderModal order={editOrder} onClose={() => setEditOrder(null)} />
      )}
      {paymentOrderId && (
        <PaymentModal orderId={paymentOrderId} onClose={() => setPaymentOrderId(null)} />
      )}
      {cancelOrderId && (
        <ConfirmDialog
          isOpen
          onClose={() => setCancelOrderId(null)}
          onConfirm={handleCancelOrder}
          title="Cancel Order?"
          message={`Are you sure you want to cancel Table ${orders.find(o => o.id === cancelOrderId)?.table_number}'s order? This action cannot be undone.`}
          confirmText="Yes, Cancel Order"
          cancelText="No, Keep It"
          variant="danger"
          isLoading={cancelMutation.isPending}
        />
      )}
      {serveModalData && (
        <PartialServeModal
          item={serveModalData.item}
          orderId={serveModalData.orderId}
          onClose={() => setServeModalData(null)}
          onServe={handleServeItem}
        />
      )}
      {editModalData && (
        <EditServedQuantityModal
          item={editModalData.item}
          orderId={editModalData.orderId}
          onClose={() => setEditModalData(null)}
          onEdit={handleEditServedQuantity}
        />
      )}
      {moveOrderId && (
        <MoveTableModal
          order={orders.find(o => o.id === moveOrderId)!}
          onClose={() => setMoveOrderId(null)}
        />
      )}

      <KeyboardShortcutsHelp />
    </div>
  );
}
