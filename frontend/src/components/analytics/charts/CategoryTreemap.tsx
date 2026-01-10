import React from 'react';
import { ResponsiveContainer, Treemap, Tooltip } from 'recharts';
import { useCategoryPerformance } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface CategoryTreemapProps {
  dateRange?: { start: string; end: string };
}

const CategoryTreemap: React.FC<CategoryTreemapProps> = ({ dateRange }) => {
  const { theme } = useTheme();
  const params: AnalyticsQueryParams = {
    start_date: dateRange?.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange?.end ? `${dateRange.end}T23:59:59Z` : undefined,
  };

  const { data, isLoading } = useCategoryPerformance(params);

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (!data || data.categories.length === 0) return <div className="h-64 flex items-center justify-center">No data available</div>;

  // Format data for Treemap (needs name and size/value)
  const treeData = data.categories.map(cat => ({
    ...cat,
    name: cat.name,
  }));

  const CustomContent = (props: any) => {
    const { root, depth, x, y, width, height, payload, name } = props;
    
    return (
      <g>
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          style={{
            fill: depth < 2 ? '#8B4513' : 'none', // Coffee brown base
            fillOpacity: (0.3 + (0.7 * ((payload?.size || 0) / (root?.children?.[0]?.size || 1000))) ), 
            stroke: '#fff',
            strokeWidth: 2 / (depth + 1e-10),
            strokeOpacity: 1 / (depth + 1e-10),
          }}
        />
        {width > 50 && height > 30 && (
          <text
            x={x + width / 2}
            y={y + height / 2}
            textAnchor="middle"
            fill="#fff"
            fontSize={12}
            fontWeight="bold"
          >
           {name}
          </text>
        )}
        {width > 50 && height > 50 && (
           <text
            x={x + width / 2}
            y={y + height / 2 + 16}
            textAnchor="middle"
            fill="#fff"
            fontSize={10}
          >
           ₹{Math.round(payload?.size)}
          </text>
        )}
      </g>
    );
  };
  
  // Custom Color Logic based on index

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={treeData}
          dataKey="size"
          aspectRatio={4 / 3}
          stroke="#fff"
          content={<CustomContent />}
        >
          <Tooltip 
             formatter={(value: any) => [`₹${Math.round(value)}`, 'Revenue']}
             contentStyle={{
                 backgroundColor: theme === 'dark' ? '#1f2937' : '#fff',
                 borderColor: theme === 'dark' ? '#374151' : '#e5e7eb',
                 color: theme === 'dark' ? '#fff' : '#000'
             }}
          />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
};

export default CategoryTreemap;
