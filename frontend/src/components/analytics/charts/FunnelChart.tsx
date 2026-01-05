import React from 'react';
import { ResponsiveContainer, FunnelChart as RechartsFunnelChart, Funnel, Tooltip, LabelList } from 'recharts';
import { useOrderStatsDetailed } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface FunnelChartProps {
  dateRange?: { start: string; end: string };
}

const FunnelChart: React.FC<FunnelChartProps> = ({ dateRange }) => {
  const { theme } = useTheme();
  const params: AnalyticsQueryParams = {
    start_date: dateRange?.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange?.end ? `${dateRange.end}T23:59:59Z` : undefined,
  };

  const { data, isLoading } = useOrderStatsDetailed(params);

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (!data || data.total_orders === 0) return <div className="h-64 flex items-center justify-center">No funnel data</div>;

  const funnelData = [
    {
      value: data.total_orders,
      name: 'Total Orders',
      fill: '#3b82f6',
    },
    {
        value: data.active_orders + data.completed_orders, // Non-canceled basically? Or just active+completed
        name: 'Processed',
        fill: '#f59e0b'
    },
    {
      value: data.completed_orders,
      name: 'Completed (Paid)',
      fill: '#10b981',
    }
  ];

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsFunnelChart>
          <Tooltip 
             contentStyle={{
                 backgroundColor: theme === 'dark' ? '#1f2937' : '#fff',
                 borderColor: theme === 'dark' ? '#374151' : '#e5e7eb',
                 color: theme === 'dark' ? '#fff' : '#000'
             }}
          />
          <Funnel
            dataKey="value"
            data={funnelData}
            isAnimationActive
          >
            <LabelList position="right" fill={theme === 'dark' ? '#fff' : '#000'} stroke="none" dataKey="name" />
             <LabelList position="inside" fill="#fff" stroke="none" dataKey="value" />
          </Funnel>
        </RechartsFunnelChart>
      </ResponsiveContainer>
    </div>
  );
};

export default FunnelChart;
