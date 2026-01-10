import React from 'react';
import { ResponsiveContainer, Treemap, Tooltip } from 'recharts';
import { useInventoryValuation } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';

const InventoryTreemap: React.FC = () => {
  const { theme } = useTheme();
  // Inventory valuation is usually current snapshot, so no date range params needed heavily
  const { data, isLoading } = useInventoryValuation();

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (!data || !data.items || data.items.length === 0) return <div className="h-64 flex items-center justify-center">No inventory data available</div>;

  // Format data
  const treeData = data.items
    .filter(item => item.value_rupees > 0) // Only show items with value
    .map(item => ({
      name: item.name,
      size: item.value_rupees,
      category: item.category
    }))
    .sort((a, b) => b.size - a.size); // Sort desc

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
            fill: depth < 2 ? (payload.category === 'Coffee' ? '#8B4513' : '#10b981') : '#3b82f6',
            fillOpacity: (0.3 + (0.7 * (payload.size / (root.children?.[0]?.size || 100))) ),
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
           ₹{Math.round(payload.size)}
          </text>
        )}
      </g>
    );
  };

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
             formatter={(value: any) => [`₹${Math.round(value)}`, 'Value']}
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

export default InventoryTreemap;
