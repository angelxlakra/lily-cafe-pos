// ========================================
// Tools Page
// Dish frequency report — how many times each dish was ordered
// over a chosen date interval and (optionally) a chosen set of dishes.
// ========================================

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useMenuItems } from '../hooks/useMenu';
import { analyticsApi } from '../api/analytics';
import type { DishFrequencyParams } from '../api/analytics';
import { Wrench, MagnifyingGlass, X } from '@phosphor-icons/react';

// Local YYYY-MM-DD for an offset number of days ago (IST-ish, uses browser locale).
function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

export default function ToolsPage() {
  // Filter inputs (draft) — only applied when "Run report" is pressed.
  const [startDate, setStartDate] = useState<string>(isoDaysAgo(7));
  const [endDate, setEndDate] = useState<string>(isoDaysAgo(0));
  const [paidOnly, setPaidOnly] = useState<boolean>(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [dishSearch, setDishSearch] = useState<string>('');

  // The params actually sent to the API (set on submit).
  const [appliedParams, setAppliedParams] = useState<DishFrequencyParams | null>(null);

  const { data: menuItems = [], isLoading: menuLoading } = useMenuItems();

  const filteredMenu = useMemo(() => {
    const q = dishSearch.trim().toLowerCase();
    const items = q
      ? menuItems.filter((m) => m.name.toLowerCase().includes(q))
      : menuItems;
    return [...items].sort((a, b) => a.name.localeCompare(b.name));
  }, [menuItems, dishSearch]);

  const selectedItems = useMemo(
    () => menuItems.filter((m) => selectedIds.includes(m.id)),
    [menuItems, selectedIds]
  );

  const {
    data,
    isFetching,
    isError,
    error,
  } = useQuery({
    queryKey: ['dish-frequency', appliedParams],
    queryFn: () => analyticsApi.getDishFrequency(appliedParams!),
    enabled: appliedParams !== null,
  });

  const toggleDish = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const runReport = () => {
    setAppliedParams({
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      menu_item_ids: selectedIds.length ? selectedIds : undefined,
      paid_only: paidOnly,
    });
  };

  const totalUnits = data?.rows.reduce((sum, r) => sum + r.quantity, 0) ?? 0;

  return (
    <div className="min-h-screen bg-neutral-background">
      <div className="max-w-5xl mx-auto flex flex-col p-6 md:p-8">
        {/* Header */}
        <div className="mb-6 flex items-center gap-3 flex-shrink-0">
          <Wrench size={32} weight="duotone" className="text-coffee-brown" />
          <div>
            <h1 className="font-heading heading-display text-coffee-brown mb-1">Tools</h1>
            <p className="text-neutral-text-light">
              Dish frequency — how many times each dish was ordered in a period
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-neutral-border p-5 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <label className="flex flex-col gap-1">
              <span className="text-sm font-medium text-neutral-text">From</span>
              <input
                type="date"
                value={startDate}
                max={endDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="px-3 py-2 rounded-md border border-neutral-border bg-neutral-background text-neutral-text"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-sm font-medium text-neutral-text">To</span>
              <input
                type="date"
                value={endDate}
                min={startDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="px-3 py-2 rounded-md border border-neutral-border bg-neutral-background text-neutral-text"
              />
            </label>
            <label className="flex items-center gap-2 md:pb-2">
              <input
                type="checkbox"
                checked={paidOnly}
                onChange={(e) => setPaidOnly(e.target.checked)}
                className="w-4 h-4 accent-coffee-brown"
              />
              <span className="text-sm text-neutral-text">Paid orders only</span>
            </label>
            <button
              onClick={runReport}
              className="btn bg-coffee-brown text-white hover:bg-coffee-dark md:justify-self-start"
            >
              Run report
            </button>
          </div>

          {/* Dish picker */}
          <div className="mt-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-neutral-text">
                Dishes {selectedIds.length > 0 ? `(${selectedIds.length} selected)` : '(all dishes)'}
              </span>
              {selectedIds.length > 0 && (
                <button
                  onClick={() => setSelectedIds([])}
                  className="text-xs text-coffee-brown hover:underline"
                >
                  Clear selection
                </button>
              )}
            </div>

            {/* Selected chips */}
            {selectedItems.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {selectedItems.map((item) => (
                  <span
                    key={item.id}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-coffee-brown/10 text-coffee-brown text-sm"
                  >
                    {item.name}
                    <button onClick={() => toggleDish(item.id)} aria-label={`Remove ${item.name}`}>
                      <X size={14} weight="bold" />
                    </button>
                  </span>
                ))}
              </div>
            )}

            {/* Search + list */}
            <div className="relative mb-2">
              <MagnifyingGlass
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-text-light"
              />
              <input
                type="text"
                value={dishSearch}
                onChange={(e) => setDishSearch(e.target.value)}
                placeholder="Search dishes to add…"
                className="w-full pl-9 pr-3 py-2 rounded-md border border-neutral-border bg-neutral-background text-neutral-text"
              />
            </div>
            <div className="max-h-44 overflow-y-auto rounded-md border border-neutral-border divide-y divide-neutral-border">
              {menuLoading ? (
                <p className="p-3 text-sm text-neutral-text-light">Loading menu…</p>
              ) : filteredMenu.length === 0 ? (
                <p className="p-3 text-sm text-neutral-text-light">No dishes match.</p>
              ) : (
                filteredMenu.map((item) => (
                  <label
                    key={item.id}
                    className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-neutral-background"
                  >
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(item.id)}
                      onChange={() => toggleDish(item.id)}
                      className="w-4 h-4 accent-coffee-brown"
                    />
                    <span className="text-sm text-neutral-text">{item.name}</span>
                  </label>
                ))
              )}
            </div>
            <p className="mt-2 text-xs text-neutral-text-light">
              Leave empty to include every dish. Selected dishes with no orders in the period show as 0.
            </p>
          </div>
        </div>

        {/* Results */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-neutral-border overflow-hidden">
          {appliedParams === null ? (
            <p className="p-6 text-center text-neutral-text-light">
              Choose a date range and press <span className="font-medium">Run report</span>.
            </p>
          ) : isFetching ? (
            <p className="p-6 text-center text-neutral-text-light">Loading…</p>
          ) : isError ? (
            <p className="p-6 text-center text-error">
              {(error as Error)?.message || 'Failed to load report.'}
            </p>
          ) : !data || data.rows.length === 0 ? (
            <p className="p-6 text-center text-neutral-text-light">
              No orders found for this period.
            </p>
          ) : (
            <>
              <div className="px-5 py-3 border-b border-neutral-border flex items-center justify-between text-sm text-neutral-text-light">
                <span>
                  {data.start_date ?? 'start'} → {data.end_date ?? 'today'}
                  {data.paid_only ? ' · paid only' : ' · excludes canceled'}
                </span>
                <span>
                  {data.rows.length} dishes · {totalUnits} units total
                </span>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-neutral-text-light border-b border-neutral-border">
                    <th className="px-5 py-3 w-12">#</th>
                    <th className="px-5 py-3">Dish</th>
                    <th className="px-5 py-3 text-right">Quantity served</th>
                    <th className="px-5 py-3 text-right">Times ordered</th>
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((row, idx) => (
                    <tr
                      key={`${row.menu_item_id ?? row.name}-${idx}`}
                      className="border-b border-neutral-border last:border-0 hover:bg-neutral-background"
                    >
                      <td className="px-5 py-3 text-neutral-text-light">{idx + 1}</td>
                      <td className="px-5 py-3 text-neutral-text font-medium">{row.name}</td>
                      <td className="px-5 py-3 text-right text-neutral-text tabular-nums">
                        {row.quantity}
                      </td>
                      <td className="px-5 py-3 text-right text-neutral-text-light tabular-nums">
                        {row.times_ordered}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
