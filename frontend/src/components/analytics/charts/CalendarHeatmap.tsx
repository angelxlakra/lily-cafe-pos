
import { useMemo } from 'react';
import { useTheme } from '../../../contexts/ThemeContext';
import { CalendarHeatmapPoint } from '../../../api/analytics';
import { formatCurrency } from '../../../utils/formatCurrency';

interface CalendarHeatmapProps {
  data: CalendarHeatmapPoint[];
  metric?: 'count' | 'value';
  year?: number; // Optional, defaults to current year implied by data range
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export default function CalendarHeatmap({ data, metric = 'value' }: CalendarHeatmapProps) {
  const { theme } = useTheme();

  // Process data into a map for O(1) lookup
  const dataMap = useMemo(() => {
    const map = new Map<string, CalendarHeatmapPoint>();
    data.forEach(d => map.set(d.date, d));
    return map;
  }, [data]);

  // Determine date range to display
  // We'll show the last 52 weeks (approx 1 year) ending today, to be safe.
  const weeks = useMemo(() => {
    const today = new Date();
    const endDate = new Date(today);
    // Align to end of week (Saturday) for clean grid if standard US, or just end today
    // Let's end today.
    
    const weeksList = [];
    // Go back 52 weeks
    for (let w = 0; w < 52; w++) {
      const weekStart = new Date(endDate);
      weekStart.setDate(endDate.getDate() - (w * 7) - endDate.getDay()); // Start of this week (Sunday)
      
      const days = [];
      for (let d = 0; d < 7; d++) {
        const currentDate = new Date(weekStart);
        currentDate.setDate(weekStart.getDate() + d);
        
        // Format YYYY-MM-DD
        const dateStr = currentDate.toISOString().split('T')[0];
        const point = dataMap.get(dateStr);
        
        days.push({
            date: currentDate,
            dateStr,
            value: point ? point[metric] : 0,
            revenue: point ? point.value : 0,
            count: point ? point.count : 0
        });
      }
      weeksList.unshift(days); // Add to front so earliest week is first
    }
    return weeksList;
  }, [dataMap, metric]);

  // Find max value for scaling
  const maxValue = useMemo(() => {
    if (!data.length) return 0;
    return Math.max(...data.map(d => d[metric]));
  }, [data, metric]);

  // Get color based on intensity
  const getColor = (value: number) => {
    if (value === 0) return theme === 'dark' ? '#374151' : '#f3f4f6'; // Base color for 0
    
    // Normalize value 0-1
    const intensity = maxValue > 0 ? value / maxValue : 0;
    
    // Base green color: #10B981 (16, 185, 129) - like GitHub
    // Or stick to brand Coffee Brown: #5C3D2E
    // Let's use Coffee Brown for consistency
    const alpha = 0.15 + (intensity * 0.85);
    
    // Coffee Brown: 92, 61, 46
    return `rgba(92, 61, 46, ${alpha})`;
  };

  return (
    <div className="w-full overflow-x-auto">
      <div className="min-w-[800px] flex flex-col gap-2">
        {/* Months Label Row (Approximate) */}
        <div className="flex text-xs text-gray-400 pl-8">
            {/* Simple distribution of month labels - not perfect alignment but good enough for MVP */}
            {weeks.filter((_, i) => i % 4 === 0).map((week, i) => (
               <div key={i} style={{ width: '56px' }}>{MONTHS[week[0].date.getMonth()]}</div> 
            ))}
        </div>

        <div className="flex gap-1">
          {/* Day Labels */}
          <div className="flex flex-col gap-1 pr-2 pt-0.5">
            {DAYS.map((day, i) => (
              <div key={day} className="text-xs text-gray-500 h-3 flex items-center" style={{ display: i % 2 !== 0 ? 'block' : 'none' }}>
                {day}
              </div>
            ))}
          </div>

          {/* Grid */}
          <div className="flex gap-1">
            {weeks.map((week, weekIndex) => (
              <div key={weekIndex} className="flex flex-col gap-1">
                {week.map((day) => (
                  <div
                    key={day.dateStr}
                    className="w-3 h-3 rounded-[1px] transition-all hover:ring-2 hover:ring-coffee-brown relative group"
                    style={{ backgroundColor: getColor(day.value) }}
                    title={`${day.dateStr}\n${day.count} orders\n${formatCurrency(day.revenue)}`}
                  >
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
        
        {/* Legend */}
        <div className="flex items-center justify-end mt-2 gap-2 text-xs text-gray-500">
            <span>Less</span>
            <div className="flex gap-1">
                <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: theme === 'dark' ? '#374151' : '#f3f4f6' }}></div>
                <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: 'rgba(92, 61, 46, 0.4)' }}></div>
                <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: 'rgba(92, 61, 46, 0.7)' }}></div>
                <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: 'rgba(92, 61, 46, 1.0)' }}></div>
            </div>
            <span>More</span>
        </div>
      </div>
    </div>
  );
}
