
import { ChartBar, Check } from '@phosphor-icons/react';
import { useTheme } from '../../contexts/ThemeContext';

export type ChartVisibility = {
  [key: string]: boolean;
};

export const AVAILABLE_CHARTS = [
  { id: 'revenueTrend', label: 'Revenue Trend', description: 'Line chart showing revenue over time' },
  { id: 'topDishes', label: 'Top Dishes', description: 'List or chart of best selling items' },
  { id: 'revenueByCategory', label: 'Revenue by Category', description: 'Bar chart of revenue distribution across categories' },
  { id: 'revenueByPaymentMethod', label: 'Revenue by Payment Method', description: 'Pie chart of payment method usage' },
  { id: 'orderHeatmap', label: 'Order Heatmap', description: 'Heatmap showing busy hours by day of week' },
  { id: 'calendarHeatmap', label: 'Calendar Heatmap', description: 'Yearly view of daily revenue intensity' },
  
  // Group 1
  { id: 'categoryTreemap', label: 'Category Composition', description: 'Treemap of category revenue' },
  { id: 'inventoryTreemap', label: 'Inventory Value Map', description: 'Treemap of inventory value' },
  { id: 'productBubble', label: 'Product Matrix (Bubble)', description: 'Volume vs Revenue vs Frequency' },
  { id: 'paymentRadial', label: 'Payment Trends (Radial)', description: 'Payment method volume and value' },
  { id: 'orderFunnel', label: 'Order Completion Funnel', description: 'Conversion from placed to paid' },

  // Group 2
  { id: 'revenueStacked', label: 'Revenue Composition Trend', description: 'Stacked area of category revenue' },
  { id: 'orderStatusStream', label: 'Order Status Flow', description: 'Stream graph of order statuses' },
  { id: 'dayRadar', label: 'Daily Performance Radar', description: 'Radar chart of day-of-week metrics' },
  { id: 'orderValueBox', label: 'Order Value Distribution', description: 'Box plot of order values' },
  { id: 'itemQuantityBox', label: 'Item Quantity Distribution', description: 'Box plot of item quantities' },

  // Group 3
  { id: 'orderSankey', label: 'Order Flow (Sankey)', description: 'Flow from Category to Payment' },
  { id: 'revenueWaterfall', label: 'Revenue Waterfall', description: 'Detailed breakdown of daily revenue' },
  { id: 'inventoryWaterfall', label: 'Inventory Waterfall', description: 'Inventory value changes' },
  { id: 'orderTimeline', label: 'Order Timeline (Gantt)', description: 'Gantt chart of orders over time' },
];

interface AnalyticsSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  visibleCharts: ChartVisibility;
  onToggleChart: (chartId: string) => void;
}

export default function AnalyticsSettingsModal({
  isOpen,
  onClose,
  visibleCharts,
  onToggleChart,
}: AnalyticsSettingsModalProps) {
  const { theme } = useTheme();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div
        className="w-full max-w-md rounded-lg shadow-xl overflow-hidden animate-in fade-in zoom-in duration-200 bg-off-white"
      >
        {/* Header */}
        <div
          style={{ background: 'linear-gradient(135deg, #C27A2A, #a06020)' }}
          className="flex items-center gap-3 px-5 py-4 flex-shrink-0"
        >
          <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
            <ChartBar size={20} weight="duotone" color="white" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-white font-heading italic text-base font-bold leading-tight">
              Chart Settings
            </h2>
            <p className="text-white/70 text-xs mt-0.5">Show or hide dashboard charts</p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-white/60 hover:text-white text-xl leading-none ml-auto flex-shrink-0"
          >
            &times;
          </button>
        </div>

        {/* Content */}
        <div className="p-4 max-h-[70vh] overflow-y-auto">
          <p className="text-sm mb-4" style={{ color: theme === 'dark' ? '#d1d5db' : '#4b5563' }}>
            Select which charts to display on your analytics dashboard using the toggles below.
          </p>

          <div className="space-y-3">
            {AVAILABLE_CHARTS.map((chart) => (
              <div 
                key={chart.id}
                className="flex items-start gap-3 p-3 rounded-lg border border-neutral-border cursor-pointer transition-colors bg-cream"
                style={{
                    borderColor: visibleCharts[chart.id] ? (theme === 'dark' ? '#A88B6A' : '#5C3D2E') : undefined
                }}
                onClick={() => onToggleChart(chart.id)}
              >
                <div 
                  className={`mt-0.5 w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 transition-colors ${
                    visibleCharts[chart.id] 
                      ? 'bg-coffee-brown border-coffee-brown text-white' 
                      : 'border-gray-400 bg-transparent'
                  }`}
                >
                  {visibleCharts[chart.id] && <Check size={12} weight="bold" />}
                </div>
                <div>
                  <h3 className="text-sm font-medium" style={{ color: theme === 'dark' ? '#ffffff' : '#1f2937' }}>
                    {chart.label}
                  </h3>
                  <p className="text-xs" style={{ color: theme === 'dark' ? '#9ca3af' : '#6b7280' }}>
                    {chart.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-neutral-border flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-coffee-brown text-white font-medium hover:bg-coffee-dark transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
