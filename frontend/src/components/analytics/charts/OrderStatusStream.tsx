import React, { useMemo } from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { useOrderStatusFlow } from '../../../hooks/useAnalytics';
import { useChartTheme } from '../../../hooks/useChartTheme';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface OrderStatusStreamProps {
  dateRange?: { start: string; end: string };
}

const OrderStatusStream: React.FC<OrderStatusStreamProps> = ({ dateRange }) => {
  const chart = useChartTheme();
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
             stroke={chart.muted}
             tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
          />
          <YAxis stroke={chart.muted} />
          <Tooltip 
             contentStyle={{
                 backgroundColor: chart.surface,
                 borderColor: chart.grid,
                 color: chart.ink
             }}
          />
          <Legend />
          <Area type="monotone" dataKey="paid" stackId="1" stroke="var(--color-success)" fill="var(--color-success)" name="Paid" />
          <Area type="monotone" dataKey="active" stackId="1" stroke="var(--color-warning)" fill="var(--color-warning)" name="Active" />
          <Area type="monotone" dataKey="canceled" stackId="1" stroke="var(--color-error)" fill="var(--color-error)" name="Canceled" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default OrderStatusStream;
