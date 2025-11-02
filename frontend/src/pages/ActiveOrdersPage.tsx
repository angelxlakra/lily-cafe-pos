// ========================================
// Active Orders Page Component
// Read-only view of all active orders (for waiters)
// ========================================

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useActiveOrders, useOrder } from "../hooks/useOrders";
import { useAppConfig } from "../hooks/useConfig";
import { formatCurrency } from "../utils/formatCurrency";
import { formatDateTime } from "../utils/formatDateTime";
import BottomNav from "../components/BottomNav";
import EmptyState from "../components/EmptyState";
import { Tray } from "@phosphor-icons/react";
import type { Order } from "../types";

export default function ActiveOrdersPage() {
  const { data: activeOrders, isLoading, error } = useActiveOrders();
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);
  const navigate = useNavigate();

  const { data: selectedOrder, isLoading: isLoadingDetails } = useOrder(
    selectedOrderId || 0
  );
  const { data: appConfig } = useAppConfig();

  const orders = activeOrders || [];

  const handleViewDetails = (orderId: number) => {
    setSelectedOrderId(orderId);
  };

  const handleCloseModal = () => {
    setSelectedOrderId(null);
  };

  const gstRatePercent = appConfig?.gst_rate ?? 18;
  const gstRateLabel = Number.isInteger(gstRatePercent)
    ? String(gstRatePercent)
    : gstRatePercent.toFixed(2);

  return (
    <div className="min-h-screen bg-neutral-background pb-16">
      {/* Header */}
      <header className="bg-coffee-brown text-cream p-4 sticky top-0 z-30 shadow-md">
        <h1 className="font-heading heading-sub text-center">Active Orders</h1>
      </header>

      {/* Main Content */}
      <main className="px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
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
                {error instanceof Error
                  ? error.message
                  : "Failed to load active orders"}
              </p>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && orders.length === 0 && (
            <EmptyState
              icon={<Tray size={32} weight="duotone" />}
              title="No active orders"
              description="Orders will appear here once tables place them."
              actionLabel="Go to tables"
              onAction={() => navigate("/tables")}
            />
          )}

          {/* Orders List */}
          {!isLoading && orders.length > 0 && (
            <div className="space-y-3">
              {orders.map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  onViewDetails={() => handleViewDetails(order.id)}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Bottom Navigation */}
      <BottomNav />

      {/* Order Details Modal */}
      {selectedOrderId && (
        <OrderDetailsModal
          order={selectedOrder}
          isLoading={isLoadingDetails}
          onClose={handleCloseModal}
          gstRateLabel={gstRateLabel}
        />
      )}
    </div>
  );
}

// Order Card Component
interface OrderCardProps {
  order: Order;
  onViewDetails: () => void;
}

function OrderCard({ order, onViewDetails }: OrderCardProps) {
  const itemCount = order.order_items?.length || 0;

  return (
    <div className="bg-off-white border border-neutral-border rounded-lg p-4 shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-semibold text-neutral-text-dark">
            Table {order.table_number}
          </h3>
          {order.customer_name && (
            <p className="text-sm text-neutral-text-light">
              {order.customer_name}
            </p>
          )}
        </div>
        <div className="text-right">
          <p className="text-lg font-bold font-heading text-coffee-brown">
            {formatCurrency(order.total_amount)}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-neutral-text-light mb-3">
        <span>
          {itemCount} {itemCount === 1 ? "item" : "items"}
        </span>
        <span>{formatDateTime(order.created_at)}</span>
      </div>

      <button
        onClick={onViewDetails}
        className="btn-secondary w-full"
      >
        View Details
      </button>
    </div>
  );
}

// Order Details Modal Component
interface OrderDetailsModalProps {
  order: any; // Full Order type
  isLoading: boolean;
  onClose: () => void;
  gstRateLabel: string;
}

function OrderDetailsModal({
  order,
  isLoading,
  onClose,
  gstRateLabel,
}: OrderDetailsModalProps) {
  console.log({ order });
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-[60] animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="fixed inset-4 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2
                   md:w-full md:max-w-lg
                   bg-off-white rounded-2xl shadow-2xl
                   z-[70] animate-scale-in
                   flex flex-col max-h-[90vh]"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-neutral-border">
          <h2 className="text-lg font-semibold text-neutral-text-dark">
            Order Details
          </h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-neutral-border transition-colors"
            aria-label="Close"
          >
            <span className="text-xl text-neutral-text-light">&times;</span>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-coffee-brown border-t-transparent rounded-full"></div>
            </div>
          ) : order ? (
            <div className="space-y-4">
              {/* Order Info */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-text-light">Order Number:</span>
                  <span className="font-medium text-neutral-text-dark">
                    {order.order_number}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-text-light">Table:</span>
                  <span className="font-medium text-neutral-text-dark">
                    {order.table_number}
                  </span>
                </div>
                {order.customer_name && (
                  <div className="flex justify-between text-sm">
                    <span className="text-neutral-text-light">Customer:</span>
                    <span className="font-medium text-neutral-text-dark">
                      {order.customer_name}
                    </span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-text-light">Time:</span>
                  <span className="font-medium text-neutral-text-dark">
                    {formatDateTime(order.created_at)}
                  </span>
                </div>
              </div>

              <div className="border-t border-neutral-border"></div>

              {/* Items */}
              <div>
                <h3 className="font-semibold text-neutral-text-dark mb-3">
                  Items
                </h3>
                <div className="space-y-2">
                  {order.order_items.map((item: any, index: number) => (
                    <div
                      key={index}
                      className="flex justify-between items-start bg-cream rounded-lg p-3"
                    >
                      <div className="flex-1">
                        <p className="font-medium text-neutral-text-dark">
                          {item.menu_item_name}
                        </p>
                        <p className="text-sm text-neutral-text-light">
                          Qty: {item.quantity} ×{" "}
                          {formatCurrency(item.unit_price)}
                        </p>
                      </div>
                      <p className="font-semibold text-coffee-brown">
                        {formatCurrency(item.subtotal)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t border-neutral-border"></div>

              {/* Totals */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-text-light">Subtotal:</span>
                  <span className="font-semibold text-neutral-text-dark">
                    {formatCurrency(order.subtotal)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-text-light">
                    SGST ({(parseFloat(gstRateLabel) / 2).toFixed(2)}%):
                  </span>
                  <span className="font-semibold text-neutral-text-dark">
                    {formatCurrency(Math.round(order.gst_amount / 2))}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-text-light">
                    CGST ({(parseFloat(gstRateLabel) / 2).toFixed(2)}%):
                  </span>
                  <span className="font-semibold text-neutral-text-dark">
                    {formatCurrency(order.gst_amount - Math.round(order.gst_amount / 2))}
                  </span>
                </div>
                <div className="border-t border-neutral-border pt-2">
                  <div className="flex justify-between text-lg">
                    <span className="font-semibold text-neutral-text-dark">
                      Total:
                    </span>
                    <span className="font-bold font-heading text-coffee-brown">
                      {formatCurrency(order.total_amount)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-center text-neutral-text-light py-8">
              Failed to load order details
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-neutral-border">
          <button
            onClick={onClose}
            className="btn-primary w-full"
          >
            Close
          </button>
        </div>
      </div>

      {/* Custom animations */}
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes scale-in {
          from {
            transform: scale(0.95);
            opacity: 0;
          }
          to {
            transform: scale(1);
            opacity: 1;
          }
        }

        .animate-fade-in {
          animation: fade-in 0.2s ease-out;
        }

        .animate-scale-in {
          animation: scale-in 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
      `}</style>
    </>
  );
}
