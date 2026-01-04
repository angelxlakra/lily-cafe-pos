// ========================================
// Analytics Dashboard Page
// Powered by Thesys C1 Generative UI
// ========================================

import { useState, useMemo } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Sidebar from '../components/Sidebar';
import DatePickerWithQuickFilters from '../components/DatePickerWithQuickFilters';
import { useRevenue, useProductPerformance, useOrderStatistics } from '../hooks/useAnalytics';
import { formatCurrency } from '../utils/formatCurrency';
import { useTheme } from '../contexts/ThemeContext';
import {
  ChartLine,
  Package,
  Receipt,
  TrendUp,
  Clock,
  Wallet,
  ChartBar,
} from '@phosphor-icons/react';
import { UpiIcon, CashIcon, CardIcon } from '../components/icons/PaymentIcons';

export default function AnalyticsPage() {
  const today = new Date().toISOString().split('T')[0];
  const [dateRange, setDateRange] = useState({ start: today, end: today });
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const { theme } = useTheme();

  // Fetch analytics data
  const { data: revenueData, isLoading: isLoadingRevenue } = useRevenue({
    start_date: dateRange.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange.end ? `${dateRange.end}T23:59:59Z` : undefined,
  });

  const { data: productData, isLoading: isLoadingProducts } = useProductPerformance({
    start_date: dateRange.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange.end ? `${dateRange.end}T23:59:59Z` : undefined,
    limit: 10,
  });

  const { data: orderStats, isLoading: isLoadingOrders } = useOrderStatistics({
    start_date: dateRange.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange.end ? `${dateRange.end}T23:59:59Z` : undefined,
  });

  const isLoading = isLoadingRevenue || isLoadingProducts || isLoadingOrders;

  // Theme-aware colors for charts
  const chartColors = {
    grid: theme === 'dark' ? '#374151' : '#e5e5e5',
    axis: theme === 'dark' ? '#9ca3af' : '#6b7280',
    tooltipBg: theme === 'dark' ? '#1f2937' : '#ffffff',
    tooltipBorder: theme === 'dark' ? '#374151' : '#e5e5e5',
    tooltipText: theme === 'dark' ? '#f3f4f6' : '#111827',
  };

  // Payment method icons
  const paymentIcons: Record<string, JSX.Element> = {
    upi: <UpiIcon size={24} weight="duotone" />,
    cash: <CashIcon size={24} weight="duotone" />,
    card: <CardIcon size={24} weight="duotone" />,
  };

  // Format revenue trend data for chart
  const revenueTrendData = useMemo(() => {
    if (!revenueData?.revenue_trend) return [];
    return revenueData.revenue_trend.map((item) => ({
      date: new Date(item.date).toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric'
      }),
      revenue: item.revenue,
    }));
  }, [revenueData]);

  // Format revenue by category for chart
  const categoryRevenueData = useMemo(() => {
    if (!productData?.revenue_by_category) return [];
    return Object.entries(productData.revenue_by_category).map(([name, revenue]) => ({
      name,
      revenue,
    }));
  }, [productData]);

  // Calculate comparison metrics (simulated - in production would compare with previous period)
  const revenueChange = useMemo(() => {
    if (!revenueData?.revenue_trend || revenueData.revenue_trend.length < 2) return 0;
    const trend = revenueData.revenue_trend;
    const latest = trend[trend.length - 1]?.revenue || 0;
    const previous = trend[trend.length - 2]?.revenue || 0;
    if (previous === 0) return 0;
    return ((latest - previous) / previous) * 100;
  }, [revenueData]);

  return (
    <div className="flex min-h-screen bg-neutral-background">
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      <div className="flex-1 p-6 md:p-8 lg:ml-60">
        {/* Header */}
        <div className="mb-6">
          <h1 className="font-heading heading-display text-coffee-brown mb-2">
            Analytics Dashboard
          </h1>
          <p className="text-neutral-text-light">
            View sales, revenue, and performance metrics powered by Thesys C1
          </p>
        </div>

        {/* Date Range Picker */}
        <div className="mb-6 bg-white p-4 rounded-lg border border-neutral-border">
          <DatePickerWithQuickFilters
            startDate={dateRange.start}
            endDate={dateRange.end}
            onChange={(start, end) => setDateRange({ start, end })}
          />
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-coffee-brown"></div>
          </div>
        )}

        {/* Analytics Content */}
        {!isLoading && (
          <div className="space-y-6">
            {/* Order Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Total Revenue Card */}
              <div className="bg-gradient-to-br from-coffee-brown to-coffee-dark p-6 rounded-lg shadow-md">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium" style={{ color: 'rgba(255, 255, 255, 0.9)' }}>Total Revenue</h3>
                  <Wallet size={24} weight="duotone" style={{ color: 'rgba(255, 255, 255, 0.8)' }} />
                </div>
                <p className="text-3xl font-bold mb-1" style={{ color: '#ffffff' }}>
                  {formatCurrency(revenueData?.total_revenue || 0)}
                </p>
                {revenueChange !== 0 && (
                  <p className="text-sm flex items-center gap-1" style={{ color: revenueChange > 0 ? '#86efac' : '#fca5a5' }}>
                    <TrendUp size={16} weight="bold" className={revenueChange < 0 ? 'rotate-180' : ''} />
                    {Math.abs(revenueChange).toFixed(1)}% vs previous
                  </p>
                )}
              </div>

              {/* Total Orders Card */}
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-neutral-border">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.9)' : '#6b7280' }}>Total Orders</h3>
                  <Receipt size={24} weight="duotone" className="text-info" />
                </div>
                <p className="text-3xl font-bold mb-1" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
                  {orderStats?.completed_orders || 0}
                </p>
                <p className="text-sm" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                  {orderStats?.active_orders || 0} active orders
                </p>
              </div>

              {/* Average Order Value Card */}
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-neutral-border">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.9)' : '#6b7280' }}>Avg Order Value</h3>
                  <ChartLine size={24} weight="duotone" className="text-lily-green" />
                </div>
                <p className="text-3xl font-bold mb-1" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
                  {formatCurrency(orderStats?.average_order_value || 0)}
                </p>
                <p className="text-sm" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                  Per completed order
                </p>
              </div>

              {/* Peak Hour Card */}
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-neutral-border">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.9)' : '#6b7280' }}>Peak Hour</h3>
                  <Clock size={24} weight="duotone" className="text-warning" />
                </div>
                <p className="text-3xl font-bold mb-1" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
                  {orderStats?.peak_hours?.[0]?.hour || 0}:00
                </p>
                <p className="text-sm" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                  {orderStats?.peak_hours?.[0]?.order_count || 0} orders
                </p>
              </div>
            </div>

            {/* Revenue Trend Chart */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-neutral-border">
              <div className="flex items-center gap-2 mb-4">
                <ChartLine size={24} weight="duotone" className="text-coffee-brown dark:text-gray-300" />
                <h2 className="font-heading text-xl" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>Revenue Trend</h2>
              </div>

              {revenueTrendData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={revenueTrendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                    <XAxis
                      dataKey="date"
                      stroke={chartColors.axis}
                      style={{ fontSize: '12px' }}
                    />
                    <YAxis
                      stroke={chartColors.axis}
                      style={{ fontSize: '12px' }}
                      tickFormatter={(value) => `₹${value}`}
                    />
                    <Tooltip
                      formatter={(value: number | undefined) => value !== undefined ? [`₹${value.toFixed(2)}`, 'Revenue'] : ['', '']}
                      contentStyle={{
                        backgroundColor: chartColors.tooltipBg,
                        border: `1px solid ${chartColors.tooltipBorder}`,
                        borderRadius: '8px',
                        color: chartColors.tooltipText
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="revenue"
                      stroke="#5C3D2E"
                      strokeWidth={2}
                      dot={{ fill: '#5C3D2E', r: 4 }}
                      activeDot={{ r: 6 }}
                      name="Revenue (₹)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-64" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                  <p>No revenue data for selected period</p>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top Products Table */}
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-neutral-border">
                <div className="flex items-center gap-2 mb-4">
                  <Package size={24} weight="duotone" className="text-coffee-brown dark:text-gray-300" />
                  <h2 className="font-heading text-xl" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>Top Products</h2>
                </div>

                {productData?.top_products && productData.top_products.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-neutral-border">
                          <th className="text-left py-2 px-2 text-sm font-medium" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                            Product
                          </th>
                          <th className="text-right py-2 px-2 text-sm font-medium" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                            Qty
                          </th>
                          <th className="text-right py-2 px-2 text-sm font-medium" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                            Revenue
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {productData.top_products.map((product, index) => (
                          <tr key={index} className="border-b border-neutral-border last:border-0">
                            <td className="py-3 px-2 text-sm font-medium" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
                              {product.name}
                            </td>
                            <td className="py-3 px-2 text-sm text-right" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.8)' : '#1f2937' }}>
                              {product.quantity_sold}
                            </td>
                            <td className="py-3 px-2 text-sm text-right font-medium" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
                              {formatCurrency(product.revenue)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-64" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                    <p>No product data for selected period</p>
                  </div>
                )}
              </div>

              {/* Revenue by Category Chart */}
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-neutral-border">
                <div className="flex items-center gap-2 mb-4">
                  <ChartBar size={24} weight="duotone" className="text-coffee-brown dark:text-gray-300" />
                  <h2 className="font-heading text-xl" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>Revenue by Category</h2>
                </div>

                {categoryRevenueData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={categoryRevenueData}>
                      <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                      <XAxis
                        dataKey="name"
                        stroke={chartColors.axis}
                        style={{ fontSize: '12px' }}
                      />
                      <YAxis
                        stroke={chartColors.axis}
                        style={{ fontSize: '12px' }}
                        tickFormatter={(value) => `₹${value}`}
                      />
                      <Tooltip
                        formatter={(value: number | undefined) => value !== undefined ? [`₹${value.toFixed(2)}`, 'Revenue'] : ['', '']}
                        contentStyle={{
                          backgroundColor: chartColors.tooltipBg,
                          border: `1px solid ${chartColors.tooltipBorder}`,
                          borderRadius: '8px',
                          color: chartColors.tooltipText
                        }}
                      />
                      <Legend />
                      <Bar
                        dataKey="revenue"
                        fill="#5C3D2E"
                        name="Revenue (₹)"
                        radius={[8, 8, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-64" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                    <p>No category data for selected period</p>
                  </div>
                )}
              </div>
            </div>

            {/* Revenue by Payment Method */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-neutral-border">
              <h2 className="font-heading text-xl mb-4" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
                Revenue by Payment Method
              </h2>

              {revenueData?.revenue_by_payment_method && Object.keys(revenueData.revenue_by_payment_method).length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(revenueData.revenue_by_payment_method).map(([method, amount]) => (
                    <div
                      key={method}
                      className="flex items-center justify-between p-4 rounded-lg bg-neutral-background dark:bg-gray-700 border border-neutral-border"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-full bg-coffee-brown/10 dark:bg-gray-600 flex items-center justify-center text-coffee-brown dark:text-gray-300">
                          {paymentIcons[method] || method.toUpperCase()}
                        </div>
                        <div>
                          <p className="text-sm capitalize" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>{method}</p>
                          <p className="text-lg font-bold" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
                            {formatCurrency(amount)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center h-32" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                  <p>No payment data for selected period</p>
                </div>
              )}
            </div>

            {/* Thesys C1 Conversational Interface - Coming Soon */}
            <div className="bg-gradient-to-br from-lily-green/10 to-info/10 dark:from-lily-green/20 dark:to-info/20 p-6 rounded-lg border border-lily-green/30 dark:border-lily-green/50">
              <h2 className="font-heading text-xl mb-2" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
                Ask Questions About Your Data
              </h2>
              <p className="mb-4" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.8)' : '#6b7280' }}>
                Thesys C1 Conversational Analytics - Coming in next update
              </p>
              <p className="text-sm italic" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                Ask natural language questions like "Show me sales trends for last month" or
                "Which products perform best on weekends?"
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
