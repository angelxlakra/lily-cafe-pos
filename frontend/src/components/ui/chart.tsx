// shadcn/ui chart primitives, adapted to the Lily Cafe theme.
//
// Copied in rather than installed (shadcn's model), with its theme classes
// mapped onto this app's own tokens so it does not bring a second design
// system with it. Series colours are declared once in a ChartConfig and
// exposed to Recharts as CSS variables, so `var(--color-<key>)` works in
// fills and strokes and follows the light/dark theme automatically.

import * as React from 'react';
import * as RechartsPrimitive from 'recharts';

import { cn } from '../../utils/cn';

export type ChartConfig = {
  [k in string]: {
    label?: React.ReactNode;
    icon?: React.ComponentType;
    color?: string;
  };
};

type ChartContextProps = { config: ChartConfig };

const ChartContext = React.createContext<ChartContextProps | null>(null);

function useChart() {
  const context = React.useContext(ChartContext);
  if (!context) {
    throw new Error('useChart must be used within a <ChartContainer />');
  }
  return context;
}

function ChartContainer({
  id,
  className,
  children,
  config,
  ...props
}: React.ComponentProps<'div'> & {
  config: ChartConfig;
  children: React.ComponentProps<typeof RechartsPrimitive.ResponsiveContainer>['children'];
}) {
  const uniqueId = React.useId();
  const chartId = `chart-${id || uniqueId.replace(/:/g, '')}`;

  return (
    <ChartContext.Provider value={{ config }}>
      <div
        data-chart={chartId}
        className={cn(
          'flex aspect-video justify-center text-xs',
          "[&_.recharts-cartesian-axis-tick_text]:fill-neutral-text-muted",
          "[&_.recharts-cartesian-grid_line[stroke='#ccc']]:stroke-neutral-border/60",
          '[&_.recharts-curve.recharts-tooltip-cursor]:stroke-neutral-border',
          "[&_.recharts-polar-grid_[stroke='#ccc']]:stroke-neutral-border",
          '[&_.recharts-radial-bar-background-sector]:fill-neutral-border/40',
          '[&_.recharts-rectangle.recharts-tooltip-cursor]:fill-neutral-border/40',
          "[&_.recharts-reference-line_[stroke='#ccc']]:stroke-neutral-border",
          '[&_.recharts-dot[stroke="#fff"]]:stroke-transparent',
          '[&_.recharts-layer]:outline-hidden',
          '[&_.recharts-sector]:outline-hidden',
          '[&_.recharts-sector[stroke="#fff"]]:stroke-transparent',
          '[&_.recharts-surface]:outline-hidden',
          className,
        )}
        {...props}
      >
        <ChartStyle id={chartId} config={config} />
        <RechartsPrimitive.ResponsiveContainer>{children}</RechartsPrimitive.ResponsiveContainer>
      </div>
    </ChartContext.Provider>
  );
}

const ChartStyle = ({ id, config }: { id: string; config: ChartConfig }) => {
  const colorConfig = Object.entries(config).filter(([, c]) => c.color);
  if (!colorConfig.length) return null;

  const css = `[data-chart=${id}] {\n${colorConfig
    .map(([key, item]) => (item.color ? `  --color-${key}: ${item.color};` : null))
    .filter(Boolean)
    .join('\n')}\n}`;

  return <style dangerouslySetInnerHTML={{ __html: css }} />;
};

const ChartTooltip = RechartsPrimitive.Tooltip;

type TooltipPayloadItem = {
  name?: string | number;
  dataKey?: string | number;
  value?: number | string;
  color?: string;
  payload?: Record<string, unknown>;
};

function ChartTooltipContent({
  active,
  payload,
  className,
  indicator = 'dot',
  hideLabel = false,
  label,
  labelFormatter,
  formatter,
  nameKey,
  labelKey,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  className?: string;
  indicator?: 'line' | 'dot' | 'dashed';
  hideLabel?: boolean;
  label?: React.ReactNode;
  labelFormatter?: (label: React.ReactNode, payload: TooltipPayloadItem[]) => React.ReactNode;
  formatter?: (value: number | string, name: string, item: TooltipPayloadItem) => React.ReactNode;
  nameKey?: string;
  labelKey?: string;
}) {
  const { config } = useChart();

  const tooltipLabel = React.useMemo(() => {
    if (hideLabel || !payload?.length) return null;
    const [item] = payload;
    const key = `${labelKey || item?.dataKey || item?.name || 'value'}`;
    const itemConfig = getPayloadConfigFromPayload(config, item, key);
    const value =
      !labelKey && typeof label === 'string'
        ? config[label as keyof typeof config]?.label || label
        : itemConfig?.label;
    if (labelFormatter) {
      return <div className="font-medium">{labelFormatter(value, payload)}</div>;
    }
    if (!value) return null;
    return <div className="font-medium">{value}</div>;
  }, [label, labelFormatter, payload, hideLabel, config, labelKey]);

  if (!active || !payload?.length) return null;

  return (
    <div
      className={cn(
        'grid min-w-[8rem] items-start gap-1.5 rounded-lg border border-neutral-border bg-neutral-background px-2.5 py-1.5 text-xs shadow-xl',
        className,
      )}
    >
      {tooltipLabel}
      <div className="grid gap-1.5">
        {payload.map((item, index) => {
          const key = `${nameKey || item.name || item.dataKey || 'value'}`;
          const itemConfig = getPayloadConfigFromPayload(config, item, key);
          const indicatorColor = item.color || (item.payload?.fill as string | undefined);

          return (
            <div
              key={`${item.dataKey}-${index}`}
              className="flex w-full flex-wrap items-center gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 [&>svg]:text-neutral-text-muted"
            >
              {formatter && item.value !== undefined && item.name ? (
                formatter(item.value, String(item.name), item)
              ) : (
                <>
                  {itemConfig?.icon ? (
                    <itemConfig.icon />
                  ) : (
                    <div
                      className={cn('shrink-0 rounded-[2px] border-(--color-border) bg-(--color-bg)', {
                        'h-2.5 w-2.5': indicator === 'dot',
                        'w-1': indicator === 'line',
                        'w-0 border-[1.5px] border-dashed bg-transparent': indicator === 'dashed',
                      })}
                      style={
                        {
                          '--color-bg': indicatorColor,
                          '--color-border': indicatorColor,
                        } as React.CSSProperties
                      }
                    />
                  )}
                  <div className="flex flex-1 items-center justify-between gap-3 leading-none">
                    <span className="text-neutral-text-muted">{itemConfig?.label || item.name}</span>
                    {item.value !== undefined && (
                      <span className="font-mono font-medium tabular-nums text-neutral-text-dark">
                        {typeof item.value === 'number' ? item.value.toLocaleString('en-IN') : item.value}
                      </span>
                    )}
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const ChartLegend = RechartsPrimitive.Legend;

function ChartLegendContent({
  className,
  payload,
  nameKey,
}: {
  className?: string;
  payload?: Array<{ value?: string; dataKey?: string | number; color?: string }>;
  nameKey?: string;
}) {
  const { config } = useChart();
  if (!payload?.length) return null;

  return (
    <div className={cn('flex flex-wrap items-center justify-center gap-x-4 gap-y-1 pt-3', className)}>
      {payload.map((item) => {
        const key = `${nameKey || item.dataKey || 'value'}`;
        const itemConfig = getPayloadConfigFromPayload(config, item, key);
        return (
          <div key={String(item.value)} className="flex items-center gap-1.5 text-neutral-text-light">
            <div className="h-2 w-2 shrink-0 rounded-[2px]" style={{ backgroundColor: item.color }} />
            {itemConfig?.label ?? item.value}
          </div>
        );
      })}
    </div>
  );
}

function getPayloadConfigFromPayload(config: ChartConfig, payload: unknown, key: string) {
  if (typeof payload !== 'object' || payload === null) return undefined;

  const payloadPayload =
    'payload' in payload && typeof payload.payload === 'object' && payload.payload !== null
      ? (payload.payload as Record<string, unknown>)
      : undefined;

  let configLabelKey: string = key;
  const record = payload as Record<string, unknown>;
  if (key in record && typeof record[key] === 'string') {
    configLabelKey = record[key] as string;
  } else if (payloadPayload && key in payloadPayload && typeof payloadPayload[key] === 'string') {
    configLabelKey = payloadPayload[key] as string;
  }

  return configLabelKey in config ? config[configLabelKey] : config[key];
}

export { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent, ChartStyle };
