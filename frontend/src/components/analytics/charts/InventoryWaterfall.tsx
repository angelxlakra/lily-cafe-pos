import React, { useMemo } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, CartesianGrid } from 'recharts';
import { useInventoryWaterfall } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface InventoryWaterfallProps {
  date?: string; 
}

const InventoryWaterfall: React.FC<InventoryWaterfallProps> = ({ date }) => {
  const { theme } = useTheme();
  const params: AnalyticsQueryParams = { date };

  const { data, isLoading } = useInventoryWaterfall(params);

  const chartData = useMemo(() => {
    if (!data || !data.data) return [];
    
    let accumulator = 0;
    return data.data.map(item => {
        if (item.is_total) {
            accumulator = item.value;
            return {
                ...item,
                range: [0, item.value],
                fill: item.color || '#3b82f6'
            };
        }
        
        const start = accumulator;
        const end = accumulator + item.value;
        accumulator = end;
        
        return {
            ...item,
            range: [start, end],
            fill: item.color || (item.value >= 0 ? '#10b981' : '#ef4444')
        };
    });
  }, [data]);

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (chartData.length === 0) return <div className="h-64 flex items-center justify-center">No inventory flow data available</div>;

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
          <XAxis dataKey="name" stroke={theme === 'dark' ? '#9ca3af' : '#4b5563'} fontSize={12} />
          <YAxis stroke={theme === 'dark' ? '#9ca3af' : '#4b5563'} />
          <Tooltip 
             cursor={{fill: 'transparent'}}
             formatter={(_value: any, _name: any, props: any) => [`₹${Math.round(props.payload.value)}`, 'Value']}
             contentStyle={{
                 backgroundColor: theme === 'dark' ? '#1f2937' : '#fff',
                 borderColor: theme === 'dark' ? '#374151' : '#e5e7eb',
                 color: theme === 'dark' ? '#fff' : '#000'
             }}
          />
          <Bar dataKey="range" barSize={40}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default InventoryWaterfall;
