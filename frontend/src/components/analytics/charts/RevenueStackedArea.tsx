import React, { useMemo } from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { useRevenueComposition } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface RevenueStackedAreaProps {
  dateRange?: { start: string; end: string };
}

const RevenueStackedArea: React.FC<RevenueStackedAreaProps> = ({ dateRange }) => {
  const { theme } = useTheme();
  const params: AnalyticsQueryParams = {
    start_date: dateRange?.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange?.end ? `${dateRange.end}T23:59:59Z` : undefined,
  };

  const { data, isLoading } = useRevenueComposition(params);

  const { transformedData, categories } = useMemo(() => {
    if (!data || !data.data) return { transformedData: [], categories: [] };

    // Get unique categories
    const cats = Array.from(new Set(data.data.map(d => d.category)));

    // Group by date
    const grouped: Record<string, any> = {};
    data.data.forEach(item => {
        if (!grouped[item.date]) {
            grouped[item.date] = { date: item.date }; // Could format date
            cats.forEach(c => grouped[item.date][c] = 0);
        }
        grouped[item.date][item.category] = item.revenue;
    });

    const result = Object.values(grouped).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    return { transformedData: result, categories: cats };
  }, [data]);

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (transformedData.length === 0) return <div className="h-64 flex items-center justify-center">No data available</div>;

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe', '#00C49F', '#FFBB28', '#FF8042'];

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
          <Legend wrapperStyle={{ paddingTop: '10px' }} />
          {categories.map((cat, index) => (
            <Area
              key={cat}
              type="monotone"
              dataKey={cat}
              stackId="1"
              stroke={COLORS[index % COLORS.length]}
              fill={COLORS[index % COLORS.length]}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RevenueStackedArea;
