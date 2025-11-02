// ========================================
// Admin Active Orders Page
// Desktop interface with edit/bill/cancel actions
// ========================================

import { useState } from 'react';
import Sidebar from '../components/Sidebar';
import PaymentModal from '../components/PaymentModal';
import { useActiveOrders, useCancelOrder } from '../hooks/useOrders';
import { formatCurrency } from '../utils/formatCurrency';
import { formatDateTime } from '../utils/formatDateTime';
import type { Order } from '../types';

export default function AdminActiveOrdersPage() {
  const { data: activeOrders, isLoading, error } = useActiveOrders();
  const [paymentOrderId, setPaymentOrderId] = useState<number | null>(null);
  const [cancelOrderId, setCancelOrderId] = useState<number | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const cancelMutation = useCancelOrder();

  const orders = activeOrders || [];

  const handleGenerateBill = (orderId: number) => {
    setPaymentOrderId(orderId);
  };

  const handleCancelOrder = async () => {
    if (!cancelOrderId) return;

    try {
      await cancelMutation.mutateAsync(cancelOrderId);
      setCancelOrderId(null);
    } catch (error) {
      console.error('Failed to cancel order:', error);
    }
  };

  return (
    <div className="flex min-h-screen bg-neutral-background">
      {/* Sidebar */}
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      {/* Main Content */}
      <div className="flex-1 lg:ml-60">
        {/* Header */}
        <header className="bg-off-white border-b border-neutral-border p-4 md:p-6">
          <div className="flex items-center gap-4">
            {/* Hamburger Menu Button */}
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden w-10 h-10 flex items-center justify-center rounded-lg bg-coffee-brown text-cream hover:bg-coffee-dark transition-colors"
              aria-label="Open menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex-1">
              <h1 className="text-xl md:text-2xl font-bold text-coffee-brown">Active Orders</h1>
              <p className="text-sm text-neutral-text-light mt-1">
                Manage ongoing orders, generate bills, and process payments
              </p>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="p-6">
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
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <p className="text-neutral-text-light text-lg mb-2">
                  No active orders
                </p>
                <p className="text-neutral-text-light text-sm">
                  Orders will appear here once tables place them
                </p>
              </div>
            </div>
          )}

          {/* Orders Grid */}
          {!isLoading && orders.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              {orders.map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  onGenerateBill={() => handleGenerateBill(order.id)}
                  onCancel={() => setCancelOrderId(order.id)}
                />
              ))}
            </div>
          )}
        </main>
      </div>

      {/* Payment Modal */}
      {paymentOrderId && (
        <PaymentModal
          orderId={paymentOrderId}
          onClose={() => setPaymentOrderId(null)}
        />
      )}

      {/* Cancel Confirmation Modal */}
      {cancelOrderId && (
        <ConfirmCancelModal
          onConfirm={handleCancelOrder}
          onCancel={() => setCancelOrderId(null)}
          isLoading={cancelMutation.isPending}
        />
      )}
    </div>
  );
}

// Order Card Component
interface OrderCardProps {
  order: Order;
  onGenerateBill: () => void;
  onCancel: () => void;
}

function OrderCard({ order, onGenerateBill, onCancel }: OrderCardProps) {
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
          <p className="text-2xl font-bold text-coffee-brown">
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

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button
          onClick={onGenerateBill}
          className="flex-1 btn bg-lily-green text-white hover:bg-[#7A8C75]"
        >
          Generate Bill
        </button>
      </div>

      {/* Cancel Button */}
      <button
        onClick={onCancel}
        className="btn w-full mt-2 bg-error/10 border border-error text-error hover:bg-error hover:text-white"
      >
        Cancel Order
      </button>
    </div>
  );
}

// Confirm Cancel Modal
interface ConfirmCancelModalProps {
  onConfirm: () => void;
  onCancel: () => void;
  isLoading: boolean;
}

function ConfirmCancelModal({ onConfirm, onCancel, isLoading }: ConfirmCancelModalProps) {
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-[60]"
        onClick={onCancel}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                   w-full max-w-md bg-off-white rounded-2xl shadow-2xl z-[70] p-6"
        role="dialog"
        aria-modal="true"
      >
        <h2 className="text-xl font-bold text-neutral-text-dark mb-4">
          Cancel Order?
        </h2>
        <p className="text-neutral-text-light mb-6">
          Are you sure you want to cancel this order? This action cannot be undone.
        </p>

        <div className="flex gap-3">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1 btn bg-cream border border-neutral-border text-neutral-text-dark hover:bg-neutral-border"
          >
            No, Keep It
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 btn bg-error text-white hover:bg-[#D32F2F]"
          >
            {isLoading ? 'Canceling...' : 'Yes, Cancel'}
          </button>
        </div>
      </div>
    </>
  );
}
