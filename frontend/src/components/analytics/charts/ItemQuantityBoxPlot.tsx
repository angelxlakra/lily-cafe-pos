import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ErrorBar } from 'recharts';
import { useItemQuantityDistribution } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface ItemQuantityBoxPlotProps {
  dateRange?: { start: string; end: string };
}

const ItemQuantityBoxPlot: React.FC<ItemQuantityBoxPlotProps> = ({ dateRange }) => {
  const { theme } = useTheme();
  const params: AnalyticsQueryParams = {
    start_date: dateRange?.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange?.end ? `${dateRange.end}T23:59:59Z` : undefined,
  };

  const { data, isLoading } = useItemQuantityDistribution(params);

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (!data || !data.data) return <div className="h-64 flex items-center justify-center">No data available</div>;

  const chartData = data.data.map(d => ({
    name: d.item_name,
    median: d.stats.median,
    min: d.stats.min,
    max: d.stats.max,
    errorVals: [d.stats.median - d.stats.min, d.stats.max - d.stats.median] 
  }));

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 20, right: 20 }} layout="horizontal">
          <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
          <XAxis 
            dataKey="name" 
            stroke={theme === 'dark' ? '#9ca3af' : '#4b5563'} 
            angle={-45} 
            textAnchor="end"
            height={60}
          />
          <YAxis stroke={theme === 'dark' ? '#9ca3af' : '#4b5563'} label={{ value: 'Qty Sold', angle: -90, position: 'insideLeft' }} />
          <Tooltip 
             cursor={{fill: 'transparent'}}
             content={({ active, payload }) => {
                 if (active && payload && payload.length) {
                     const d = payload[0].payload;
                     return (
                         <div className={`p-2 rounded border shadow-sm ${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-black'}`}>
                             <p className="font-bold">{d.name}</p>
                             <p>Max Daily: {d.max}</p>
                             <p>Median Daily: {d.median}</p>
                             <p>Min Daily: {d.min}</p>
                         </div>
                     );
                 }
                 return null;
             }}
          />
          <Bar dataKey="median" fill="#82ca9d" barSize={30}>
            <ErrorBar dataKey="errorVals" width={4} strokeWidth={2} stroke={theme === 'dark' ? '#fff' : '#000'} direction="y" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ItemQuantityBoxPlot;
