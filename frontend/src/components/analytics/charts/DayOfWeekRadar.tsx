import React, { useMemo } from 'react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Tooltip, Legend } from 'recharts';
import { useDayOfWeekStats } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface DayOfWeekRadarProps {
  dateRange?: { start: string; end: string };
}

const DayOfWeekRadar: React.FC<DayOfWeekRadarProps> = ({ dateRange }) => {
  const { theme } = useTheme();
  const params: AnalyticsQueryParams = {
    start_date: dateRange?.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange?.end ? `${dateRange.end}T23:59:59Z` : undefined,
  };

  const { data, isLoading } = useDayOfWeekStats(params);

  const normalizedData = useMemo(() => {
    if (!data || !data.data) return [];
    
    const maxRev = Math.max(...data.data.map(d => d.revenue_rupees), 1);
    const maxOrders = Math.max(...data.data.map(d => d.order_count), 1);

    // Sort by day index (0=Monday in backend, usually)
    // Backend DayOfWeekStat: day_index 0=Monday, 6=Sunday.
    const sortedDetails = [...data.data].sort((a, b) => a.day_index - b.day_index);

    return sortedDetails.map(d => ({
        day: d.day.substring(0, 3),
        revenue: d.revenue_rupees,
        orders: d.order_count,
        normalizedRevenue: (d.revenue_rupees / maxRev) * 100,
        normalizedOrders: (d.order_count / maxOrders) * 100,
        fullDay: d.day
    }));
  }, [data]);

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (normalizedData.length === 0) return <div className="h-64 flex items-center justify-center">No data available</div>;

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={normalizedData}>
          <PolarGrid stroke={theme === 'dark' ? '#4b5563' : '#e5e7eb'} />
          <PolarAngleAxis 
            dataKey="day" 
            tick={{ fill: theme === 'dark' ? '#9ca3af' : '#4b5563', fontSize: 12 }} 
          />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
          
          <Radar
            name="Revenue"
            dataKey="normalizedRevenue"
            stroke="#8884d8"
            fill="#8884d8"
            fillOpacity={0.4}
          />
          <Radar
            name="Orders"
            dataKey="normalizedOrders"
            stroke="#82ca9d"
            fill="#82ca9d"
            fillOpacity={0.4}
          />
          <Legend />
          <Tooltip 
             formatter={(value: any, name: any, props: any) => {
                 if (name === 'Revenue') return [`₹${props.payload.revenue}`, name];
                 if (name === 'Orders') return [props.payload.orders, name];
                 return [value, name];
             }}
             contentStyle={{
                 backgroundColor: theme === 'dark' ? '#1f2937' : '#fff',
                 borderColor: theme === 'dark' ? '#374151' : '#e5e7eb',
                 color: theme === 'dark' ? '#fff' : '#000'
             }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default DayOfWeekRadar;
