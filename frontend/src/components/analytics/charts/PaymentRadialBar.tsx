import React from 'react';
import { ResponsiveContainer, RadialBarChart, RadialBar, Legend, Tooltip } from 'recharts';
import { usePaymentTrends } from '../../../hooks/useAnalytics';
import { useTheme } from '../../../contexts/ThemeContext';
import { AnalyticsQueryParams } from '../../../api/analytics';

interface PaymentRadialBarProps {
  dateRange?: { start: string; end: string };
}

const PaymentRadialBar: React.FC<PaymentRadialBarProps> = ({ dateRange }) => {
  const { theme } = useTheme();
  const params: AnalyticsQueryParams = {
    start_date: dateRange?.start ? `${dateRange.start}T00:00:00Z` : undefined,
    end_date: dateRange?.end ? `${dateRange.end}T23:59:59Z` : undefined,
  };

  const { data, isLoading } = usePaymentTrends(params);

  if (isLoading) return <div className="h-64 flex items-center justify-center">Loading...</div>;
  if (!data || !data.payment_methods) return <div className="h-64 flex items-center justify-center">No data available</div>;

  const COLORS: Record<string, string> = {
      'cash': '#10b981',
      'upi': '#3b82f6',
      'card': '#8b5cf6',
      'other': '#9ca3af'
  };

  const chartData = Object.entries(data.payment_methods).map(([method, stat]) => ({
    name: method.toUpperCase(),
    value: stat.transaction_count, // Radial bar usually size by count
    amount: stat.total_amount_rupees,
    fill: COLORS[method.toLowerCase()] || COLORS['other']
  })).sort((a, b) => b.value - a.value); // Sort desc for radial nesting

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart 
            innerRadius="20%" 
            outerRadius="90%" 
            barSize={20} 
            data={chartData}
            startAngle={180} 
            endAngle={-180}
        >
          <RadialBar
            label={{ position: 'insideStart', fill: '#fff' }}
            background
            dataKey="value"
          />
          <Legend 
            iconSize={10} 
            layout="vertical" 
            verticalAlign="middle" 
            align="right"
            wrapperStyle={{ color: theme === 'dark' ? '#fff' : '#000' }}
          />
          <Tooltip 
             formatter={(value: any, name: any, props: any) => [
                 `${value} txns (₹${props.payload.amount})`, 
                 name
             ]}
             contentStyle={{
                 backgroundColor: theme === 'dark' ? '#1f2937' : '#fff',
                 borderColor: theme === 'dark' ? '#374151' : '#e5e7eb',
                 color: theme === 'dark' ? '#fff' : '#000' // Fixed text color
             }}
          />
        </RadialBarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PaymentRadialBar;
