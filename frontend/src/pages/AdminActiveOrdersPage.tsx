// ========================================
// Admin Active Orders Page
// Desktop interface with edit/bill/cancel actions
// ========================================

import { useState } from 'react';
import { toast } from 'sonner';
import { ClipboardText } from '@phosphor-icons/react';
import { useSidebar } from '../context/SidebarContext';
import { 
  useActiveOrders, 
  useCancelOrder, 
  useUpdateItemServedStatus, 
  useSetItemServedQuantity 
} from '../hooks/useOrders';
import EmptyState from '../components/EmptyState';
import EditOrderModal from '../components/EditOrderModal';
import PaymentModal from '../components/PaymentModal';
import ConfirmDialog from '../components/ConfirmDialog';
import PartialServeModal from '../components/PartialServeModal';
import EditServedQuantityModal from '../components/EditServedQuantityModal';
import { formatCurrency } from '../utils/formatCurrency';
import { formatDateTime } from '../utils/formatDateTime';
import type { Order, OrderItem } from '../types';

export default function AdminActiveOrdersPage() {
  const { data: activeOrders, isLoading, error } = useActiveOrders();
  const [paymentOrderId, setPaymentOrderId] = useState<number | null>(null);
  const [editOrder, setEditOrder] = useState<Order | null>(null);
  const [cancelOrderId, setCancelOrderId] = useState<number | null>(null);
  const [serveModalData, setServeModalData] = useState<{ item: OrderItem; orderId: number } | null>(null);
  const [editModalData, setEditModalData] = useState<{ item: OrderItem; orderId: number } | null>(null);
  const { setMobileOpen } = useSidebar();

  const cancelMutation = useCancelOrder();
  const updateServedMutation = useUpdateItemServedStatus();
  const setServedQuantityMutation = useSetItemServedQuantity();

  const orders = activeOrders || [];

  const handleServeItem = (orderId: number, itemId: number, quantityToServe: number) => {
    updateServedMutation.mutate(
      { orderId, itemId, quantityToServe },
      {
        onError: (error) => {
          console.error('Error updating served quantity:', error);
          toast.error("Failed to update served quantity", {
            description: error instanceof Error ? error.message : "Please try again."
          });
        },
        onSuccess: () => {
          toast.success("Served quantity updated successfully");
        },
      }
    );
  };

  const handleEditServedQuantity = (orderId: number, itemId: number, quantityServed: number) => {
    setServedQuantityMutation.mutate(
      { orderId, itemId, quantityServed },
      {
        onError: (error) => {
          console.error('Error setting served quantity:', error);
          toast.error("Failed to update served quantity", {
            description: error instanceof Error ? error.message : "Please try again."
          });
        },
        onSuccess: () => {
          toast.success("Served quantity updated successfully");
        },
      }
    );
  };

  const handleGenerateBill = (orderId: number) => {
    setPaymentOrderId(orderId);
  };

  const handleCancelOrder = async () => {
    if (!cancelOrderId) return;

    try {
      await cancelMutation.mutateAsync(cancelOrderId);
      toast.success("Order cancelled successfully");
      setCancelOrderId(null);
    } catch (error) {
      console.error('Failed to cancel order:', error);
      toast.error("Failed to cancel order", {
        description: error instanceof Error ? error.message : "Please try again."
      });
    }
  };

  return (
    <div className="flex flex-col h-full">
        {/* Header */}
        <header className="bg-off-white border-b border-neutral-border p-4 md:p-6">
          <div className="flex items-center gap-4">
            {/* Hamburger Menu Button */}
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden w-10 h-10 flex items-center justify-center rounded-lg bg-coffee-brown text-cream hover:bg-coffee-dark transition-colors"
              aria-label="Open menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex-1">
              <h1 className="font-heading heading-section text-neutral-text-dark">Active Orders</h1>
              <p className="text-sm text-muted mt-1">
                Manage ongoing orders, generate bills, and process payments
              </p>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-6 overflow-y-auto">
          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <div className="animate-spin h-12 w-12 border-4 border-coffee-brown border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-neutral-text-light">Loading orders...</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-error/10 border border-error rounded-lg p-4">
              <p className="text-error font-medium">
                {error instanceof Error ? error.message : 'Failed to load active orders'}
              </p>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && orders.length === 0 && (
            <EmptyState
              icon={<ClipboardText size={32} weight="duotone" />}
              title="No active orders"
              description="Once tables send orders, you'll see them listed here ready for billing."
            />
          )}

          {/* Orders Grid */}
          {!isLoading && orders.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              {orders.map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  onEdit={() => setEditOrder(order)}
                  onGenerateBill={() => handleGenerateBill(order.id)}
                  onCancel={() => setCancelOrderId(order.id)}
                  onOpenServeModal={(item) => setServeModalData({ item, orderId: order.id })}
                  onOpenEditModal={(item) => setEditModalData({ item, orderId: order.id })}
                />
              ))}
            </div>
          )}
        </main>


      {/* Edit Order Modal */}
      {editOrder && (
        <EditOrderModal
          order={editOrder}
          onClose={() => setEditOrder(null)}
        />
      )}

      {/* Payment Modal */}
      {paymentOrderId && (
        <PaymentModal
          orderId={paymentOrderId}
          onClose={() => setPaymentOrderId(null)}
        />
      )}

      {/* Cancel Confirmation Dialog */}
      {cancelOrderId && (
        <ConfirmDialog
          isOpen={true}
          onClose={() => setCancelOrderId(null)}
          onConfirm={handleCancelOrder}
          title="Cancel Order?"
          message={`Are you sure you want to cancel ${orders.find(o => o.id === cancelOrderId) ? `Table ${orders.find(o => o.id === cancelOrderId)!.table_number}'s order (${formatCurrency(orders.find(o => o.id === cancelOrderId)!.total_amount)})` : 'this order'}? This action cannot be undone.`}
          confirmText="Yes, Cancel Order"
          cancelText="No, Keep It"
          variant="danger"
          isLoading={cancelMutation.isPending}
        />
      )}

      {/* Partial Serve Modal */}
      {serveModalData && (
        <PartialServeModal
          item={serveModalData.item}
          orderId={serveModalData.orderId}
          onServe={handleServeItem}
          onClose={() => setServeModalData(null)}
        />
      )}

      {/* Edit Served Quantity Modal */}
      {editModalData && (
        <EditServedQuantityModal
          item={editModalData.item}
          orderId={editModalData.orderId}
          onEdit={handleEditServedQuantity}
          onClose={() => setEditModalData(null)}
        />
      )}
    </div>
  );
}

// Order Card Component
interface OrderCardProps {
  order: Order;
  onEdit: () => void;
  onGenerateBill: () => void;
  onCancel: () => void;
  onOpenServeModal: (item: OrderItem) => void;
  onOpenEditModal: (item: OrderItem) => void;
}

function OrderCard({ order, onEdit, onGenerateBill, onCancel, onOpenServeModal, onOpenEditModal }: OrderCardProps) {
  const [showItems, setShowItems] = useState(false);
  const itemCount = order.order_items?.length || 0;

  return (
    <div className="bg-off-white border border-neutral-border rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-neutral-text-dark">
            Table {order.table_number}
          </h3>
          {order.customer_name && (
            <p className="text-sm text-neutral-text-light mt-1">
              {order.customer_name}
            </p>
          )}
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold font-heading text-coffee-brown">
            {formatCurrency(order.total_amount)}
          </p>
        </div>
      </div>

      {/* Order Info */}
      <div className="flex items-center justify-between text-sm text-neutral-text-light mb-4">
        <span>
          {itemCount} {itemCount === 1 ? 'item' : 'items'}
        </span>
        <span>{formatDateTime(order.created_at)}</span>
      </div>

      {/* View Items Toggle */}
      <button
        onClick={() => setShowItems(!showItems)}
        className="w-full text-left text-sm font-medium text-coffee-brown hover:text-coffee-dark mb-3 flex items-center gap-2 transition-colors"
      >
        <svg
          className={`w-4 h-4 transition-transform ${showItems ? 'rotate-90' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        {showItems ? 'Hide Items' : 'View Items'}
      </button>

      {/* Menu Items List */}
      {showItems && (
        <div className="mb-4 space-y-3">
          {/* Dine-in Items */}
          {order.order_items.filter(item => !item.is_parcel).length > 0 && (
            <div className="border border-neutral-border rounded-lg overflow-hidden bg-white">
              <div className="bg-neutral-background px-3 py-2 border-b border-neutral-border">
                <h4 className="text-sm font-semibold text-neutral-text-dark">DINE-IN:</h4>
              </div>
              <div className="max-h-64 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-white border-b border-neutral-border sticky top-0 z-10">
                    <tr>
                      <th className="text-center p-2 font-semibold text-neutral-text-dark w-16">Status</th>
                      <th className="text-left p-2 font-semibold text-neutral-text-dark">Item</th>
                      <th className="text-center p-2 font-semibold text-neutral-text-dark">Qty</th>
                      <th className="text-center p-2 font-semibold text-neutral-text-dark w-24">Serve</th>
                    </tr>
                  </thead>
                  <tbody>
                    {order.order_items.filter(item => !item.is_parcel).map((item) => (
                  <tr key={item.id} className="border-b border-neutral-border last:border-0 hover:bg-neutral-background/50 transition-colors">
                    <td className="p-2 text-center" onClick={(e) => e.stopPropagation()}>
                      {item.is_served ? (
                        <span
                          onClick={() => onOpenEditModal(item)}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-white bg-lily-green px-2.5 py-1 rounded-full shadow-sm whitespace-nowrap cursor-pointer hover:bg-lily-green/90 transition-colors"
                          title="Click to edit served quantity"
                        >
                          ✓ Done
                        </span>
                      ) : item.quantity_served > 0 ? (
                        <span
                          onClick={() => onOpenEditModal(item)}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-orange-800 bg-orange-100 px-2.5 py-1 rounded-full border border-orange-200 whitespace-nowrap cursor-pointer hover:bg-orange-200 transition-colors"
                          title="Click to edit served quantity"
                        >
                          {item.quantity_served}/{item.quantity}
                        </span>
                      ) : (
                        <span
                          onClick={() => onOpenEditModal(item)}
                          className="inline-flex items-center gap-1 text-xs font-medium text-neutral-text-light bg-neutral-background px-2.5 py-1 rounded-full border border-neutral-border whitespace-nowrap cursor-pointer hover:bg-neutral-border/30 transition-colors"
                          title="Click to edit served quantity"
                        >
                          Pending
                        </span>
                      )}
                    </td>
                    <td className={`p-2 text-neutral-text-dark ${item.is_served ? 'line-through opacity-60' : ''}`}>
                      {item.menu_item_name}
                    </td>
                    <td className="p-2 text-center text-neutral-text-light">{item.quantity}</td>
                    <td className="p-2 text-center" onClick={(e) => e.stopPropagation()}>
                      {!item.is_served && (
                        <button
                          onClick={() => onOpenServeModal(item)}
                          className="text-xs font-medium text-coffee-brown hover:text-coffee-dark
                                     bg-coffee-brown/10 hover:bg-coffee-brown/20 px-3 py-1.5 rounded-lg
                                     transition-colors"
                        >
                          Serve
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

          {/* Parcel Items */}
          {order.order_items.filter(item => item.is_parcel).length > 0 && (
            <div className="border border-coffee-brown/30 rounded-lg overflow-hidden bg-white">
              <div className="bg-coffee-brown/10 px-3 py-2 border-b border-coffee-brown/30">
                <h4 className="text-sm font-semibold text-coffee-brown">PARCEL:</h4>
              </div>
              <div className="max-h-64 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-white border-b border-neutral-border sticky top-0 z-10">
                    <tr>
                      <th className="text-center p-2 font-semibold text-neutral-text-dark w-16">Status</th>
                      <th className="text-left p-2 font-semibold text-neutral-text-dark">Item</th>
                      <th className="text-center p-2 font-semibold text-neutral-text-dark">Qty</th>
                      <th className="text-center p-2 font-semibold text-neutral-text-dark w-24">Serve</th>
                    </tr>
                  </thead>
                  <tbody>
                    {order.order_items.filter(item => item.is_parcel).map((item) => (
                      <tr key={item.id} className="border-b border-neutral-border last:border-0 hover:bg-neutral-background/50 transition-colors">
                        <td className="p-2 text-center" onClick={(e) => e.stopPropagation()}>
                          {item.is_served ? (
                            <span
                              onClick={() => onOpenEditModal(item)}
                              className="inline-flex items-center gap-1 text-xs font-semibold text-white bg-lily-green px-2.5 py-1 rounded-full shadow-sm whitespace-nowrap cursor-pointer hover:bg-lily-green/90 transition-colors"
                              title="Click to edit served quantity"
                            >
                              ✓ Done
                            </span>
                          ) : item.quantity_served > 0 ? (
                            <span
                              onClick={() => onOpenEditModal(item)}
                              className="inline-flex items-center gap-1 text-xs font-semibold text-orange-800 bg-orange-100 px-2.5 py-1 rounded-full border border-orange-200 whitespace-nowrap cursor-pointer hover:bg-orange-200 transition-colors"
                              title="Click to edit served quantity"
                            >
                              {item.quantity_served}/{item.quantity}
                            </span>
                          ) : (
                            <span
                              onClick={() => onOpenEditModal(item)}
                              className="inline-flex items-center gap-1 text-xs font-medium text-neutral-text-light bg-neutral-background px-2.5 py-1 rounded-full border border-neutral-border whitespace-nowrap cursor-pointer hover:bg-neutral-border/30 transition-colors"
                              title="Click to edit served quantity"
                            >
                              Pending
                            </span>
                          )}
                        </td>
                        <td className={`p-2 text-neutral-text-dark ${item.is_served ? 'line-through opacity-60' : ''}`}>
                          {item.menu_item_name}
                        </td>
                        <td className="p-2 text-center text-neutral-text-light">{item.quantity}</td>
                        <td className="p-2 text-center" onClick={(e) => e.stopPropagation()}>
                          {!item.is_served && (
                            <button
                              onClick={() => onOpenServeModal(item)}
                              className="text-xs font-medium text-coffee-brown hover:text-coffee-dark
                                       bg-coffee-brown/10 hover:bg-coffee-brown/20 px-3 py-1.5 rounded-lg
                                       transition-colors"
                            >
                              Serve
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button
          onClick={onEdit}
          className="btn-secondary flex-1"
        >
          Edit
        </button>
        <button
          onClick={onGenerateBill}
          className="btn-success flex-1"
        >
          Generate Bill
        </button>
      </div>

      {/* Cancel Button */}
      <button
        onClick={onCancel}
        className="btn-destructive w-full mt-2"
      >
        Cancel Order
      </button>
    </div>
  );
}

