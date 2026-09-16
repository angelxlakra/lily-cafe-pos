// ========================================
// Cash Day Page (hidden)
// Look up the cash counter for any single day.
// Mobile-first; reachable only by direct URL (/admin/cash-day).
// ========================================

import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { CaretLeft, CaretRight, Money } from '@phosphor-icons/react';
import { cashApi } from '../api/cash';
import { useAuth } from '../hooks/useAuth';
import { formatTime } from '../utils/formatDateTime';

const DENOMS = [500, 200, 100, 50, 20, 10] as const;

// Local (not UTC) YYYY-MM-DD for today.
function todayLocal(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function shiftDay(iso: string, days: number): string {
  const [y, m, d] = iso.split('-').map(Number);
  const dt = new Date(y, m - 1, d + days);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}`;
}

function prettyDay(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function shortDay(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

function rupees(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  const n = Number(value);
  return `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
}

const STATUS_STYLE: Record<string, { label: string; className: string }> = {
  open: { label: 'Open', className: 'bg-info/15 text-info' },
  closed_pending_verification: { label: 'Closed · awaiting verification', className: 'bg-warning/15 text-warning' },
  verified: { label: 'Verified', className: 'bg-success/15 text-success' },
};

export default function CashDayPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const today = todayLocal();

  // Previous days are owner-only on the API, so admin is pinned to today and
  // the day-stepping controls are disabled rather than left to fail with 403.
  const { isOwner } = useAuth();
  const requestedDay = searchParams.get('date') || today;
  const day = isOwner ? requestedDay : today;

  const setDay = (value: string) => {
    if (!value || !isOwner) return;
    setSearchParams({ date: value > today ? today : value }, { replace: true });
  };

  const { data, isFetching, isError, error } = useQuery({
    queryKey: ['cash-counter-day', day],
    queryFn: () => cashApi.getDay(day),
    staleTime: 30 * 1000,
  });

  const counter = data?.counter ?? null;
  const variance = counter?.variance != null ? Number(counter.variance) : null;
  const isClosed = counter?.closing_balance != null;

  return (
    <div className="min-h-screen bg-neutral-background pb-10">
      {/* Sticky day picker */}
      <div className="sticky top-0 z-10 bg-neutral-background/95 backdrop-blur border-b border-neutral-border">
        <div className="max-w-xl mx-auto px-4 pt-4 pb-3">
          <div className="flex items-center gap-2 mb-3">
            <Money size={24} weight="duotone" className="text-coffee-brown" />
            <h1 className="font-heading text-xl text-coffee-brown">Cash by day</h1>
            {isOwner && day !== today && (
              <button
                onClick={() => setDay(today)}
                className="ml-auto text-sm font-medium text-coffee-brown px-3 py-1.5 rounded-full border border-neutral-border active:scale-95 transition-transform"
              >
                Today
              </button>
            )}
          </div>

          {isOwner && (
            <div className="flex items-stretch gap-2">
              <button
                onClick={() => setDay(shiftDay(day, -1))}
                aria-label="Previous day"
                className="w-12 shrink-0 flex items-center justify-center rounded-xl border border-neutral-border bg-white dark:bg-gray-800 text-neutral-text active:scale-95 transition-transform"
              >
                <CaretLeft size={20} weight="bold" />
              </button>
              <input
                type="date"
                value={day}
                max={today}
                onChange={(e) => setDay(e.target.value)}
                className="flex-1 min-w-0 h-12 px-3 rounded-xl border border-neutral-border bg-white dark:bg-gray-800 text-neutral-text text-base text-center"
              />
              <button
                onClick={() => setDay(shiftDay(day, 1))}
                disabled={day >= today}
                aria-label="Next day"
                className="w-12 shrink-0 flex items-center justify-center rounded-xl border border-neutral-border bg-white dark:bg-gray-800 text-neutral-text active:scale-95 transition-transform disabled:opacity-40 disabled:active:scale-100"
              >
                <CaretRight size={20} weight="bold" />
              </button>
            </div>
          )}
          <p className="mt-2 text-center text-sm text-neutral-text-light">{prettyDay(day)}</p>
        </div>
      </div>

      <div className="max-w-xl mx-auto px-4 pt-4 space-y-4">
        {isError ? (
          <Card>
            <p className="text-center text-error">{(error as Error)?.message || 'Failed to load.'}</p>
          </Card>
        ) : !data ? (
          <Card>
            <p className="text-center text-neutral-text-light">Loading…</p>
          </Card>
        ) : (
          <div className={isFetching ? 'opacity-60 transition-opacity space-y-4' : 'space-y-4'}>
            {!counter ? (
              <Card>
                <p className="text-center font-medium text-neutral-text">No cash counter for this day</p>
                <p className="mt-1 text-center text-sm text-neutral-text-light">
                  Cash collected: {rupees(data.cash_payments_total)} ({data.cash_payments_count} payments)
                </p>
              </Card>
            ) : (
              <>
                {/* Headline */}
                <Card>
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm text-neutral-text-light">Status</span>
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_STYLE[counter.status]?.className ?? ''}`}>
                      {STATUS_STYLE[counter.status]?.label ?? counter.status}
                    </span>
                  </div>

                  {variance !== null && (
                    <div
                      className={`mt-4 rounded-xl p-4 text-center ${
                        variance === 0 ? 'bg-success/10' : variance > 0 ? 'bg-warning/10' : 'bg-error/10'
                      }`}
                    >
                      <p className="text-sm text-neutral-text-light">
                        {variance === 0 ? 'Perfect match' : variance > 0 ? 'Extra cash' : 'Cash short'}
                      </p>
                      <p
                        className={`text-3xl font-bold tabular-nums ${
                          variance === 0 ? 'text-success' : variance > 0 ? 'text-warning' : 'text-error'
                        }`}
                      >
                        {variance > 0 ? '+' : variance < 0 ? '−' : ''}
                        {rupees(Math.abs(variance))}
                      </p>
                    </div>
                  )}

                  <dl className="mt-4 space-y-2.5 text-base">
                    <Row label="Opening balance" value={rupees(counter.opening_balance)} />
                    <Row
                      label={`Cash sales · ${data.cash_payments_count}`}
                      value={`+ ${rupees(data.cash_payments_total)}`}
                    />
                    <div className="border-t border-neutral-border pt-2.5">
                      <Row
                        label="Expected closing"
                        value={rupees(counter.expected_closing ?? Number(counter.opening_balance) + Number(data.cash_payments_total))}
                        strong
                      />
                    </div>
                    <Row label="Counted closing" value={isClosed ? rupees(counter.closing_balance) : 'Not closed'} strong />
                  </dl>
                </Card>

                {/* Denominations */}
                <Card title="Notes counted">
                  <div className="grid grid-cols-[1fr_auto_auto] gap-x-4 text-sm">
                    <span className="pb-2 text-neutral-text-light">Note</span>
                    <span className="pb-2 text-right text-neutral-text-light w-16">Open</span>
                    <span className="pb-2 text-right text-neutral-text-light w-16">Close</span>
                    {DENOMS.map((d) => {
                      const open = counter[`opening_${d}s` as const];
                      const close = counter[`closing_${d}s` as const];
                      return (
                        <div key={d} className="contents">
                          <span className="py-2 border-t border-neutral-border font-medium text-neutral-text">₹{d}</span>
                          <span className="py-2 border-t border-neutral-border text-right tabular-nums text-neutral-text">
                            {open}
                          </span>
                          <span className="py-2 border-t border-neutral-border text-right tabular-nums text-neutral-text">
                            {close ?? '—'}
                          </span>
                        </div>
                      );
                    })}
                    <span className="pt-2 border-t-2 border-neutral-border font-semibold text-neutral-text">Total</span>
                    <span className="pt-2 border-t-2 border-neutral-border text-right tabular-nums font-semibold text-neutral-text">
                      {rupees(counter.opening_balance)}
                    </span>
                    <span className="pt-2 border-t-2 border-neutral-border text-right tabular-nums font-semibold text-neutral-text">
                      {isClosed ? rupees(counter.closing_balance) : '—'}
                    </span>
                  </div>
                </Card>

                {/* Timeline */}
                <Card title="Activity">
                  <dl className="space-y-2.5 text-sm">
                    <Row label="Opened" value={`${formatTime(counter.opened_at)} · ${counter.opened_by}`} />
                    <Row
                      label="Closed"
                      value={counter.closed_at ? `${formatTime(counter.closed_at)} · ${counter.closed_by ?? ''}` : '—'}
                    />
                    <Row
                      label="Verified"
                      value={counter.verified_at ? `${formatTime(counter.verified_at)} · ${counter.verified_by ?? ''}` : '—'}
                    />
                  </dl>
                </Card>

                {counter.notes && (
                  <Card title="Notes">
                    <p className="text-sm text-neutral-text whitespace-pre-wrap">{counter.notes}</p>
                  </Card>
                )}
              </>
            )}

            {/* Jump between recorded days */}
            {(data.prev_date || data.next_date) && (
              <div className="grid grid-cols-2 gap-2">
                {data.prev_date ? (
                  <button
                    onClick={() => setDay(data.prev_date!)}
                    className="flex items-center gap-1 justify-start px-3 py-3 rounded-xl border border-neutral-border text-sm text-coffee-brown active:scale-95 transition-transform"
                  >
                    <CaretLeft size={16} weight="bold" /> Last recorded · {shortDay(data.prev_date)}
                  </button>
                ) : (
                  <span />
                )}
                {data.next_date && (
                  <button
                    onClick={() => setDay(data.next_date!)}
                    className="flex items-center gap-1 justify-end px-3 py-3 rounded-xl border border-neutral-border text-sm text-coffee-brown active:scale-95 transition-transform"
                  >
                    Next recorded · {shortDay(data.next_date)} <CaretRight size={16} weight="bold" />
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Card({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <section className="bg-white dark:bg-gray-800 rounded-2xl border border-neutral-border p-4">
      {title && <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-neutral-text-light">{title}</h2>}
      {children}
    </section>
  );
}

function Row({ label, value, strong }: { label: string; value: string; strong?: boolean }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <dt className="text-neutral-text-light">{label}</dt>
      <dd className={`tabular-nums text-right text-neutral-text ${strong ? 'font-semibold' : ''}`}>{value}</dd>
    </div>
  );
}
