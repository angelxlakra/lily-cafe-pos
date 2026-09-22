import { useMemo } from 'react';
import { useTheme } from '../contexts/ThemeContext';

/**
 * Chart colours read from the design tokens.
 *
 * Recharts needs literal colour strings, so we resolve the CSS variables
 * once per theme instead of branching on `theme === 'dark'` in every chart.
 * Add a colour here, not in a component.
 */
export interface ChartTheme {
  /** Titles and values. */
  ink: string;
  /** Axis labels, legends, secondary text. */
  muted: string;
  /** Grid lines and axis lines. */
  grid: string;
  /** Tooltip and chart surface. */
  surface: string;
  border: string;
  /** Series colours in fixed order — assign by entity, never by rank. */
  series: string[];
}

const readVar = (name: string, fallback: string) => {
  if (typeof window === 'undefined') return fallback;
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
};

export function useChartTheme(): ChartTheme {
  const { theme } = useTheme();

  return useMemo(() => ({
    ink: readVar('--color-neutral-text-dark', '#2C2420'),
    muted: readVar('--color-neutral-text-muted', '#736459'),
    grid: readVar('--color-neutral-border', '#D4C4B0'),
    surface: readVar('--color-off-white', '#FAF8F5'),
    border: readVar('--color-neutral-border', '#D4C4B0'),
    series: [1, 2, 3, 4, 5, 6].map(step => readVar(`--color-chart-${step}`, '#8A4B23')),
  }), [theme]);
}
