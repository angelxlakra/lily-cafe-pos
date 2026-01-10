import React from 'react';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, CartesianGrid } from 'recharts';
import { useProductPerformanceDetailed } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface ProductBubbleChartProps {
  dateRange?: { start: string; end: string };
}

const ProductBubbleChart: React.FC<ProductBubbleChartProps> = ({ dateRange }) => {
  const { theme } = useTheme();
  const params: AnalyticsQueryParams = {
    start_date: dateRange?.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange?.end ? `${dateRange.end}T23:59:59Z` : undefined,
  };

  const { data, isLoading } = useProductPerformanceDetailed(params);

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (!data || data.top_products.length === 0) return <div className="h-64 flex items-center justify-center">No data available</div>;

  const chartData = data.top_products.map(p => ({
    ...p,
    name: p.name,
    x: p.quantity_sold,
    y: p.revenue_rupees,
    z: p.order_count,
  }));

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
          <XAxis 
            type="number" 
            dataKey="x" 
            name="Quantity" 
            unit=" units" 
            stroke={theme === 'dark' ? '#9ca3af' : '#4b5563'}
            label={{ value: 'Quantity Sold', position: 'bottom', offset: 0, fill: theme === 'dark' ? '#9ca3af' : '#4b5563' }}
          />
          <YAxis 
            type="number" 
            dataKey="y" 
            name="Revenue" 
            unit="₹" 
            stroke={theme === 'dark' ? '#9ca3af' : '#4b5563'}
            label={{ value: 'Revenue (₹)', angle: -90, position: 'insideLeft', fill: theme === 'dark' ? '#9ca3af' : '#4b5563' }}
          />
          <ZAxis type="number" dataKey="z" range={[64, 400]} name="Orders" />
          <Tooltip 
             cursor={{ strokeDasharray: '3 3' }}
             content={({ active, payload }) => {
                 if (active && payload && payload.length) {
                     const d = payload[0].payload;
                     return (
                         <div className={`p-2 rounded border shadow-sm ${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-black'}`}>
                             <p className="font-bold mb-1">{d.name}</p>
                             <p>Sold: {d.x} units</p>
                             <p>Revenue: ₹{d.y}</p>
                             <p>Orders: {d.z}</p>
                         </div>
                     );
                 }
                 return null;
             }}
          />
          <Scatter 
            name="Products" 
            data={chartData} 
            fill="#8B4513"
            fillOpacity={0.6}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ProductBubbleChart;
