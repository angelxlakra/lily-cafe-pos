import React from 'react';
import { ResponsiveContainer, Sankey, Tooltip } from 'recharts';
import { useOrderFlow } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface OrderSankeyProps {
  dateRange?: { start: string; end: string };
}

const OrderSankey: React.FC<OrderSankeyProps> = ({ dateRange }) => {
  const { theme } = useTheme();
  const params: AnalyticsQueryParams = {
    start_date: dateRange?.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange?.end ? `${dateRange.end}T23:59:59Z` : undefined,
  };

  const { data, isLoading } = useOrderFlow(params);

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (!data || !data.nodes || data.nodes.length === 0 || data.links.length === 0) return <div className="h-64 flex items-center justify-center">No flow data available</div>;

  return (
    <div className="h-80 w-full font-sans text-xs">
      <ResponsiveContainer width="100%" height="100%">
        <Sankey
          data={data}
          node={{
             // @ts-ignore
             stroke: '#777', strokeWidth: 1,
             fill: theme === 'dark' ? '#8884d8' : '#8884d8'
          }}
          link={{ stroke: '#77c878' }}
          margin={{ left: 10, right: 10, top: 10, bottom: 10 }}
        >
          <Tooltip 
             contentStyle={{
                 backgroundColor: theme === 'dark' ? '#1f2937' : '#fff',
                 borderColor: theme === 'dark' ? '#374151' : '#e5e7eb',
                 color: theme === 'dark' ? '#fff' : '#000'
             }}
          />
        </Sankey>
      </ResponsiveContainer>
    </div>
  );
};

export default OrderSankey;
