import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ErrorBar } from 'recharts';
import { useOrderValueDistribution } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface OrderValueBoxPlotProps {
  dateRange?: { start: string; end: string };
  groupBy?: 'day_of_week' | 'payment_method';
}

// Simplified Box Plot: Median Bar with Min-Max Whiskers
const BoxPlotChart: React.FC<OrderValueBoxPlotProps> = ({ dateRange, groupBy = 'day_of_week' }) => {
  const { theme } = useTheme();
  const params: AnalyticsQueryParams = {
    start_date: dateRange?.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange?.end ? `${dateRange.end}T23:59:59Z` : undefined,
    group_by: groupBy
  };

  const { data, isLoading } = useOrderValueDistribution(params);

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (!data || !data.data) return <div className="h-64 flex items-center justify-center">No data available</div>;

  const chartData = data.data.map(d => ({
    name: d.group,
    median: d.stats.median,
    min: d.stats.min,
    max: d.stats.max,
    errorVals: [d.stats.median - d.stats.min, d.stats.max - d.stats.median] 
  }));

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 20, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
          <XAxis dataKey="name" stroke={theme === 'dark' ? '#9ca3af' : '#4b5563'} />
          <YAxis stroke={theme === 'dark' ? '#9ca3af' : '#4b5563'} label={{ value: 'Value (₹)', angle: -90, position: 'insideLeft' }} />
          <Tooltip 
             cursor={{fill: 'transparent'}}
             content={({ active, payload }) => {
                 if (active && payload && payload.length) {
                     const d = payload[0].payload;
                     return (
                         <div className={`p-2 rounded border shadow-sm ${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-black'}`}>
                             <p className="font-bold">{d.name}</p>
                             <p>Max: ₹{d.max}</p>
                             <p>Median: ₹{d.median}</p>
                             <p>Min: ₹{d.min}</p>
                         </div>
                     );
                 }
                 return null;
             }}
          />
          <Bar dataKey="median" fill="#8884d8" barSize={30}>
            {/* ErrorBar for Range (Min to Max) */}
            <ErrorBar dataKey="errorVals" width={4} strokeWidth={2} stroke={theme === 'dark' ? '#fff' : '#000'} direction="y" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default BoxPlotChart;
