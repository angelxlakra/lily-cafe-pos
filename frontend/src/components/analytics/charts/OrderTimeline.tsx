import React, { useMemo } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { useOrderTimeline } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface OrderTimelineProps {
  date?: string; 
}

const OrderTimeline: React.FC<OrderTimelineProps> = ({ date }) => {
  const { theme } = useTheme();
  const params: AnalyticsQueryParams = { date };

  const { data, isLoading } = useOrderTimeline(params);

  const chartData = useMemo(() => {
    if (!data || !data.data) return [];
    
    // Sort by creation time
    return data.data
      .filter(d => d.paid_at) // Only show completed ones for Gantt ranges? Or render active till now?
      .map(d => ({
        name: `#${d.order_number} (T${d.table_number})`,
        range: [new Date(d.created_at).getTime(), d.paid_at ? new Date(d.paid_at).getTime() : new Date().getTime()],
        amount: d.amount,
        duration: d.duration_minutes
      }))
      .sort((a, b) => a.range[0] - b.range[0]);
  }, [data]);

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (chartData.length === 0) return <div className="h-64 flex items-center justify-center">No timeline data available</div>;

  const minTime = Math.min(...chartData.map(d => d.range[0]));
  const maxTime = Math.max(...chartData.map(d => d.range[1]));

  return (
    <div className="h-96 w-full overflow-auto"> {/* Make taller and scrollable if many orders? */}
      <ResponsiveContainer width="100%" height={Math.max(400, chartData.length * 30)}>
        <BarChart 
            data={chartData} 
            layout="vertical" 
            margin={{ top: 20, right: 30, left: 100, bottom: 5 }}
            barCategoryGap={2}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} opacity={0.2} />
          <XAxis 
            type="number" 
            domain={[minTime, maxTime]} 
            scale="time" 
            stroke={theme === 'dark' ? '#9ca3af' : '#4b5563'}
            tickFormatter={(unixTime) => new Date(unixTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          />
          <YAxis 
            type="category" 
            dataKey="name" 
            stroke={theme === 'dark' ? '#9ca3af' : '#4b5563'} 
            width={100}
            style={{ fontSize: 10 }}
          />
          <Tooltip 
             cursor={{fill: 'transparent'}}
             content={({ active, payload }) => {
                 if (active && payload && payload.length) {
                     const d = payload[0].payload;
                     const start = new Date(d.range[0]).toLocaleTimeString();
                     const end = new Date(d.range[1]).toLocaleTimeString();
                     return (
                         <div className={`p-2 rounded border shadow-sm ${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-black'}`}>
                             <p className="font-bold">{d.name}</p>
                             <p>{start} - {end}</p>
                             <p>Duration: {d.duration} mins</p>
                             <p>Amount: ₹{d.amount}</p>
                         </div>
                     );
                 }
                 return null;
             }}
          />
          <Bar dataKey="range" fill="#3b82f6" radius={[4, 4, 4, 4]} barSize={20} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default OrderTimeline;
