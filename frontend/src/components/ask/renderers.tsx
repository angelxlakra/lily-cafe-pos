// One renderer per report family. Each takes exactly the data shape the
// backend returns for that report and draws it; nothing here computes a
// figure, it only lays out what it was given.

import React from 'react';
import { Bar, BarChart, CartesianGrid, Cell, XAxis, YAxis } from 'recharts';

import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '../ui/chart';
import { dayLabel, humanize, inr, isPercentKey, isRupeeKey, num, pct, shortDay } from './format';
import { Empty, Section, ShareList, SplitBar, Stat } from './primitives';

type Data = Record<string, any>;

// ----------------------------------------------------------------------
// Sales
// ----------------------------------------------------------------------

export function SalesSummary({ data }: { data: Data }) {
  const byMethod: Record<string, number> = data.revenue_by_payment_method ?? {};
  const segments = Object.entries(byMethod)
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1])
    .map(([key, value]) => ({ key, label: methodLabel(key), value, display: inr(value) }));

  return (
    <div className="space-y-4">
      <Stat label="Revenue" value={inr(data.total_revenue_rupees)} size="lg" />
      <div className="grid grid-cols-2 gap-4">
        <Stat label="Paid orders" value={num(data.total_orders)} />
        <Stat label="Avg order" value={inr(data.average_order_value_rupees)} />
      </div>
      {segments.length > 0 && (
        <Section title="By payment method">
          <SplitBar segments={segments} />
        </Section>
      )}
    </div>
  );
}

function methodLabel(key: string) {
  return { upi: 'UPI', cash: 'Cash', card: 'Card' }[key] ?? humanize(key);
}

// ----------------------------------------------------------------------
// Ranked items and categories
// ----------------------------------------------------------------------

export function TopItems({ data }: { data: Data }) {
  const items: Array<{ name: string; quantity_sold: number; revenue_rupees: number }> = data.top_products ?? [];
  if (!items.length) return <Empty>No items were sold in this period.</Empty>;
  return (
    <ShareList
      rows={items.map((it) => ({
        key: it.name,
        label: it.name,
        value: it.quantity_sold,
        display: `${num(it.quantity_sold)} sold`,
        sub: inr(it.revenue_rupees),
      }))}
    />
  );
}

export function CategoryPerformance({ data }: { data: Data }) {
  const cats: Array<Data> = data.categories ?? [];
  if (!cats.length) return <Empty>No sales in this period.</Empty>;
  return (
    <ShareList
      rows={cats.map((c) => ({
        key: c.name,
        label: c.name,
        value: c.revenue_rupees,
        display: inr(c.revenue_rupees),
        sub: `${pct(c.revenue_percentage)} of revenue · ${num(c.order_count)} orders · top: ${c.top_item ?? '—'}`,
      }))}
    />
  );
}

// ----------------------------------------------------------------------
// Revenue by day
// ----------------------------------------------------------------------

const dailyConfig = {
  revenue_rupees: { label: 'Revenue', color: 'var(--color-coffee-brown)' },
} satisfies ChartConfig;

export function BestDays({ data }: { data: Data }) {
  const days: Array<{ date: string; revenue_rupees: number; orders: number }> = [...(data.days ?? [])].sort(
    (a, b) => a.date.localeCompare(b.date),
  );
  if (!days.length) return <Empty>No sales in this period.</Empty>;
  const best = data.best_day?.date;
  const worst = data.worst_day?.date;
  const dense = days.length > 14;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Stat label="Best day" value={inr(data.best_day?.revenue_rupees)} hint={best && dayLabel(best)} tone="up" />
        <Stat label="Lowest day" value={inr(data.worst_day?.revenue_rupees)} hint={worst && dayLabel(worst)} tone="down" />
      </div>
      <ChartContainer config={dailyConfig} className="h-44 w-full aspect-auto">
        <BarChart data={days} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <CartesianGrid vertical={false} strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tickLine={false}
            axisLine={false}
            tickFormatter={shortDay}
            interval={dense ? Math.ceil(days.length / 6) - 1 : 0}
            tickMargin={6}
          />
          <YAxis tickLine={false} axisLine={false} tickFormatter={(v) => compact(v)} width={56} />
          <ChartTooltip
            cursor={false}
            content={
              <ChartTooltipContent
                labelFormatter={(_, payload) => dayLabel(String(payload?.[0]?.payload?.date ?? ''))}
                formatter={(value, name, item) => (
                  <div className="flex w-full justify-between gap-4">
                    <span className="text-neutral-text-muted">{name === 'revenue_rupees' ? 'Revenue' : name}</span>
                    <span className="font-medium tabular-nums">
                      {inr(Number(value))} · {num(item.payload?.orders as number)} orders
                    </span>
                  </div>
                )}
              />
            }
          />
          <Bar dataKey="revenue_rupees" radius={[3, 3, 0, 0]}>
            {days.map((d) => (
              <Cell
                key={d.date}
                fill={
                  d.date === best
                    ? 'var(--color-lily-green)'
                    : d.date === worst
                      ? 'var(--color-warning)'
                      : 'var(--color-coffee-brown)'
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ChartContainer>
      <div className="grid grid-cols-2 gap-4">
        <Stat label="Average per day" value={inr(data.average_daily_revenue_rupees)} size="sm" />
        <Stat label="Trading days" value={num(data.trading_days)} size="sm" />
      </div>
    </div>
  );
}

function compact(v: number) {
  if (v >= 100000) return `${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `${Math.round(v / 1000)}k`;
  return String(v);
}

// ----------------------------------------------------------------------
// Peak hours — the report returns busiest and slowest hours only, not a
// full day, so a bar chart would mislead. Two short lists instead.
// ----------------------------------------------------------------------

export function PeakHours({ data }: { data: Data }) {
  const peak: Array<Data> = data.peak_hours ?? [];
  const slow: Array<Data> = data.slowest_hours ?? [];
  if (!peak.length) return <Empty>No orders in this period.</Empty>;
  const max = Math.max(1, ...peak.map((h) => h.order_count));
  return (
    <div className="space-y-4">
      <Section title="Busiest hours">
        <ShareList
          max={max}
          rows={peak.map((h) => ({
            key: String(h.hour),
            label: h.hour_label,
            value: h.order_count,
            display: `${num(h.order_count)} orders`,
            sub: `${inr(h.revenue_rupees)} · mostly ${h.top_category ?? '—'}`,
          }))}
        />
      </Section>
      {slow.length > 0 && (
        <Section title="Quietest hours">
          <ShareList
            max={max}
            rows={slow.map((h) => ({
              key: String(h.hour),
              label: h.hour_label,
              value: h.order_count,
              display: `${num(h.order_count)} orders`,
            }))}
          />
        </Section>
      )}
    </div>
  );
}

// ----------------------------------------------------------------------
// Two- and three-way splits
// ----------------------------------------------------------------------

export function PaymentMethods({ data }: { data: Data }) {
  const methods: Record<string, Data> = data.payment_methods ?? {};
  const segments = Object.entries(methods)
    .filter(([, m]) => (m.total_amount_rupees ?? 0) > 0)
    .sort((a, b) => b[1].total_amount_rupees - a[1].total_amount_rupees)
    .map(([key, m]) => ({
      key,
      label: methodLabel(key),
      value: m.total_amount_rupees,
      display: inr(m.total_amount_rupees),
      sub: `${pct(m.percentage_revenue)} · ${num(m.transaction_count)} payments · avg ${inr(m.avg_transaction_rupees)}`,
    }));
  if (!segments.length) return <Empty>No payments in this period.</Empty>;
  return (
    <div className="space-y-4">
      <Stat label="Total collected" value={inr(data.total_revenue_rupees)} size="lg" />
      <SplitBar segments={segments} />
    </div>
  );
}

function pairSplit(data: Data, a: [string, string], b: [string, string]) {
  const [aKey, aLabel] = a;
  const [bKey, bLabel] = b;
  const left: Data = data[aKey] ?? {};
  const right: Data = data[bKey] ?? {};
  const countKey = 'order_count' in left ? 'order_count' : 'quantity_sold';
  const countLabel = countKey === 'order_count' ? 'orders' : 'sold';
  const avgKey = 'avg_order_value_rupees' in left ? 'avg_order_value_rupees' : 'avg_price_rupees';
  const segments = [
    { key: aKey, label: aLabel, side: left },
    { key: bKey, label: bLabel, side: right },
  ].map(({ key, label, side }) => ({
    key,
    label,
    value: side.revenue_rupees ?? 0,
    display: inr(side.revenue_rupees),
    sub: `${pct(side.revenue_percentage)} · ${num(side[countKey])} ${countLabel} · avg ${inr(side[avgKey])}`,
  }));
  const total = segments.reduce((s, x) => s + x.value, 0);
  if (total === 0) return <Empty>No sales in this period.</Empty>;
  return <SplitBar segments={segments} />;
}

export const ParcelVsDineIn = ({ data }: { data: Data }) => pairSplit(data, ['dine_in', 'Dine-in'], ['parcel', 'Parcel']);
export const VegVsNonVeg = ({ data }: { data: Data }) => pairSplit(data, ['vegetarian', 'Veg'], ['non_vegetarian', 'Non-veg']);
export const BeverageVsFood = ({ data }: { data: Data }) => pairSplit(data, ['food', 'Food'], ['beverages', 'Beverages']);

// ----------------------------------------------------------------------
// Comparison
// ----------------------------------------------------------------------

export function ComparePeriods({ data }: { data: Data }) {
  const cur: Data = data.current ?? {};
  const prev: Data = data.previous ?? {};
  const change: Data = data.change ?? {};
  const rows: Array<[string, string, string, string, (v: number) => string]> = [
    ['Revenue', 'revenue_rupees', 'revenue_change_rupees', 'revenue_change_percentage', (v) => inr(v)],
    ['Orders', 'orders', 'orders_change', 'orders_change_percentage', (v) => num(v)],
    ['Avg order', 'avg_order_value_rupees', 'aov_change_rupees', 'aov_change_percentage', (v) => inr(v)],
  ];
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-[1fr_auto_auto] gap-x-4 gap-y-2 text-sm items-baseline">
        <div />
        <div className="text-xs uppercase tracking-wide text-neutral-text-muted text-right">{prettyPeriod(cur.period) ?? 'Now'}</div>
        <div className="text-xs uppercase tracking-wide text-neutral-text-muted text-right">{prettyPeriod(prev.period) ?? 'Before'}</div>
        {rows.map(([label, key, deltaKey, pctKey, fmt]) => {
          const delta = change[deltaKey] as number | undefined;
          const tone = delta === undefined || delta === 0 ? 'muted' : delta > 0 ? 'up' : 'down';
          return (
            <React.Fragment key={key}>
              <div>
                <div className="text-neutral-text-body">{label}</div>
                <div
                  className={
                    tone === 'up' ? 'text-xs text-success' : tone === 'down' ? 'text-xs text-error' : 'text-xs text-neutral-text-muted'
                  }
                >
                  {delta === undefined ? '' : `${delta > 0 ? '▲' : delta < 0 ? '▼' : '•'} ${fmt(Math.abs(delta))} (${pct(Math.abs(change[pctKey] ?? 0), 1)})`}
                </div>
              </div>
              <div className="text-right font-semibold tabular-nums text-neutral-text-dark">{fmt(cur[key] ?? 0)}</div>
              <div className="text-right tabular-nums text-neutral-text-light">{fmt(prev[key] ?? 0)}</div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}

/** "Week of 2026-09-14" → "Week of 14 Sep": the tool's labels carry ISO dates. */
function prettyPeriod(label: unknown): string | undefined {
  if (typeof label !== 'string') return undefined;
  return label.replace(/\d{4}-\d{2}-\d{2}/g, (iso) => shortDay(iso));
}

// ----------------------------------------------------------------------
// One dish
// ----------------------------------------------------------------------

export function DishDetails({ data }: { data: Data }) {
  if (data.error) return <Empty>{String(data.error)}</Empty>;
  const perf: Data = data.performance ?? {};
  return (
    <div className="space-y-4">
      <div>
        <div className="text-lg font-semibold text-neutral-text-dark">{data.item_name}</div>
        <div className="text-xs text-neutral-text-light">
          {data.category} · {inr(data.current_price_rupees)}
          {data.is_vegetarian === false ? ' · non-veg' : ''}
          {data.is_available === false ? ' · off the menu' : ''}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Stat label="Sold" value={num(perf.quantity_sold)} size="lg" />
        <Stat label="Revenue" value={inr(perf.revenue_rupees)} size="lg" />
        <Stat label="Orders with it" value={num(perf.order_count)} size="sm" />
        <Stat label="Per order" value={num(perf.avg_quantity_per_order)} size="sm" />
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// Stock
// ----------------------------------------------------------------------

export function InventoryStatus({ data }: { data: Data }) {
  const low: Array<Data> = data.low_stock_items ?? [];
  const items: Array<Data> = data.items ?? [];
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Stat label="Below threshold" value={num(data.low_stock_count)} size="lg" tone={data.low_stock_count > 0 ? 'down' : undefined} />
        <Stat label="Stock value" value={inr(data.total_inventory_value_rupees)} size="lg" />
      </div>
      {low.length > 0 && (
        <Section title="Needs reordering">
          <ul className="divide-y divide-neutral-border/60 rounded-lg border border-neutral-border">
            {low.map((it) => (
              <li key={it.name} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                <div className="min-w-0">
                  <div className="truncate text-neutral-text-dark">{it.name}</div>
                  <div className="text-xs text-neutral-text-muted">{it.category}</div>
                </div>
                <div className="text-right shrink-0">
                  <div className="font-medium tabular-nums text-error">
                    {num(it.current_quantity)} {it.unit}
                  </div>
                  <div className="text-xs text-neutral-text-muted">min {num(it.min_threshold)}</div>
                </div>
              </li>
            ))}
          </ul>
        </Section>
      )}
      {items.length > 0 && (
        <Section title="All stock">
          <ul className="divide-y divide-neutral-border/60 text-sm">
            {items.map((it) => (
              <li key={it.name} className="flex items-center justify-between gap-3 py-1.5">
                <span className="truncate text-neutral-text-body">{it.name}</span>
                <span className="shrink-0 tabular-nums text-neutral-text-light">
                  {num(it.current_quantity)} · {inr(it.value_rupees)}
                </span>
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

// ----------------------------------------------------------------------
// Cash counter
// ----------------------------------------------------------------------

export function CashCounter({ data }: { data: Data }) {
  if (data.error) return <Empty>{String(data.error)}</Empty>;
  const variance = data.variance_rupees as number | null;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Stat label="Opening" value={inr(data.opening_balance_rupees)} />
        <Stat label="Cash taken" value={inr(data.cash_received_today_rupees)} />
        <Stat label="Expected close" value={inr(data.expected_closing_rupees)} />
        <Stat label="Actual close" value={inr(data.closing_balance_rupees)} />
      </div>
      <Stat
        label="Variance"
        value={variance === null || variance === undefined ? 'None' : `${variance > 0 ? '+' : ''}${inr(variance, true)}`}
        size="lg"
        tone={!variance ? 'muted' : variance > 0 ? 'up' : 'down'}
        hint={
          <>
            {data.is_verified ? `Verified by ${data.verified_by}` : 'Not yet verified'}
            {data.opened_by ? ` · opened by ${data.opened_by}` : ''}
            {data.closed_by ? ` · closed by ${data.closed_by}` : ''}
          </>
        }
      />
    </div>
  );
}

// ----------------------------------------------------------------------
// Generic: any report without a bespoke layout
// ----------------------------------------------------------------------

export function KeyValues({ data }: { data: Data }) {
  const scalars: Array<[string, unknown]> = [];
  const groups: Array<[string, Data]> = [];
  const lists: Array<[string, Array<Data>]> = [];

  for (const [key, value] of Object.entries(data)) {
    if (value === null || value === undefined) continue;
    if (Array.isArray(value)) {
      if (value.length && typeof value[0] === 'object') lists.push([key, value]);
    } else if (typeof value === 'object') {
      groups.push([key, value as Data]);
    } else {
      scalars.push([key, value]);
    }
  }

  return (
    <div className="space-y-4">
      {scalars.length > 0 && <ScalarGrid entries={scalars} />}
      {groups.map(([key, group]) => (
        <Section key={key} title={humanize(key)}>
          <ScalarGrid entries={Object.entries(group).filter(([, v]) => typeof v !== 'object')} />
        </Section>
      ))}
      {lists.map(([key, rows]) => (
        <Section key={key} title={humanize(key)}>
          <SimpleTable rows={rows} />
        </Section>
      ))}
    </div>
  );
}

function ScalarGrid({ entries }: { entries: Array<[string, unknown]> }) {
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-3">
      {entries.map(([key, value]) => (
        <Stat key={key} label={humanize(key)} value={formatValue(key, value)} size="sm" />
      ))}
    </div>
  );
}

function SimpleTable({ rows }: { rows: Array<Data> }) {
  const columns = Object.keys(rows[0] ?? {}).filter((c) => typeof rows[0][c] !== 'object');
  return (
    <div className="overflow-x-auto -mx-1">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-neutral-text-muted">
            {columns.map((c) => (
              <th key={c} className="px-1 pb-1 font-medium">
                {humanize(c)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-neutral-border/60">
              {columns.map((c) => (
                <td key={c} className="px-1 py-1.5 tabular-nums text-neutral-text-body">
                  {formatValue(c, row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatValue(key: string, value: unknown): string {
  if (typeof value === 'number') {
    if (isRupeeKey(key)) return inr(value);
    if (isPercentKey(key)) return pct(value, 1);
    return num(value);
  }
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return String(value);
}

// ----------------------------------------------------------------------
// Everything about a period
// ----------------------------------------------------------------------

export function PeriodSummary({ data }: { data: Data }) {
  return (
    <div className="space-y-6">
      {data.sales && <SalesSummary data={data.sales} />}
      {data.best_days && (
        <Section title="By day">
          <BestDays data={data.best_days} />
        </Section>
      )}
      {data.top_items && (
        <Section title="Best sellers">
          <TopItems data={data.top_items} />
        </Section>
      )}
      {data.categories && (
        <Section title="Categories">
          <CategoryPerformance data={data.categories} />
        </Section>
      )}
      {data.peak_hours && (
        <Section title="When it's busy">
          <PeakHours data={data.peak_hours} />
        </Section>
      )}
    </div>
  );
}

// ----------------------------------------------------------------------
// Registry
// ----------------------------------------------------------------------

const RENDERERS: Record<string, React.ComponentType<{ data: Data }>> = {
  sales_summary: SalesSummary,
  period_summary: PeriodSummary,
  top_items: TopItems,
  dish_details: DishDetails,
  best_days: BestDays,
  category_performance: CategoryPerformance,
  peak_hours: PeakHours,
  payment_methods: PaymentMethods,
  parcel_vs_dinein: ParcelVsDineIn,
  veg_vs_nonveg: VegVsNonVeg,
  beverage_vs_food: BeverageVsFood,
  compare_periods: ComparePeriods,
  inventory_status: InventoryStatus,
  cash_counter: CashCounter,
};

export function ReportView({ reportId, data }: { reportId: string; data: Data }) {
  const Renderer = RENDERERS[reportId] ?? KeyValues;
  return <Renderer data={data} />;
}
