// ========================================
// Order History Page
// View past orders with date filtering
// ========================================

import { useState } from 'react';
import Sidebar from '../components/Sidebar';
import EmptyState from '../components/EmptyState';
import { useOrderHistory, useOrder } from '../hooks/useOrders';
import { useAppConfig } from '../hooks/useConfig';
import { formatCurrency } from '../utils/formatCurrency';
import { formatDateTime } from '../utils/formatDateTime';
import { CalendarDots, Printer } from '@phosphor-icons/react';
import { paymentsApi } from '../api/client';

export default function OrderHistoryPage() {
  // Get today's date for max date validation
  const today = new Date().toISOString().split('T')[0];

  // Default to yesterday to avoid potential issues with today's date
  const getYesterday = () => {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return yesterday.toISOString().split('T')[0];
  };

  const [selectedDate, setSelectedDate] = useState(getYesterday());
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const { data: orderHistory, isLoading, error } = useOrderHistory({
    date: selectedDate,
  });

  const { data: selectedOrder, isLoading: isLoadingDetails } = useOrder(
    selectedOrderId || 0
  );

  const { data: appConfig } = useAppConfig();

  const orders = orderHistory || [];

  const handleViewDetails = (orderId: number) => {
    setSelectedOrderId(orderId);
  };

  const handleCloseModal = () => {
    setSelectedOrderId(null);
  };

  const handlePrintReceipt = async (orderId: number) => {
    try {
      await paymentsApi.printReceipt(orderId);
    } catch (error) {
      console.error('Failed to print receipt:', error);
      alert('Failed to print receipt. Please try again.');
    }
  };

  const gstRatePercent = appConfig?.gst_rate ?? 18;
  const gstRateLabel = Number.isInteger(gstRatePercent)
    ? String(gstRatePercent)
    : gstRatePercent.toFixed(2);

  // Calculate daily totals
  const dailyTotal = orders.reduce((sum, order) => sum + order.total_amount, 0);
  const dailyOrderCount = orders.length;

  return (
    <div className="flex min-h-screen bg-neutral-background">
      {/* Sidebar */}
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      {/* Main Content */}
      <div className="flex-1 lg:ml-60 flex flex-col">
        {/* Header */}
        <header className="bg-off-white border-b border-neutral-border p-4 md:p-6">
          <div className="flex items-center gap-4 mb-4">
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
              <h1 className="font-heading heading-section text-coffee-brown">
                Order History
              </h1>
              <p className="text-sm text-muted mt-1">
                View past orders and daily sales
              </p>
            </div>
          </div>

          {/* Date Picker */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <label className="text-sm font-medium text-neutral-text-dark">
              Date:
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              max={today}
              className="px-4 py-2 border border-neutral-border rounded-lg focus:outline-none focus:ring-2 focus:ring-coffee-brown w-full sm:w-auto"
            />
          </div>
        </header>

        {/* Daily Summary */}
        {!isLoading && !error && orders.length > 0 && (
          <div className="p-4 sm:p-6 bg-off-white border-b border-neutral-border">
            <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 xl:grid-cols-3">
              <div className="bg-lily-green/10 border border-lily-green rounded-lg p-4">
                <p className="text-sm text-neutral-text-light mb-1">Total Orders</p>
                <p className="text-2xl font-bold font-heading text-coffee-brown">
                  {dailyOrderCount}
                </p>
              </div>
              <div className="bg-coffee-light/10 border border-coffee-light rounded-lg p-4">
                <p className="text-sm text-neutral-text-light mb-1">Daily Revenue</p>
                <p className="text-2xl font-bold font-heading text-coffee-brown">
                  {formatCurrency(dailyTotal)}
                </p>
              </div>
              <div className="bg-cream border border-neutral-border rounded-lg p-4">
                <p className="text-sm text-neutral-text-light mb-1">Average Order</p>
                <p className="text-2xl font-bold font-heading text-coffee-brown">
                  {formatCurrency(Math.round(dailyTotal / dailyOrderCount))}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <main className="p-4 sm:p-6 flex-1">
          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <div className="animate-spin h-12 w-12 border-4 border-coffee-brown border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-neutral-text-light">Loading order history...</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-error/10 border border-error rounded-lg p-4">
              <p className="text-error font-medium">
                Failed to load order history
              </p>
              <p className="text-sm text-error/80 mt-2">
                {error instanceof Error && error.message.includes('422')
                  ? 'The selected date may be invalid or no orders exist for this date. Try selecting a different date.'
                  : error instanceof Error
                    ? error.message
                    : 'Please check your connection and try again.'}
              </p>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && orders.length === 0 && (
            <EmptyState
              icon={<CalendarDots size={32} weight="duotone" />}
              title="No orders on this date"
              description="Try picking another day or adjust your search criteria."
              actionLabel="Jump to today"
              onAction={() => setSelectedDate(today)}
            />
          )}

          {/* Orders Table */}
          {!isLoading && orders.length > 0 && (
            <div className="bg-off-white border border-neutral-border rounded-lg overflow-hidden">
              {/* Desktop Table */}
              <div className="hidden md:block">
                <table className="w-full">
                  <thead className="bg-cream border-b border-neutral-border">
                    <tr>
                      <th className="px-6 py-3 text-left text-sm font-semibold text-neutral-text-dark">
                        Order #
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-neutral-text-dark">
                      Table
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-neutral-text-dark">
                      Customer
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-neutral-text-dark">
                      Time
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-neutral-text-dark">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-sm font-semibold text-neutral-text-dark">
                      Total
                    </th>
                    <th className="px-6 py-3 text-right text-sm font-semibold text-neutral-text-dark">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-border">
                  {orders.map((order) => (
                    <tr
                      key={order.id}
                      className="hover:bg-cream/50 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <p className="font-mono text-sm text-neutral-text-dark">
                          {order.order_number}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="font-medium text-neutral-text-dark">
                          Table {order.table_number}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-neutral-text-dark">
                          {order.customer_name || '—'}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-neutral-text-light">
                          {formatDateTime(order.created_at)}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-neutral-text-light">—</p>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <p className="font-semibold text-coffee-brown">
                          {formatCurrency(order.total_amount)}
                        </p>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handlePrintReceipt(order.id)}
                            className="px-3 py-1 text-sm bg-lily-green/10 border border-lily-green text-lily-green hover:bg-lily-green hover:text-white rounded-md transition-colors flex items-center gap-1"
                            title="Print Receipt"
                          >
                            <Printer size={16} weight="bold" />
                            <span className="hidden lg:inline">Print</span>
                          </button>
                          <button
                            onClick={() => handleViewDetails(order.id)}
                            className="px-3 py-1 text-sm bg-cream border border-coffee-light text-coffee-brown hover:bg-coffee-light hover:text-white rounded-md transition-colors"
                          >
                            View Details
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>

              {/* Mobile Cards */}
              <div className="md:hidden p-4 space-y-4">
                {orders.map((order) => (
                  <div
                    key={order.id}
                    className="rounded-xl border border-neutral-border bg-cream/50 p-4 space-y-3"
                  >
                    <div className="flex flex-wrap justify-between gap-2">
                      <div>
                        <p className="text-xs text-neutral-text-light uppercase tracking-wide">
                          Order #
                        </p>
                        <p className="font-mono text-sm text-neutral-text-dark">
                          {order.order_number}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-neutral-text-light uppercase tracking-wide">
                          Total
                        </p>
                        <p className="font-semibold text-coffee-brown">
                          {formatCurrency(order.total_amount)}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                      <div>
                        <p className="text-neutral-text-light">Table</p>
                        <p className="font-medium text-neutral-text-dark">
                          Table {order.table_number}
                        </p>
                      </div>
                      <div>
                        <p className="text-neutral-text-light">Customer</p>
                        <p className="text-neutral-text-dark">
                          {order.customer_name || '—'}
                        </p>
                      </div>
                      <div className="sm:col-span-2">
                        <p className="text-neutral-text-light">Time</p>
                        <p className="text-neutral-text-dark">
                          {formatDateTime(order.created_at)}
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handlePrintReceipt(order.id)}
                        className="px-4 py-2 text-sm bg-lily-green/10 border border-lily-green text-lily-green hover:bg-lily-green hover:text-white rounded-md transition-colors flex items-center justify-center gap-1"
                        title="Print Receipt"
                      >
                        <Printer size={16} weight="bold" />
                        Print
                      </button>
                      <button
                        onClick={() => handleViewDetails(order.id)}
                        className="flex-1 px-4 py-2 text-sm bg-cream border border-coffee-light text-coffee-brown hover:bg-coffee-light hover:text-white rounded-md transition-colors"
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Order Details Modal */}
      {selectedOrderId && (
        <OrderDetailsModal
          order={selectedOrder}
          isLoading={isLoadingDetails}
          onClose={handleCloseModal}
          onPrintReceipt={handlePrintReceipt}
          gstRateLabel={gstRateLabel}
        />
      )}
    </div>
  );
}

// Order Details Modal Component
interface OrderDetailsModalProps {
  order: any;
  isLoading: boolean;
  onClose: () => void;
  onPrintReceipt: (orderId: number) => void;
  gstRateLabel: string;
}

function OrderDetailsModal({
  order,
  isLoading,
  onClose,
  onPrintReceipt,
  gstRateLabel,
}: OrderDetailsModalProps) {
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-[60]"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                   w-full max-w-lg bg-off-white rounded-2xl shadow-2xl z-[70]
                   flex flex-col max-h-[90vh]"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-border">
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
        <div className="flex-1 overflow-y-auto p-6">
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
                  <span className="font-mono font-medium text-neutral-text-dark">
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
                <h3 className="font-semibold text-neutral-text-dark mb-3">Items</h3>
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
                          Qty: {item.quantity} � {formatCurrency(item.unit_price)}
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
        <div className="p-6 border-t border-neutral-border">
          <div className="flex gap-3">
            <button
              onClick={() => order && onPrintReceipt(order.id)}
              disabled={!order}
              className="flex-1 px-4 py-2 bg-lily-green/10 border border-lily-green text-lily-green hover:bg-lily-green hover:text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium"
            >
              <Printer size={20} weight="bold" />
              Print Receipt
            </button>
            <button
              onClick={onClose}
              className="btn-primary flex-1"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
