import React, { useMemo } from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { useOrderStatusFlow } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface OrderStatusStreamProps {
  dateRange?: { start: string; end: string };
}

const OrderStatusStream: React.FC<OrderStatusStreamProps> = ({ dateRange }) => {
  const { theme } = useTheme();
  const params: AnalyticsQueryParams = {
    start_date: dateRange?.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange?.end ? `${dateRange.end}T23:59:59Z` : undefined,
  };

  const { data, isLoading } = useOrderStatusFlow(params);

  const { transformedData } = useMemo(() => {
    if (!data || !data.data) return { transformedData: [] };

    const grouped: Record<string, any> = {};
    data.data.forEach(item => {
        if (!grouped[item.date]) {
            grouped[item.date] = { date: item.date, active: 0, paid: 0, canceled: 0 };
        }
        grouped[item.date][item.status] = item.count;
    });

    const result = Object.values(grouped).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    return { transformedData: result };
  }, [data]);

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (transformedData.length === 0) return <div className="h-64 flex items-center justify-center">No status data available</div>;

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={transformedData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
          <XAxis 
             dataKey="date" 
             stroke={theme === 'dark' ? '#9ca3af' : '#4b5563'}
             tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
          />
          <YAxis stroke={theme === 'dark' ? '#9ca3af' : '#4b5563'} />
          <Tooltip 
             contentStyle={{
                 backgroundColor: theme === 'dark' ? '#1f2937' : '#fff',
                 borderColor: theme === 'dark' ? '#374151' : '#e5e7eb',
                 color: theme === 'dark' ? '#fff' : '#000'
             }}
          />
          <Legend />
          <Area type="monotone" dataKey="paid" stackId="1" stroke="#10b981" fill="#10b981" name="Paid" />
          <Area type="monotone" dataKey="active" stackId="1" stroke="#f59e0b" fill="#f59e0b" name="Active" />
          <Area type="monotone" dataKey="canceled" stackId="1" stroke="#ef4444" fill="#ef4444" name="Canceled" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default OrderStatusStream;
