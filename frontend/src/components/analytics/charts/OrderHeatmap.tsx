
import { useMemo } from 'react';
import { useChartTheme } from '../../../hooks/useChartTheme';
import { HeatmapPoint } from '../../../api/analytics';
import { formatCurrency } from '../../../utils/formatCurrency';

interface OrderHeatmapProps {
  data: HeatmapPoint[];
  metric?: 'order_count' | 'revenue';
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

export default function OrderHeatmap({ data, metric = 'order_count' }: OrderHeatmapProps) {
  const chart = useChartTheme();
  
  // Find max value for scaling color intensity
  const maxValue = useMemo(() => {
    if (!data.length) return 0;
    return Math.max(...data.map(d => d[metric]));
  }, [data, metric]);

  // Sequential ramp: one hue, mixed toward the chart surface, so the scale
  // reads the same on paper and on espresso. Alpha over a fixed brown made
  // the quiet hours invisible in dark mode.
  const getColor = (value: number) => {
    if (value === 0) return chart.grid;
    const intensity = maxValue > 0 ? value / maxValue : 0;
    const strength = Math.round(12 + intensity * 88);
    return `color-mix(in oklab, ${chart.series[0]} ${strength}%, ${chart.surface})`;
  };

  const getTooltip = (day: string, hour: number, _value: number, revenue: number, count: number) => {
    const formattedRevenue = formatCurrency(revenue);
    return `${day} ${hour}:00\n${count} orders\n${formattedRevenue} revenue`;
  };

  return (
    <div className="w-full overflow-x-auto">
      <div className="min-w-[600px]">
        {/* Header Row (Hours) */}
        <div className="flex">
          <div className="w-12 flex-shrink-0"></div> {/* Spacer for Day labels */}
          <div className="flex-1 grid gap-1" style={{ gridTemplateColumns: 'repeat(24, minmax(0, 1fr))' }}>
            {HOURS.map(h => (
              <div key={h} className="text-xs text-center text-neutral-text-muted" style={{ fontSize: '10px' }}>
                {h % 4 === 0 ? h : ''}
              </div>
            ))}
          </div>
        </div>

        {/* Rows (Days) */}
        <div className="flex flex-col gap-1 mt-1">
          {DAYS.map((day, dayIndex) => (
            <div key={day} className="flex items-center">
              <div className="w-12 text-xs font-medium text-neutral-text-muted">{day}</div>
              <div className="flex-1 grid gap-1" style={{ gridTemplateColumns: 'repeat(24, minmax(0, 1fr))' }}>
                {HOURS.map(hour => {
                    // Find data point
                    // Note: Backend returns 0=Sun, 6=Sat match DAYS array index
                    const point = data.find(d => d.day_of_week === dayIndex && d.hour === hour);
                    const value = point ? point[metric] : 0;
                    const revenue = point ? point.revenue : 0;
                    const count = point ? point.order_count : 0;

                    return (
                        <div
                        key={`${day}-${hour}`}
                        className="aspect-square rounded-sm transition-all hover:ring-2 hover:ring-coffee-brown relative group"
                        style={{ backgroundColor: getColor(value) }}
                        title={getTooltip(day, hour, value, revenue, count)}
                        >
                        {/* Custom Tooltip using group-hover if we wanted fancy HTML tooltip */}
                        </div>
                    );
                })}
              </div>
            </div>
          ))}
        </div>
        
        {/* Legend */}
        <div className="flex items-center justify-end mt-2 gap-2 text-xs text-neutral-text-muted">
            <span>Less</span>
            <div className="flex gap-1">
                <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: chart.grid }}></div>
                <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: `color-mix(in oklab, ${chart.series[0]} 30%, ${chart.surface})` }}></div>
                <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: `color-mix(in oklab, ${chart.series[0]} 60%, ${chart.surface})` }}></div>
                <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: `color-mix(in oklab, ${chart.series[0]} 100%, ${chart.surface})` }}></div>
            </div>
            <span>More</span>
        </div>
      </div>
    </div>
  );
}
