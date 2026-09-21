import React from 'react';
import { cn } from '../../utils/cn';

/** A big figure with a small label — the unit of a money screen on a phone. */
export function Stat({
  label,
  value,
  hint,
  size = 'md',
  tone,
  className,
}: {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  size?: 'lg' | 'md' | 'sm';
  tone?: 'up' | 'down' | 'muted';
  className?: string;
}) {
  return (
    <div className={cn('min-w-0', className)}>
      <div className="text-xs uppercase tracking-wide text-neutral-text-muted">{label}</div>
      <div
        className={cn(
          'font-semibold tabular-nums text-neutral-text-dark truncate',
          size === 'lg' && 'text-3xl leading-tight',
          size === 'md' && 'text-xl leading-snug',
          size === 'sm' && 'text-base',
          tone === 'up' && 'text-success',
          tone === 'down' && 'text-error',
          tone === 'muted' && 'text-neutral-text-light',
        )}
      >
        {value}
      </div>
      {hint && <div className="text-xs text-neutral-text-light mt-0.5">{hint}</div>}
    </div>
  );
}

export function Section({
  title,
  children,
  className,
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={cn('space-y-2', className)}>
      {title && (
        <h3 className="text-sm font-semibold text-neutral-text-body">{title}</h3>
      )}
      {children}
    </section>
  );
}

/** Rows with a proportional bar: readable at any width, no axes needed. */
export function ShareList({
  rows,
  max,
}: {
  rows: Array<{ key: string; label: React.ReactNode; value: number; display: string; sub?: string }>;
  max?: number;
}) {
  const top = max ?? Math.max(1, ...rows.map((r) => r.value));
  return (
    <ul className="space-y-2">
      {rows.map((row, i) => (
        <li key={row.key} className="text-sm">
          <div className="flex items-baseline justify-between gap-3">
            <span className="truncate text-neutral-text-body">
              <span className="text-neutral-text-muted tabular-nums mr-2">{i + 1}.</span>
              {row.label}
            </span>
            <span className="shrink-0 tabular-nums font-medium text-neutral-text-dark">{row.display}</span>
          </div>
          <div className="mt-1 h-1.5 w-full rounded-full bg-neutral-border/40">
            <div
              className="h-1.5 rounded-full bg-coffee-brown"
              style={{ width: `${Math.max(2, (row.value / top) * 100)}%` }}
            />
          </div>
          {row.sub && <div className="text-xs text-neutral-text-muted mt-0.5">{row.sub}</div>}
        </li>
      ))}
    </ul>
  );
}

const SEGMENT_COLORS = [
  'var(--color-coffee-brown)',
  'var(--color-lily-green)',
  'var(--color-coffee-light)',
  'var(--color-warning)',
];

/** One stacked bar for a 2–4 way split, with a legend of figures beneath. */
export function SplitBar({
  segments,
}: {
  segments: Array<{ key: string; label: string; value: number; display: string; sub?: string }>;
}) {
  const total = segments.reduce((sum, s) => sum + Math.max(0, s.value), 0);
  return (
    <div>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-neutral-border/40">
        {total > 0 &&
          segments.map((s, i) => (
            <div
              key={s.key}
              style={{ width: `${(Math.max(0, s.value) / total) * 100}%`, backgroundColor: SEGMENT_COLORS[i % SEGMENT_COLORS.length] }}
            />
          ))}
      </div>
      <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2">
        {segments.map((s, i) => (
          <li key={s.key} className="flex items-start gap-2 text-sm">
            <span
              className="mt-1.5 h-2 w-2 shrink-0 rounded-[2px]"
              style={{ backgroundColor: SEGMENT_COLORS[i % SEGMENT_COLORS.length] }}
            />
            <div className="min-w-0">
              <div className="text-neutral-text-light text-xs">{s.label}</div>
              <div className="font-medium tabular-nums text-neutral-text-dark">{s.display}</div>
              {s.sub && <div className="text-xs text-neutral-text-muted">{s.sub}</div>}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-neutral-text-light">{children}</p>;
}
