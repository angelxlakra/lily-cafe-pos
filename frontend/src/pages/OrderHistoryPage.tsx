// ========================================
// Order History Page
// View past orders with date filtering
// ========================================

import { useState, useMemo } from 'react';
import EmptyState from '../components/EmptyState';
import DatePickerWithQuickFilters from '../components/DatePickerWithQuickFilters';
import SortableTableHeader from '../components/SortableTableHeader';
import { useOrderHistory, useOrder, useUpdatePayments, useCancelOrder } from '../hooks/useOrders';
import { useAppConfig } from '../hooks/useConfig';
import { useSortableTable } from '../hooks/useSortableTable';
import { formatCurrency } from '../utils/formatCurrency';
import { formatDateTime } from '../utils/formatDateTime';
import { CalendarDots, Printer, PencilSimple, MagnifyingGlass, X, CaretLeft, CaretRight, Trash } from '@phosphor-icons/react';
import { UpiIcon, CashIcon, CardIcon } from '../components/icons/PaymentIcons';
import DailyRevenueModal from '../components/DailyRevenueModal';
import EditPaymentsModal from '../components/EditPaymentsModal';
import { paymentsApi } from '../api/client';
import type { PaymentMethod, PaymentCreateRequest, Order } from '../types';
import PageHeader from '../components/PageHeader';
import AdminStatsBar from '../components/AdminStatsBar';

export default function OrderHistoryPage() {
  // Get today's date for max date validation
  const today = new Date().toISOString().split('T')[0];


  const [dateRange, setDateRange] = useState({ start: today, end: today });
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);
  const [isRevenueModalOpen, setIsRevenueModalOpen] = useState(false);
  const [editPaymentsOrder, setEditPaymentsOrder] = useState<Order | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [cancelOrderId, setCancelOrderId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'paid' | 'canceled'>('all');
  const [isBreakdownOpen, setIsBreakdownOpen] = useState(false);

  // Payment method icons
  const paymentIcons: Record<PaymentMethod, JSX.Element> = {
    upi: <UpiIcon size={18} weight="duotone" className="text-coffee-brown" />,
    cash: <CashIcon size={18} weight="duotone" className="text-coffee-brown" />,
    card: <CardIcon size={18} weight="duotone" className="text-coffee-brown" />,
  };

  // Helper to render payment method icons for an order
  const renderPaymentMethods = (order: any) => {
    if (!order.payments || order.payments.length === 0) {
      return <span className="text-neutral-text-light text-sm">—</span>;
    }

    // Get unique payment methods
    const uniqueMethods = Array.from(
      new Set(order.payments.map((p: any) => p.payment_method))
    ) as PaymentMethod[];

    return (
      <div className="flex items-center gap-1.5">
        {uniqueMethods.map((method) => (
          <span
            key={method}
            className="inline-flex items-center justify-center w-7 h-7 rounded-md bg-coffee-brown/10 border border-coffee-brown/20"
            title={method.toUpperCase()}
          >
            {paymentIcons[method]}
          </span>
        ))}
      </div>
    );
  };

  // Helper to render status badge
  const renderStatusBadge = (status: 'active' | 'paid' | 'canceled') => {
    if (status === 'canceled') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-md bg-error/10 text-error border border-error/20">
          Cancelled
        </span>
      );
    }
    return null;
  };

  const { data: orderHistoryData, isLoading, error } = useOrderHistory({
    start_date: dateRange.start,
    end_date: dateRange.end,
    page,
    size: pageSize,
  });

  const allOrders = orderHistoryData?.items || [];
  const totalPages = orderHistoryData?.pages || 0;

  const { data: selectedOrder, isLoading: isLoadingDetails } = useOrder(
    selectedOrderId || 0
  );

  const { data: appConfig } = useAppConfig();
  const updatePaymentsMutation = useUpdatePayments();
  const cancelOrderMutation = useCancelOrder();

  // Filter orders based on search query and status
  const filteredOrders = useMemo(() => {
    let filtered = allOrders;

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(order => order.status === statusFilter);
    }

    // Apply search query
    if (!searchQuery.trim()) return filtered;

    const query = searchQuery.toLowerCase();
    return filtered.filter(order => {
      // Search by table number
      if (order.table_number.toString().includes(query)) return true;

      // Search by customer name
      if (order.customer_name?.toLowerCase().includes(query)) return true;

      // Search by order ID
      if (order.id.toString().includes(query)) return true;

      // Search by amount (convert to rupees for better UX)
      const amountInRupees = (order.total_amount / 100).toString();
      if (amountInRupees.includes(query)) return true;

      return false;
    });
  }, [allOrders, searchQuery, statusFilter]);

  // Computed stats for AdminStatsBar
  const totalRevenue = filteredOrders
    .filter(o => o.status !== 'canceled')
    .reduce((sum, o) => sum + o.total_amount, 0);
  const avgOrder = filteredOrders.length > 0
    ? Math.round(totalRevenue / filteredOrders.filter(o => o.status !== 'canceled').length) || 0
    : 0;

  // Payment breakdown by method from filteredOrders
  const methodBreakdown = (() => {
    const paidOrders = filteredOrders.filter(o => o.status !== 'canceled' && o.payments && o.payments.length > 0);
    const byMethod: Record<string, number> = {};
    paidOrders.forEach(o => {
      o.payments.forEach((p: any) => {
        const m = p.payment_method || 'unknown';
        byMethod[m] = (byMethod[m] || 0) + p.amount;
      });
    });
    const total = Object.values(byMethod).reduce((s, v) => s + v, 0);
    return Object.entries(byMethod).map(([method, amount]) => ({
      method,
      amount,
      pct: total > 0 ? Math.round((amount / total) * 100) : 0,
    }));
  })();

  // Add display_time to orders based on payment time or created_at
  const processedOrders = useMemo(() => {
    return filteredOrders.map(order => {
      let displayTime = order.created_at;
      if (order.payments && order.payments.length > 0) {
        // Find latest payment time
        const latestPayment = order.payments.reduce((prev, current) => {
          return new Date(prev.created_at) > new Date(current.created_at) ? prev : current;
        });
        displayTime = latestPayment.created_at;
      }
      return {
        ...order,
        display_time: displayTime
      };
    });
  }, [filteredOrders]);

  // Add sorting to filtered orders
  const { sortedData: orders, sortConfig, requestSort } = useSortableTable(
    processedOrders,
    'display_time' as keyof typeof processedOrders[0], // Use dynamic key
    'desc'
  );

  const handleViewDetails = (orderId: number) => {
    setSelectedOrderId(orderId);
  };

  const handleCloseModal = () => {
    setSelectedOrderId(null);
  };

  const handleEditPayments = (order: Order) => {
    setEditPaymentsOrder(order);
  };

  const handleSavePayments = async (orderId: number, payments: PaymentCreateRequest[]) => {
    try {
      await updatePaymentsMutation.mutateAsync({
        orderId,
        data: { payments },
      });
      setEditPaymentsOrder(null);
    } catch (error) {
      console.error('Failed to update payments:', error);
    }
  };

  const handlePrintReceipt = async (orderId: number) => {
    try {
      await paymentsApi.printReceipt(orderId);
    } catch (error) {
      console.error('Failed to print receipt:', error);
      alert('Failed to print receipt. Please try again.');
    }
  };

  const handleCancelOrder = async () => {
    if (!cancelOrderId) return;

    try {
      await cancelOrderMutation.mutateAsync(cancelOrderId);
      setCancelOrderId(null);
    } catch (error) {
      console.error('Failed to cancel order:', error);
      alert('Failed to cancel order. Please try again.');
    }
  };

  const gstRatePercent = appConfig?.gst_rate ?? 18;
  const gstRateLabel = Number.isInteger(gstRatePercent)
    ? String(gstRatePercent)
    : gstRatePercent.toFixed(2);

  // Calculate stats based on server data (for the full period)
  const periodTotalRevenue = orderHistoryData?.total_revenue || 0;

  // Calculate payment method breakdown
  // Prefer server-side breakdown if available, otherwise fallback to local (though local is only current page)
  const paymentBreakdown = orderHistoryData?.payment_breakdown || orders.reduce(
    (acc, order) => {
      if (order.payments) {
        order.payments.forEach((payment: any) => {
          if (payment.payment_method === 'cash') acc.cash += payment.amount;
          else if (payment.payment_method === 'upi') acc.upi += payment.amount;
          else if (payment.payment_method === 'card') acc.card += payment.amount;
        });
      }
      return acc;
    },
    { cash: 0, upi: 0, card: 0 }
  );

  return (
    <div className="flex flex-col h-full bg-neutral-background">
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <PageHeader title="Order History" subtitle="Review and manage completed orders" />
        <AdminStatsBar
          stats={[
            { label: 'Total Orders', value: String(filteredOrders.length) },
            {
              label: 'Revenue',
              value: formatCurrency(totalRevenue),
              clickable: true,
              onClick: () => setIsBreakdownOpen(prev => !prev),
              hint: '↗ tap for breakdown',
            },
            { label: 'Avg Order', value: formatCurrency(avgOrder) },
          ]}
        />

        {/* Revenue Breakdown Panel */}
        {isBreakdownOpen && (
          <div className="flex gap-3 px-4 py-3 border-b border-neutral-border bg-cream/40 overflow-x-auto">
            {methodBreakdown.map(b => (
              <div key={b.method} className="flex-shrink-0 bg-off-white border border-neutral-border rounded-lg px-3 py-2 min-w-[100px]">
                <p className="text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">{b.method}</p>
                <p className="text-sm font-bold text-coffee-brown">{formatCurrency(b.amount)}</p>
                <p className="text-[10px] text-neutral-text-light">{b.pct}%</p>
              </div>
            ))}
          </div>
        )}

        {/* Filters */}
        <div className="p-4 md:p-6 bg-off-white border-b border-neutral-border">
          {/* Date Picker and Search */}
          <div className="space-y-4">
            {/* Date Picker with Quick Filters */}
            <DatePickerWithQuickFilters
              startDate={dateRange.start}
              endDate={dateRange.end}
              onChange={(start, end) => {
                setDateRange({ start, end });
                setPage(1);
              }}
              max={today}
            />

            {/* Search Bar */}
            <div className="relative">
              <MagnifyingGlass
                size={20}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-text-light"
                aria-hidden="true"
              />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by table, customer, order ID, or amount..."
                className="w-full pl-10 pr-10 py-2 border border-neutral-border dark:border-neutral-700 rounded-lg bg-white dark:bg-neutral-800 text-neutral-text-dark dark:text-neutral-text-light focus:outline-none focus:ring-2 focus:ring-coffee-brown"
                aria-label="Search orders"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-text-light hover:text-neutral-text-dark dark:hover:text-white transition-colors"
                  aria-label="Clear search"
                >
                  <X size={18} aria-hidden="true" />
                </button>
              )}
            </div>

            {/* Status Filter */}
            <div className="flex gap-2">
              <button
                onClick={() => setStatusFilter('all')}
                className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                  statusFilter === 'all'
                    ? 'bg-coffee-brown text-white'
                    : 'bg-white border border-neutral-border text-neutral-text-dark hover:bg-cream'
                }`}
              >
                All Orders
              </button>
              <button
                onClick={() => setStatusFilter('paid')}
                className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                  statusFilter === 'paid'
                    ? 'bg-coffee-brown text-white'
                    : 'bg-white border border-neutral-border text-neutral-text-dark hover:bg-cream'
                }`}
              >
                Paid Only
              </button>
              <button
                onClick={() => setStatusFilter('canceled')}
                className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                  statusFilter === 'canceled'
                    ? 'bg-error text-white'
                    : 'bg-white border border-neutral-border text-neutral-text-dark hover:bg-cream'
                }`}
              >
                Cancelled Only
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <main className="p-4 sm:p-6 flex-1">
          {/* Loading State — skeleton */}
          {isLoading && (
            <div className="p-6 animate-pulse space-y-2">
              <div className="flex gap-0 border border-neutral-border rounded-lg overflow-hidden mb-4">
                {[1,2,3].map(i => (
                  <div key={i} className="flex-1 h-14 bg-neutral-border/50" />
                ))}
              </div>
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-10 w-full bg-neutral-border/50 rounded" />
              ))}
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
              icon={searchQuery ? <MagnifyingGlass size={32} weight="duotone" /> : <CalendarDots size={32} weight="duotone" />}
              title={searchQuery ? "No matching orders" : "No orders in this period"}
              description={
                searchQuery
                  ? `No orders found matching "${searchQuery}". Try a different search term.`
                  : "No orders were placed on this date. Try picking another day."
              }
              actionLabel={searchQuery ? "Clear search" : "Jump to today"}
              onAction={() => searchQuery ? setSearchQuery('') : setDateRange({ start: today, end: today })}
              secondaryActionLabel={searchQuery ? "Jump to today" : undefined}
              onSecondaryAction={searchQuery ? () => setDateRange({ start: today, end: today }) : undefined}
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
                      <SortableTableHeader<any>
                        label="Order #"
                        sortKey={'id' as any}
                        currentSortKey={sortConfig.key as any}
                        sortDirection={sortConfig.direction}
                        onSort={requestSort as any}
                        align="left"
                      />
                      <SortableTableHeader<any>
                        label="Table"
                        sortKey={'table_number' as any}
                        currentSortKey={sortConfig.key as any}
                        sortDirection={sortConfig.direction}
                        onSort={requestSort as any}
                        align="left"
                      />
                      <SortableTableHeader<any>
                        label="Customer"
                        sortKey={'customer_name' as any}
                        currentSortKey={sortConfig.key as any}
                        sortDirection={sortConfig.direction}
                        onSort={requestSort as any}
                        align="left"
                      />
                      <SortableTableHeader<any>
                        label="Time"
                        sortKey={'display_time' as any}
                        currentSortKey={sortConfig.key as any}
                        sortDirection={sortConfig.direction}
                        onSort={requestSort as any}
                        align="left"
                      />
                      <th className="px-4 py-3 text-left text-sm font-semibold text-neutral-text-light uppercase tracking-wider">
                        Payment Mode
                      </th>
                      <SortableTableHeader<any>
                        label="Total"
                        sortKey={'total_amount' as any}
                        currentSortKey={sortConfig.key as any}
                        sortDirection={sortConfig.direction}
                        onSort={requestSort as any}
                        align="right"
                      />
                      <th className="px-4 py-3 text-right text-sm font-semibold text-neutral-text-light uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                <tbody className="divide-y divide-neutral-border">
                  {orders.map((order) => (
                    <tr
                      key={order.id}
                      onClick={() => handleViewDetails(order.id)}
                      className="hover:bg-cream/40 transition-colors cursor-pointer"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <p className="font-mono text-sm text-neutral-text-dark">
                            {order.order_number}
                          </p>
                          {renderStatusBadge(order.status)}
                        </div>
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
                          {formatDateTime((order as any).display_time)}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        {renderPaymentMethods(order)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <p className={`font-semibold ${order.status === 'canceled' ? 'line-through text-neutral-text-light' : 'text-coffee-brown'}`}>
                          {formatCurrency(order.total_amount)}
                        </p>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {order.status !== 'canceled' && (
                            <>
                              <button
                                onClick={(e) => { e.stopPropagation(); handlePrintReceipt(order.id); }}
                                className="px-3 py-1 text-sm bg-lily-green/10 border border-lily-green text-lily-green hover:bg-lily-green hover:text-white rounded-md transition-colors flex items-center gap-1"
                                title="Print Receipt"
                              >
                                <Printer size={16} weight="bold" />
                                <span className="hidden lg:inline">Print</span>
                              </button>
                              <button
                                onClick={(e) => { e.stopPropagation(); handleEditPayments(order); }}
                                className="px-3 py-1 text-sm bg-coffee-brown/10 border border-coffee-brown text-coffee-brown hover:bg-coffee-brown hover:text-white rounded-md transition-colors flex items-center gap-1"
                                title="Edit Payments"
                              >
                                <PencilSimple size={16} weight="bold" />
                                <span className="hidden lg:inline">Edit</span>
                              </button>
                            </>
                          )}
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
                    onClick={() => handleViewDetails(order.id)}
                    className="rounded-xl border border-neutral-border bg-cream/50 p-4 space-y-3 cursor-pointer hover:bg-cream/40 transition-colors"
                  >
                    <div className="flex flex-wrap justify-between gap-2">
                      <div>
                        <p className="text-xs text-neutral-text-light uppercase tracking-wide">
                          Order #
                        </p>
                        <div className="flex items-center gap-2">
                          <p className="font-mono text-sm text-neutral-text-dark">
                            {order.order_number}
                          </p>
                          {renderStatusBadge(order.status)}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-neutral-text-light uppercase tracking-wide">
                          Total
                        </p>
                        <p className={`font-semibold ${order.status === 'canceled' ? 'line-through text-neutral-text-light' : 'text-coffee-brown'}`}>
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
                          {formatDateTime((order as any).display_time)}
                        </p>
                      </div>
                      <div className="sm:col-span-2">
                        <p className="text-neutral-text-light">Payment Mode</p>
                        <div className="mt-1">
                          {renderPaymentMethods(order)}
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-2 flex-wrap">
                      {order.status !== 'canceled' && (
                        <>
                          <button
                            onClick={(e) => { e.stopPropagation(); handlePrintReceipt(order.id); }}
                            className="px-4 py-2 text-sm bg-lily-green/10 border border-lily-green text-lily-green hover:bg-lily-green hover:text-white rounded-md transition-colors flex items-center justify-center gap-1"
                            title="Print Receipt"
                          >
                            <Printer size={16} weight="bold" />
                            Print
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleEditPayments(order); }}
                            className="px-4 py-2 text-sm bg-coffee-brown/10 border border-coffee-brown text-coffee-brown hover:bg-coffee-brown hover:text-white rounded-md transition-colors flex items-center justify-center gap-1"
                            title="Edit Payments"
                          >
                            <PencilSimple size={16} weight="bold" />
                            Edit
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {/* Pagination */}
          {!isLoading && totalPages > 1 && (
            <div className="flex items-center justify-between p-4 mt-4 border-t border-neutral-border bg-white dark:bg-neutral-800 rounded-lg shadow-sm">
              <p className="text-sm text-neutral-text-light">
                Page <span className="font-medium text-neutral-text-dark">{page}</span> of{' '}
                <span className="font-medium text-neutral-text-dark">{totalPages}</span>
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1.5 text-sm bg-white dark:bg-neutral-700 border border-neutral-border dark:border-neutral-600 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 transition-colors"
                >
                  <CaretLeft size={16} />
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1.5 text-sm bg-white dark:bg-neutral-700 border border-neutral-border dark:border-neutral-600 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 transition-colors"
                >
                  Next
                  <CaretRight size={16} />
                </button>
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

      {/* Edit Payments Modal */}
      {editPaymentsOrder && (
        <EditPaymentsModal
          order={editPaymentsOrder}
          onSave={handleSavePayments}
          onClose={() => setEditPaymentsOrder(null)}
          isSaving={updatePaymentsMutation.isPending}
          onCancelOrder={() => setCancelOrderId(editPaymentsOrder.id)}
        />
      )}

      {/* Cancel Order Confirmation Modal */}
      {cancelOrderId && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-[60]"
            onClick={() => setCancelOrderId(null)}
            aria-hidden="true"
          />

          {/* Modal */}
          <div
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                       w-full max-w-md bg-off-white rounded-2xl shadow-2xl z-[70] p-6"
            role="dialog"
            aria-modal="true"
          >
            <h3 className="text-lg font-semibold text-neutral-text-dark mb-4">
              Cancel Order?
            </h3>
            <p className="text-neutral-text-light mb-6">
              Are you sure you want to cancel this order? This will mark it as cancelled
              and it will no longer appear in active orders. This is useful for removing
              duplicate or mistaken orders.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setCancelOrderId(null)}
                className="px-4 py-2 text-sm bg-cream border border-coffee-light text-coffee-brown hover:bg-coffee-light/20 rounded-md transition-colors"
              >
                Keep Order
              </button>
              <button
                onClick={handleCancelOrder}
                disabled={cancelOrderMutation.isPending}
                className="px-4 py-2 text-sm bg-error border border-error text-white hover:bg-error/90 rounded-md transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {cancelOrderMutation.isPending ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                    Cancelling...
                  </>
                ) : (
                  <>
                    <Trash size={16} weight="bold" />
                    Yes, Cancel Order
                  </>
                )}
              </button>
            </div>
          </div>
        </>
      )}

      {/* Daily Revenue Modal */}
      <DailyRevenueModal
        isOpen={isRevenueModalOpen}
        onClose={() => setIsRevenueModalOpen(false)}
        data={{
          total: periodTotalRevenue,
          ...paymentBreakdown
        }}
        date={dateRange.start}
      />
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
                          Qty: {item.quantity}  {formatCurrency(item.unit_price)}
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
