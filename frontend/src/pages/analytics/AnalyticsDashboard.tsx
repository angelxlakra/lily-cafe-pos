
import { useState, useMemo } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import DatePickerWithQuickFilters, { quickFilters } from '../../components/DatePickerWithQuickFilters';
import { useRevenue, useProductPerformance, useOrderStatistics, useHeatmap, useCalendarHeatmap } from '../../hooks/useAnalytics';
import { formatCurrency } from '../../utils/formatCurrency';
import { useTheme } from '../../contexts/ThemeContext';
import {
  ChartLine,
  Package,
  Receipt,
  TrendUp,
  Clock,
  Wallet,
  ChartBar,
  ListBullets,
  ChartPie,
  Gear,
  SquaresFour,
  Calendar
} from '@phosphor-icons/react';
import { UpiIcon, CashIcon, CardIcon } from '../../components/icons/PaymentIcons';
import AnalyticsSettingsModal, { AVAILABLE_CHARTS, ChartVisibility } from '../../components/analytics/AnalyticsSettingsModal';
import OrderHeatmap from '../../components/analytics/charts/OrderHeatmap';
import CalendarHeatmap from '../../components/analytics/charts/CalendarHeatmap';
import CategoryTreemap from '../../components/analytics/charts/CategoryTreemap';
import InventoryTreemap from '../../components/analytics/charts/InventoryTreemap';
import ProductBubbleChart from '../../components/analytics/charts/ProductBubbleChart';
import PaymentRadialBar from '../../components/analytics/charts/PaymentRadialBar';
import FunnelChart from '../../components/analytics/charts/FunnelChart';
import RevenueStackedArea from '../../components/analytics/charts/RevenueStackedArea';
import OrderStatusStream from '../../components/analytics/charts/OrderStatusStream';
import DayOfWeekRadar from '../../components/analytics/charts/DayOfWeekRadar';
import OrderValueBoxPlot from '../../components/analytics/charts/OrderValueBoxPlot';
import ItemQuantityBoxPlot from '../../components/analytics/charts/ItemQuantityBoxPlot';
import OrderSankey from '../../components/analytics/charts/OrderSankey';
import RevenueWaterfall from '../../components/analytics/charts/RevenueWaterfall';
import InventoryWaterfall from '../../components/analytics/charts/InventoryWaterfall';
import OrderTimeline from '../../components/analytics/charts/OrderTimeline';

type TopDishesView = 'list' | 'bar' | 'pie';

export default function AnalyticsDashboard() {
  const today = new Date().toISOString().split('T')[0];
  // Default to "All Time" (last 3 months)
  const allTimeFilter = quickFilters.find(f => f.label === 'All Time');
  const initialRange = allTimeFilter ? allTimeFilter.getRange() : { start: today, end: today };

  const [dateRange, setDateRange] = useState(initialRange);
  const [topDishesView, setTopDishesView] = useState<TopDishesView>('list');
  const { theme } = useTheme();

  // Settings Modal State
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  
  // Chart Visibility State
  const [visibleCharts, setVisibleCharts] = useState<ChartVisibility>(() => {
    const saved = localStorage.getItem('analytics_visible_charts');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse saved chart visibility', e);
      }
    }
    // Default all to true
    return AVAILABLE_CHARTS.reduce((acc, chart) => {
      acc[chart.id] = true;
      return acc;
    }, {} as ChartVisibility);
  });

  const handleToggleChart = (chartId: string) => {
    setVisibleCharts(prev => {
      const next = { ...prev, [chartId]: !prev[chartId] };
      localStorage.setItem('analytics_visible_charts', JSON.stringify(next));
      return next;
    });
  };

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

  const { data: heatmapData, isLoading: isLoadingHeatmap } = useHeatmap({
    start_date: dateRange.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange.end ? `${dateRange.end}T23:59:59Z` : undefined,
  });

  const { data: calendarHeatmapData, isLoading: isLoadingCalendarHeatmap } = useCalendarHeatmap({
    // Always fetch last 365 days for calendar view if no range, or respect range?
    // Docs say "Yearly view", usually always shows last year.
    // Let's pass undefined to let backend handle default (last 365 days)
    // or just pass the current range if user wants to zoom in (but UI is designed for full year)
    // Actually, backend defaults to 365 days if no params.
    // But if we pass `dateRange` which is likely "Today" or "This Week", it restricts the data.
    // We should probably NOT pass `dateRange` if we want the full year context, 
    // OR we only show it when "All Time" or long range is selected.
    // For now, let's fetch full year context always for this chart.
   });

  const isLoading = isLoadingRevenue || isLoadingProducts || isLoadingOrders || isLoadingHeatmap || isLoadingCalendarHeatmap;

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
    
    // Check if we are viewing a single day
    const isSingleDay = dateRange.start === dateRange.end;

    // Trim leading and trailing zeros
    const trend = [...revenueData.revenue_trend];
    
    // Find first non-zero index
    let firstNonZero = 0;
    while (firstNonZero < trend.length && trend[firstNonZero].revenue === 0) {
      firstNonZero++;
    }
    
    // If all are zero, return empty or keep as is?
    // If we want to show "No data", returning empty is better.
    if (firstNonZero === trend.length) return [];

    // Find last non-zero index
    let lastNonZero = trend.length - 1;
    while (lastNonZero >= 0 && trend[lastNonZero].revenue === 0) {
      lastNonZero--;
    }
    
    const trimmedTrend = trend.slice(firstNonZero, lastNonZero + 1);

    return trimmedTrend.map((item) => ({
      date: new Date(item.date).toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric',
        // If single day, show hour
        ...(isSingleDay && { hour: 'numeric', minute: 'numeric', hour12: true, day: undefined, month: undefined })
      }),
      // For single day, we might want a shorter label like "10 AM"
      originalDate: item.date,
      revenue: item.revenue,
    }));
  }, [revenueData, dateRange]);

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

  // Format payment method data for pie chart
  const paymentPieData = useMemo(() => {
    if (!revenueData?.revenue_by_payment_method) return [];
    const total = Object.values(revenueData.revenue_by_payment_method).reduce((sum, val) => sum + (val as number), 0);
    return Object.entries(revenueData.revenue_by_payment_method).map(([method, amount]) => ({
      name: method.charAt(0).toUpperCase() + method.slice(1),
      value: amount as number,
      percentage: total > 0 ? ((amount as number / total) * 100).toFixed(1) : '0',
    }));
  }, [revenueData]);

  // Format top products for bar chart
  const topProductsChartData = useMemo(() => {
    if (!productData?.top_products) return [];
    return productData.top_products.slice(0, 5).map((product: any) => ({
      name: product.name.length > 15 ? product.name.substring(0, 15) + '...' : product.name,
      fullName: product.name,
      quantity: product.quantity_sold,
      revenue: product.revenue,
    }));
  }, [productData]);

  // Format top dishes for pie chart
  const topDishesPieData = useMemo(() => {
    if (!productData?.top_products) return [];
    const topFive = productData.top_products.slice(0, 5);
    const totalRevenue = topFive.reduce((sum: number, p: any) => sum + p.revenue, 0);
    return topFive.map((product: any) => ({
      name: product.name.length > 20 ? product.name.substring(0, 20) + '...' : product.name,
      fullName: product.name,
      value: product.revenue,
      quantity: product.quantity_sold,
      percentage: totalRevenue > 0 ? ((product.revenue / totalRevenue) * 100).toFixed(1) : '0',
    }));
  }, [productData]);

  // Colors for pie charts
  const PIE_COLORS = ['#5C3D2E', '#8B6F47', '#A88B6A', '#C9A86A', '#E4C9A0'];

  return (
    <div>
      <AnalyticsSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        visibleCharts={visibleCharts}
        onToggleChart={handleToggleChart}
      />

        {/* Date Range Picker and Settings */}
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="flex-1 p-4 rounded-lg border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
            <DatePickerWithQuickFilters
              startDate={dateRange.start}
              endDate={dateRange.end}
              onChange={(start, end) => setDateRange({ start, end })}
            />
          </div>
          
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-neutral-border hover:bg-neutral-light transition-colors self-start md:self-stretch"
            style={{ 
              backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
              color: theme === 'dark' ? '#ffffff' : '#5C3D2E' 
            }}
          >
            <Gear size={20} weight="duotone" />
            <span>Customize Dashboard</span>
          </button>
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
            {/* Order Statistics Cards - Always Visible */}
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
              <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
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
              <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
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
              <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
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

            {/* Calendar Heatmap (Yearly View) */}
             {visibleCharts.calendarHeatmap && (
              <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                <div className="flex items-center gap-2 mb-4">
                  <Calendar size={24} weight="duotone" className="text-coffee-brown dark:text-gray-300" />
                  <h2 className="font-heading text-xl" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
                    Yearly Activity
                  </h2>
                </div>
                
                 {calendarHeatmapData?.data && calendarHeatmapData.data.length > 0 ? (
                    <CalendarHeatmap data={calendarHeatmapData.data} />
                ) : (
                    <div className="flex items-center justify-center h-64" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                        <p>No activity data available</p>
                    </div>
                )}
              </div>
            )}
            
            {/* Revenue Trend Chart */}
            {visibleCharts.revenueTrend && (
              <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
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
                        tickFormatter={formatCurrency}
                      />
                      <Tooltip
                        formatter={(value: number | undefined) => value !== undefined ? [formatCurrency(value), 'Revenue'] : ['', '']}
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
            )}

            {/* Time-based Order Heatmap */}
            {visibleCharts.orderHeatmap && (
              <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                <div className="flex items-center gap-2 mb-4">
                  <SquaresFour size={24} weight="duotone" className="text-coffee-brown dark:text-gray-300" />
                  <h2 className="font-heading text-xl" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>Busy Times</h2>
                </div>
                
                {heatmapData?.data && heatmapData.data.length > 0 ? (
                    <OrderHeatmap data={heatmapData.data} />
                ) : (
                    <div className="flex items-center justify-center h-64" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                        <p>No activity data for selected period</p>
                    </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top Dishes with View Toggle */}
              {visibleCharts.topDishes && (
                <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Package size={24} weight="duotone" className="text-coffee-brown dark:text-gray-300" />
                      <h2 className="font-heading text-xl" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>Top Dishes</h2>
                    </div>

                    {/* View Toggle */}
                    <div className="flex gap-1 p-1 rounded-lg border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#374151' : '#f5f5f5' }}>
                      <button
                        onClick={() => setTopDishesView('list')}
                        className={`p-2 rounded transition-colors ${
                          topDishesView === 'list' ? 'bg-coffee-brown text-white' : 'hover:bg-neutral-light'
                        }`}
                        title="List View"
                      >
                        <ListBullets size={18} weight={topDishesView === 'list' ? 'bold' : 'regular'} />
                      </button>
                      <button
                        onClick={() => setTopDishesView('bar')}
                        className={`p-2 rounded transition-colors ${
                          topDishesView === 'bar' ? 'bg-coffee-brown text-white' : 'hover:bg-neutral-light'
                        }`}
                        title="Bar Chart"
                      >
                        <ChartBar size={18} weight={topDishesView === 'bar' ? 'bold' : 'regular'} />
                      </button>
                      <button
                        onClick={() => setTopDishesView('pie')}
                        className={`p-2 rounded transition-colors ${
                          topDishesView === 'pie' ? 'bg-coffee-brown text-white' : 'hover:bg-neutral-light'
                        }`}
                        title="Pie Chart"
                      >
                        <ChartPie size={18} weight={topDishesView === 'pie' ? 'bold' : 'regular'} />
                      </button>
                    </div>
                  </div>

                  {/* List View */}
                  {topDishesView === 'list' && (
                    <>
                      {productData?.top_products && productData.top_products.length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead>
                              <tr className="border-b border-neutral-border">
                                <th className="text-left py-2 px-2 text-sm font-medium" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                                  Dish
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
                              {productData.top_products.slice(0, 10).map((product: any, index: number) => (
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
                    </>
                  )}

                  {/* Bar Chart View */}
                  {topDishesView === 'bar' && (
                    <>
                      {topProductsChartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={topProductsChartData} layout="horizontal">
                            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                            <XAxis
                              dataKey="name"
                              stroke={chartColors.axis}
                              style={{ fontSize: '11px' }}
                              angle={-45}
                              textAnchor="end"
                              height={80}
                            />
                            <YAxis
                              stroke={chartColors.axis}
                              style={{ fontSize: '12px' }}
                            />
                            <Tooltip
                              formatter={(value: number | undefined, name: any) => {
                                if (name === 'Quantity') return [value, 'Quantity Sold'];
                                return value !== undefined ? [formatCurrency(value), 'Revenue'] : ['', ''];
                              }}
                              contentStyle={{
                                backgroundColor: chartColors.tooltipBg,
                                border: `1px solid ${chartColors.tooltipBorder}`,
                                borderRadius: '8px',
                                color: chartColors.tooltipText
                              }}
                            />
                            <Legend />
                            <Bar
                              dataKey="quantity"
                              fill="#8B6F47"
                              name="Quantity"
                              radius={[8, 8, 0, 0]}
                            />
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
                          <p>No product data for selected period</p>
                        </div>
                      )}
                    </>
                  )}

                  {/* Pie Chart View */}
                  {topDishesView === 'pie' && (
                    <>
                      {topDishesPieData.length > 0 ? (
                        <div className="flex flex-col items-center">
                          <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                              <Pie
                                data={topDishesPieData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ payload }) => `${payload.percentage}%`}
                                outerRadius={90}
                                fill="#8884d8"
                                dataKey="value"
                              >
                                {topDishesPieData.map((_, index) => (
                                  <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip
                                formatter={(value: number | undefined) => value !== undefined ? [formatCurrency(value), 'Revenue'] : ['', '']}
                                contentStyle={{
                                  backgroundColor: chartColors.tooltipBg,
                                  border: `1px solid ${chartColors.tooltipBorder}`,
                                  borderRadius: '8px',
                                  color: chartColors.tooltipText
                                }}
                              />
                            </PieChart>
                          </ResponsiveContainer>

                          {/* Legend */}
                          <div className="grid grid-cols-1 gap-2 mt-2 w-full">
                            {topDishesPieData.map((entry, index) => (
                              <div key={entry.name} className="flex items-center justify-between px-2">
                                <div className="flex items-center gap-2">
                                  <div
                                    className="w-3 h-3 rounded-full"
                                    style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }}
                                  />
                                  <span className="text-xs font-medium" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
                                    {entry.name}
                                  </span>
                                </div>
                                <span className="text-xs" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.8)' : '#6b7280' }}>
                                  {formatCurrency(entry.value)} ({entry.percentage}%)
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center h-64" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                          <p>No product data for selected period</p>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {/* Revenue by Category Chart */}
              {visibleCharts.revenueByCategory && (
                <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
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
              )}
            </div>

            {/* Revenue by Payment Method - Pie Chart */}
            {visibleCharts.revenueByPaymentMethod && (
              <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                <div className="flex items-center gap-2 mb-4">
                  <Wallet size={24} weight="duotone" className="text-coffee-brown dark:text-gray-300" />
                  <h2 className="font-heading text-xl" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
                    Revenue by Payment Method
                  </h2>
                </div>

                {paymentPieData.length > 0 ? (
                  <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="flex-1">
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={paymentPieData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, payload }) => `${name}: ${payload.percentage}%`}
                            outerRadius={100}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {paymentPieData.map((_, index) => (
                              <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip
                            formatter={(value: number | undefined) => value !== undefined ? [`₹${value.toFixed(2)}`, 'Revenue'] : ['', '']}
                            contentStyle={{
                              backgroundColor: chartColors.tooltipBg,
                              border: `1px solid ${chartColors.tooltipBorder}`,
                              borderRadius: '8px',
                              color: chartColors.tooltipText
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Legend with values */}
                    <div className="flex-shrink-0 space-y-3">
                      {paymentPieData.map((entry, index) => (
                        <div key={entry.name} className="flex items-center gap-3">
                          <div
                            className="w-4 h-4 rounded-full"
                            style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }}
                          />
                          <div>
                            <div className="flex items-center gap-2">
                              {paymentIcons[entry.name.toLowerCase()] || entry.name.toUpperCase()}
                              <span className="text-sm font-medium" style={{ color: theme === 'dark' ? '#ffffff' : '#5C3D2E' }}>
                                {entry.name}
                              </span>
                            </div>
                            <p className="text-sm" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.8)' : '#6b7280' }}>
                              {formatCurrency(entry.value)} ({entry.percentage}%)
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-64" style={{ color: theme === 'dark' ? 'rgba(255, 255, 255, 0.6)' : '#6b7280' }}>
                    <p>No payment data for selected period</p>
                  </div>
                )}
              </div>
            )}

            {/* =====================================================================================
                NEW CHART SECTIONS
               ===================================================================================== */}
            
            {/* --- Sales Performance Section --- */}
            {(visibleCharts.categoryTreemap || visibleCharts.productBubble || visibleCharts.revenueStacked || visibleCharts.revenueWaterfall || visibleCharts.paymentRadial) && (
             <div className="space-y-6">
                 <h2 className="text-2xl font-bold font-heading" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Sales Performance</h2>
                 <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                     
                     {visibleCharts.categoryTreemap && (
                         <div className="p-6 rounded-lg shadow-md border border-neutral-border col-span-1 lg:col-span-2" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                             <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Category Composition</h3>
                             <CategoryTreemap dateRange={dateRange} />
                         </div>
                     )}

                     {visibleCharts.revenueStacked && (
                         <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                             <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Revenue Composition Trend</h3>
                             <RevenueStackedArea dateRange={dateRange} />
                         </div>
                     )}

                     {visibleCharts.revenueWaterfall && (
                         <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                             <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Revenue Breakdown (Waterfall)</h3>
                             <RevenueWaterfall date={dateRange.start} />
                         </div>
                     )}

                     {visibleCharts.productBubble && (
                         <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                             <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Product Matrix</h3>
                             <ProductBubbleChart dateRange={dateRange} />
                         </div>
                     )}

                     {visibleCharts.paymentRadial && (
                         <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                             <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Payment Trends</h3>
                             <PaymentRadialBar dateRange={dateRange} />
                         </div>
                     )}
                 </div>
             </div>
            )}

            {/* --- Order Insights Section --- */}
            {(visibleCharts.orderFunnel || visibleCharts.orderStatusStream || visibleCharts.orderSankey || visibleCharts.orderTimeline || visibleCharts.dayRadar || visibleCharts.orderValueBox) && (
                <div className="space-y-6">
                    <h2 className="text-2xl font-bold font-heading" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Order Insights</h2>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                        {visibleCharts.orderSankey && (
                            <div className="p-6 rounded-lg shadow-md border border-neutral-border col-span-1 lg:col-span-2" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                                <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Category to Payment Flow</h3>
                                <OrderSankey dateRange={dateRange} />
                            </div>
                        )}

                        {visibleCharts.orderTimeline && (
                            <div className="p-6 rounded-lg shadow-md border border-neutral-border col-span-1 lg:col-span-2" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                                <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Order Timeline (Gantt)</h3>
                                <OrderTimeline date={dateRange.start} />
                            </div>
                        )}

                        {visibleCharts.orderFunnel && (
                            <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                                <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Order Completion Funnel</h3>
                                <FunnelChart dateRange={dateRange} />
                            </div>
                        )}
                        
                        {visibleCharts.orderStatusStream && (
                            <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                                <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Order Status Flow</h3>
                                <OrderStatusStream dateRange={dateRange} />
                            </div>
                        )}

                        {visibleCharts.dayRadar && (
                            <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                                <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Daily Performance Radar</h3>
                                <DayOfWeekRadar dateRange={dateRange} />
                            </div>
                        )}

                        {visibleCharts.orderValueBox && (
                            <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                                <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Order Value Distribution</h3>
                                <OrderValueBoxPlot dateRange={dateRange} />
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* --- Inventory Section --- */}
            {(visibleCharts.inventoryTreemap || visibleCharts.inventoryWaterfall || visibleCharts.itemQuantityBox) && (
                <div className="space-y-6">
                    <h2 className="text-2xl font-bold font-heading" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Inventory & Items</h2>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        
                        {visibleCharts.inventoryTreemap && (
                            <div className="p-6 rounded-lg shadow-md border border-neutral-border col-span-1 lg:col-span-2" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                                <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Inventory Value Map</h3>
                                <InventoryTreemap />
                            </div>
                        )}

                        {visibleCharts.inventoryWaterfall && (
                            <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                                <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Inventory Value Change</h3>
                                <InventoryWaterfall date={dateRange.start} />
                            </div>
                        )}

                        {visibleCharts.itemQuantityBox && (
                            <div className="p-6 rounded-lg shadow-md border border-neutral-border" style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}>
                                <h3 className="text-lg font-bold mb-4" style={{ color: theme === 'dark' ? '#fff' : '#5C3D2E' }}>Item Quantity Distribution</h3>
                                <ItemQuantityBoxPlot dateRange={dateRange} />
                            </div>
                        )}
                    </div>
                </div>
            )}
          </div>
        )}
    </div>
  );
}
