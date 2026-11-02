// The ops inventory page: stock as plain numbers, grouped by category, with the nightly count on the side.

import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { inventoryApi } from '../api/inventory';
import { useAuth } from '../hooks/useAuth';
import { useInventoryItems } from '../hooks/useInventory';
import { describeApiError } from '../utils/apiError';
import { rupees } from '../utils/costing';
import { formatQty, haveIt, isPresence } from '../utils/countQuantity';
import { localDate } from '../utils/formatDateTime';
import type { CountSummary, InventoryItem } from '../types/inventory';
import { usePurchaseDay } from './api';
import { formatPackPrice, usesPackForm } from './packPrice';

type Filter = 'all' | 'low' | 'made';
const MADE = 'Made in the kitchen';
const NIGHTS = 7;

const stockText = (item: InventoryItem) =>
  isPresence(item) ? (haveIt(item.current_quantity) === 'out' ? 'Out' : 'Have it') : `${formatQty(item.current_quantity)} ${item.unit}`;
const alertText = (item: InventoryItem) => (isPresence(item) ? '—' : `${formatQty(item.min_threshold)} ${item.unit}`);

/** The price the way the recipe page writes it: "₹99 / 10 g". */
function priceText(item: InventoryItem): string {
  if (item.current_price == null) return item.has_recipe ? 'from recipe' : '—';
  const price = Number(item.current_price);
  return usesPackForm(item) && item.pack_unit
    ? formatPackPrice(price, Number(item.pack_size), item.pack_unit)
    : formatPackPrice(price, 1, item.unit);
}

/** Stock × price; both are per the item's own unit. */
const valueOf = (item: InventoryItem): number | null =>
  item.current_price == null || isPresence(item) ? null : Math.round(Number(item.current_quantity) * Number(item.current_price));

const nightLabel = (date: string) =>
  new Date(`${date}T00:00`).toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' });

const dayDiff = (from: string, to: string) => Math.round((Date.parse(`${to}T00:00Z`) - Date.parse(`${from}T00:00Z`)) / 864e5);

/** The last seven nights ending on `today`, newest first; a night with no count says so. */
function lastNights(counts: CountSummary[], today: string) {
  const byDate = new Map<string, CountSummary>();
  for (const count of counts) if (!byDate.has(count.business_date)) byDate.set(count.business_date, count); // newest first
  return Array.from({ length: NIGHTS }, (_, i) => {
    const d = new Date(`${today}T00:00`);
    d.setDate(d.getDate() - i);
    const date = localDate(d);
    return { date, count: byDate.get(date) };
  });
}

function countedText(item: InventoryItem, today: string): string {
  if (!item.last_counted) return 'never';
  const days = dayDiff(item.last_counted, today);
  return days <= 0 ? 'today' : days === 1 ? 'yesterday' : `${days} days ago`;
}

export default function OpsInventoryPage() {
  const { isOwner } = useAuth();
  const items = useInventoryItems({ is_active: true });
  const counts = useQuery({ queryKey: ['inventory', 'counts', 'recent', 'ops'], queryFn: () => inventoryApi.getCounts(20) });
  // The server's business date (the count night runs to 04:00); local while it loads.
  const today = usePurchaseDay(undefined).data?.business_date ?? localDate();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<Filter>('all');

  const all = items.data?.items;
  const lowCount = all?.filter(i => i.is_low_stock).length ?? 0;
  const madeCount = all?.filter(i => i.has_recipe).length ?? 0;
  const totalValue = useMemo(() => (all ?? []).reduce((sum, i) => sum + (valueOf(i) ?? 0), 0), [all]);

  const groups = useMemo(() => {
    const needle = search.trim().toLowerCase();
    const shown = (all ?? []).filter(i =>
      (filter === 'all' || (filter === 'low' && i.is_low_stock) || (filter === 'made' && i.has_recipe))
      && (i.name.toLowerCase().includes(needle) || (i.brand ?? '').toLowerCase().includes(needle)));
    const byName = new Map<string, InventoryItem[]>();
    for (const item of shown) {
      const key = item.has_recipe ? MADE : item.category_name ?? 'Uncategorised';
      byName.set(key, [...(byName.get(key) ?? []), item]);
    }
    // Made items last, as in the mockup; the rest keep the order the server sorted them in.
    return [...byName.entries()].sort(([a], [b]) => Number(a === MADE) - Number(b === MADE));
  }, [all, search, filter]);

  if (items.isError) return <p className="err">{describeApiError(items.error)}</p>;
  if (!all) return <p className="muted">Loading…</p>;

  const nights = lastNights(counts.data ?? [], today);
  const FILTERS: { id: Filter; label: string }[] = [
    { id: 'all', label: 'All' }, { id: 'low', label: `Low (${lowCount})` }, { id: 'made', label: `Made here (${madeCount})` },
  ];

  return (
    <>
      <h1>Inventory</h1>
      <p className="muted">{all.length} items · stock value {rupees(totalValue)}</p>
      <div className="ops-inv">
        <aside className="ops-inv-side">
          <h2>Daily count</h2>
          <Link to="/admin/inventory/count" className="btn ops-link-btn">Start tonight's count</Link>
          <table className="ops-nights">
            <caption className="sr-only">Last {NIGHTS} nights</caption>
            <tbody>
              {nights.map(({ date, count }) => (
                <tr key={date}>
                  <td>{nightLabel(date)}</td>
                  {count
                    ? <><td>{count.counted_by}</td><td className="n">{count.items_checked} / {count.items_total}</td></>
                    : <td colSpan={2} className="muted">no count</td>}
                </tr>
              ))}
            </tbody>
          </table>
          {counts.isError && <p className="err">{describeApiError(counts.error)}</p>}
        </aside>
        <div className="ops-inv-main">
          <div className="ops-filters">
            <input
              type="search" className="grow" placeholder="Search items or brands" aria-label="Search items"
              value={search} onChange={e => setSearch(e.target.value)}
            />
            <div className="chips" role="group" aria-label="Filter">
              {FILTERS.map(f => (
                <button key={f.id} type="button" className={`chip${filter === f.id ? ' on' : ''}`} aria-pressed={filter === f.id} onClick={() => setFilter(f.id)}>
                  {f.label}
                </button>
              ))}
            </div>
            {isOwner && <Link to="/admin/inventory?tab=items&edit=all" className="btn ghost ops-link-btn">Edit all</Link>}
          </div>
          <div className="ops-wrap">
            <table className="ops-t ops-inv-t">
              <thead>
                <tr>
                  <th>Item</th><th>Brand</th><th className="n">In stock</th><th className="n">Alert below</th>
                  <th className="n">Price</th><th className="n">Value</th><th>Counted</th>
                </tr>
              </thead>
              {groups.map(([group, rows]) => (
                <tbody key={group}>
                  <tr className="cat"><th colSpan={7} scope="colgroup">{group}</th></tr>
                  {rows.map(item => {
                    const value = valueOf(item);
                    return (
                      <tr key={item.id} className="row">
                        <td className="name">
                          {item.name}{item.has_recipe && <> <span className="pill made">made</span></>}
                          <span className="sub">{[item.brand, priceText(item)].filter(Boolean).join(' · ')}</span>
                        </td>
                        <td className="brand">{item.brand ?? ''}</td>
                        <td className="n stock">{item.is_low_stock ? <span className="pill bad">{stockText(item)}</span> : stockText(item)}</td>
                        <td className="n alert">{alertText(item)}</td>
                        <td className="n price">{priceText(item)}</td>
                        <td className="n val">{value == null ? '' : rupees(value)}</td>
                        <td className="counted muted">{countedText(item, today)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              ))}
              {groups.length === 0 && <tbody><tr><td colSpan={7} className="muted">{all.length === 0 ? 'No items yet.' : 'Nothing matches.'}</td></tr></tbody>}
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
