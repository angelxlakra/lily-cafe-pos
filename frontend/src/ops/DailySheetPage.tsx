// The daily purchase sheet in the ops look. Same endpoints and rules as the Purchases tab
// (PurchaseSheetTab), plus the owner's "price changes to approve" cards.

import { useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { inventoryApi } from '../api/inventory';
import { useAuth } from '../hooks/useAuth';
import { costingKeys } from '../hooks/useCosting';
import { inventoryKeys, useInventoryItems } from '../hooks/useInventory';
import { describeApiError } from '../utils/apiError';
import { isPresence, parseQty } from '../utils/countQuantity';
import { localDate } from '../utils/formatDateTime';
import { entryUnit, isPriceJump, lineColumns, parseRupees, pickItems, rupees, showQuantity, trim } from '../utils/purchaseSheet';
import type { DayItemColumns, InventoryItem, Purchase, PurchaseItem } from '../types/inventory';
import { useApproveAllPrices, useOverview, usePendingPrices, usePurchaseDay, useReviewPrice } from './api';
import type { PendingPrice } from './api';

const NEW_ITEM_UNITS = ['kg', 'L', 'pcs', 'pack', 'bottle'];
const DATE = /^\d{4}-\d{2}-\d{2}$/;

/** A line on its way to the server. The form is already free for the next one. */
interface PendingLine {
  key: number;
  label: string;
  amount: number;
  line: PurchaseItem;
  vendorName: string;
  error?: string;
}

const perUnit = (price: number | string | null | undefined, unit: string) => {
  const { label, factor } = entryUnit(unit);
  return price == null ? null : `${rupees(Number(price) * factor)}/${label}`;
};

const shiftDay = (date: string, days: number) => {
  const d = new Date(`${date}T00:00`);
  d.setDate(d.getDate() + days);
  return localDate(d);
};

export default function DailySheetPage() {
  const queryClient = useQueryClient();
  const { isOwner } = useAuth();
  const [params, setParams] = useSearchParams();
  const today = localDate();
  // Admin sees today only: a date in the URL is ignored. Today itself sends no date (the server's "today").
  const asked = isOwner ? params.get('date') : null;
  const date = asked && DATE.test(asked) && asked < today ? asked : undefined;
  const setDate = (next: string) => setParams(next && next < today ? { date: next } : {});

  const dayQuery = usePurchaseDay(date);
  const day = dayQuery.data;
  const editable = day?.editable ?? !date;
  const { data: itemsResponse } = useInventoryItems({ is_active: true });
  const { data: frequent = [] } = useQuery({
    queryKey: [...inventoryKeys.all, 'purchases', 'frequent'],
    queryFn: inventoryApi.getFrequentPurchases,
  });
  const { data: vendors = [] } = useQuery({ queryKey: [...inventoryKeys.all, 'vendors'], queryFn: inventoryApi.getVendors });
  const items = useMemo(() => itemsResponse?.items ?? [], [itemsResponse]);
  const presenceIds = useMemo(() => new Set(items.filter(isPresence).map(item => item.id)), [items]);
  const brands = useMemo(() => new Map(items.map(item => [item.id, item.brand])), [items]);

  const [query, setQuery] = useState('');
  const [pickerOpen, setPickerOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const [picked, setPicked] = useState<InventoryItem | null>(null);
  const [newItemName, setNewItemName] = useState<string | null>(null);
  const [unitQtyText, setUnitQtyText] = useState('');
  const [rateText, setRateText] = useState('');
  const [countText, setCountText] = useState('');
  const [note, setNote] = useState('');
  // Sticky across rows: one shop, several lines. Shown in the row, so never silent.
  const [vendorText, setVendorText] = useState('');
  const [jump, setJump] = useState<{ previous: number; next: number } | null>(null);
  const [pending, setPending] = useState<PendingLine[]>([]);
  const [error, setError] = useState<string | null>(null);

  const searchRef = useRef<HTMLInputElement>(null);
  const rateRef = useRef<HTMLInputElement>(null);
  const countRef = useRef<HTMLInputElement>(null);
  const noteRef = useRef<HTMLInputElement>(null);
  // One create per new vendor name, even when two lines for it save at once.
  const vendorIds = useRef(new Map<string, Promise<number>>());

  const options = useMemo(() => pickItems(items, query, frequent), [items, query, frequent]);
  const exactMatch = items.some(item => item.name.toLowerCase() === query.trim().toLowerCase());
  const offerNew = query.trim() !== '' && !exactMatch;
  const optionCount = options.length + (offerNew ? 1 : 0);

  const presence = picked ? isPresence(picked) : false;
  const unit = picked ? entryUnit(picked.unit) : null;
  const unitQty = unitQtyText.trim() === '' ? 1 : parseQty(unitQtyText);
  const rate = parseRupees(rateText);
  const count = presence ? 1 : parseQty(countText);
  const draftIn = rate !== null && count !== null ? Math.round(rate * count * 100) / 100 : null;
  const purchases = day?.purchases ?? [];
  const pendingTotal = editable ? pending.reduce((sum, p) => sum + p.amount, 0) : 0;
  const dayTotal = Number(day?.total_amount ?? 0) + pendingTotal;

  // A purchase moves stock, prices, the approval list and costs, so refresh all of them.
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: inventoryKeys.all });
    queryClient.invalidateQueries({ queryKey: costingKeys.all });
  };

  const choose = (item: InventoryItem) => {
    setPicked(item);
    setQuery(item.name);
    setPickerOpen(false);
    setNewItemName(null);
    setError(null);
    // Unit qty is usually 1 (1 kg, 1 pc) and left blank; the rate is what changes.
    rateRef.current?.focus();
  };

  const addNewItem = async (unitName: string) => {
    if (!newItemName) return;
    try {
      const item = await inventoryApi.quickAddItem(newItemName, unitName);
      refresh();
      choose(item);
    } catch (e) {
      setError(describeApiError(e));
    }
  };

  const reset = () => {
    setPicked(null);
    setQuery('');
    setUnitQtyText('');
    setRateText('');
    setCountText('');
    setNote('');
    setJump(null);
    setError(null);
    searchRef.current?.focus();
  };

  const vendorId = (name: string): Promise<number | null> => {
    if (!name) return Promise.resolve(null);
    const known = vendors.find(v => v.name.toLowerCase() === name.toLowerCase());
    if (known) return Promise.resolve(known.id);
    const key = name.toLowerCase();
    if (!vendorIds.current.has(key)) {
      vendorIds.current.set(key, inventoryApi.createVendor(name).then(made => {
        queryClient.invalidateQueries({ queryKey: [...inventoryKeys.all, 'vendors'] });
        return made.id;
      }));
    }
    const made = vendorIds.current.get(key)!;
    made.catch(() => vendorIds.current.delete(key)); // let a retry try again
    return made;
  };

  /** Save in the background; the row stays on screen until it is in the day's list. */
  const save = async (entry: PendingLine) => {
    setPending(list => [...list.filter(p => p.key !== entry.key), { ...entry, error: undefined }]);
    try {
      await inventoryApi.recordPurchase({ items: [{ ...entry.line, vendor_id: await vendorId(entry.vendorName) }] });
      await queryClient.invalidateQueries({ queryKey: inventoryKeys.all });
      setPending(list => list.filter(p => p.key !== entry.key));
      refresh();
    } catch (e) {
      setPending(list => list.map(p => (p.key === entry.key ? { ...p, error: describeApiError(e) } : p)));
    }
  };

  const submit = (confirmed = false) => {
    if (!picked) {
      setError('Pick what you bought first.');
      searchRef.current?.focus();
      return;
    }
    if (!presence && (unitQty === null || unitQty <= 0)) {
      setError(`Unit quantity should be a number of ${unit!.label}, like 1 or 0.5.`);
      return;
    }
    if (rate === null) {
      setError('What was the rate?');
      rateRef.current?.focus();
      return;
    }
    if (count === null || count <= 0) {
      setError('How many did you buy?');
      countRef.current?.focus();
      return;
    }
    if (draftIn === 0 && !note.trim()) {
      setError('₹0 — say why, e.g. "free from the vendor".');
      noteRef.current?.focus();
      return;
    }
    const quantity = presence ? 1 : unitQty! * count * unit!.factor;
    // Asked here, not after a round trip, so nothing typed next can be lost
    // while waiting. The server's own check still runs on save.
    const next = draftIn! / quantity;
    if (!confirmed && !presence && isPriceJump(picked.current_price, next)) {
      setJump({ previous: Number(picked.current_price), next });
      return;
    }
    save({
      key: Date.now(),
      label: presence ? picked.name : `${picked.name} · ${trim(unitQty!)} ${unit!.label} × ${trim(count)}`,
      amount: draftIn!,
      line: {
        item_id: picked.id,
        quantity,
        total_amount: draftIn,
        pack_count: presence ? undefined : count,
        notes: note.trim() || undefined,
      },
      vendorName: vendorText.trim(),
    });
    reset();
  };

  const onSearchKey = (event: React.KeyboardEvent) => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      setPickerOpen(true);
      setHighlight(h => (h + (event.key === 'ArrowDown' ? 1 : -1) + optionCount) % Math.max(optionCount, 1));
    } else if (event.key === 'Enter') {
      event.preventDefault();
      if (highlight < options.length) {
        if (options[highlight]) choose(options[highlight]);
      } else if (offerNew) {
        setNewItemName(query.trim());
        setPickerOpen(false);
      }
    } else if (event.key === 'Escape') {
      setPickerOpen(false);
    }
  };

  const onEnter = (next: () => void) => (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      next();
    }
  };

  // The owners' columns belong to the item, so they show once, on its first line.
  const firstLineOf = new Set<number>();
  const seen = new Set<number>();
  for (const purchase of purchases) {
    if (!seen.has(purchase.item_id)) firstLineOf.add(purchase.id);
    seen.add(purchase.item_id);
  }

  const shown = day?.business_date ?? date ?? today;
  const isToday = !date;
  const dateLabel = new Date(`${shown}T00:00`).toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' });
  const cols = editable ? 11 : 10;

  return (
    <>
      <h1>Daily sheet · {dateLabel}</h1>
      <p className="muted">
        {editable ? 'Unit qty × rate × how many. Stock goes up as each line is added.' : 'A past day: read only.'}
      </p>

      {isOwner && (
        <div className="ops-filters ops-day">
          <button type="button" className="btn ghost" aria-label="Previous day" onClick={() => setDate(shiftDay(shown, -1))}>‹</button>
          <label>
            <span className="sr-only">Day</span>
            <input type="date" value={shown} max={today} onChange={e => e.target.value && setDate(e.target.value)} />
          </label>
          <button type="button" className="btn ghost" aria-label="Next day" disabled={isToday} onClick={() => setDate(shiftDay(shown, 1))}>›</button>
          {!isToday && <button type="button" className="btn ghost" onClick={() => setDate('')}>Today</button>}
        </div>
      )}

      {isOwner && <Approvals />}

      {dayQuery.isError && <p role="alert" className="err">{describeApiError(dayQuery.error)}</p>}

      {editable && (
        <form className="ops-line" aria-label="New line" onSubmit={e => { e.preventDefault(); submit(); }}>
          <div className="ops-pick item">
            <label>
              <span>Item bought</span>
              <input
                ref={searchRef}
                role="combobox"
                aria-expanded={pickerOpen && optionCount > 0}
                aria-controls="sheet-item-options"
                aria-activedescendant={pickerOpen ? `sheet-option-${highlight}` : undefined}
                autoComplete="off"
                enterKeyHint="next"
                placeholder="What did you buy?"
                value={query}
                onChange={event => {
                  setQuery(event.target.value);
                  setPicked(null);
                  setNewItemName(null);
                  setHighlight(0);
                  setPickerOpen(true);
                  setJump(null);
                }}
                onFocus={() => !picked && setPickerOpen(true)}
                onBlur={() => setTimeout(() => setPickerOpen(false), 150)}
                onKeyDown={onSearchKey}
              />
            </label>
            {pickerOpen && optionCount > 0 && (
              <ul id="sheet-item-options" role="listbox" aria-label="Items">
                {!query.trim() && <li role="presentation" className="muted pad">Bought often</li>}
                {options.map((item, index) => (
                  <li key={item.id} role="presentation">
                    <button
                      type="button" tabIndex={-1} role="option" id={`sheet-option-${index}`} aria-selected={highlight === index}
                      onMouseDown={event => event.preventDefault()} onClick={() => choose(item)}
                    >
                      <span>{item.name}{item.brand ? ` · ${item.brand}` : ''}</span>
                      <span className="muted">{isPresence(item) ? 'yes/no' : entryUnit(item.unit).label}</span>
                    </button>
                  </li>
                ))}
                {offerNew && (
                  <li role="presentation">
                    <button
                      type="button" tabIndex={-1} role="option" id={`sheet-option-${options.length}`} aria-selected={highlight === options.length}
                      onMouseDown={event => event.preventDefault()}
                      onClick={() => { setNewItemName(query.trim()); setPickerOpen(false); }}
                    >
                      + Add “{query.trim()}” as a new item
                    </button>
                  </li>
                )}
              </ul>
            )}
          </div>

          <label>
            <span>Unit qty{unit && !presence ? ` (${unit.label})` : ''}</span>
            <input
              inputMode="decimal" autoComplete="off" disabled={presence} placeholder={presence ? '—' : '1'}
              value={unitQtyText} onChange={event => setUnitQtyText(event.target.value)}
              onKeyDown={onEnter(() => rateRef.current?.focus())}
            />
          </label>
          <label>
            <span>Rate ₹</span>
            <input
              ref={rateRef} inputMode="decimal" enterKeyHint="next" autoComplete="off"
              placeholder={picked?.current_price ? String(Math.round(Number(picked.current_price) * (unit?.factor ?? 1) * (unitQty ?? 1))) : ''}
              value={rateText}
              onChange={event => { setRateText(event.target.value); setJump(null); }}
              onKeyDown={onEnter(() => (presence ? submit() : countRef.current?.focus()))}
            />
          </label>
          <label>
            <span>Purchased</span>
            <input
              ref={countRef} inputMode="decimal" enterKeyHint="done" autoComplete="off" disabled={presence} placeholder={presence ? '1' : ''}
              value={countText}
              onChange={event => { setCountText(event.target.value); setJump(null); }}
              onKeyDown={onEnter(() => submit())}
            />
          </label>
          <label>
            <span>Vendor (optional)</span>
            {/* No datalist: its popup swallows Enter, so the line wouldn't save. */}
            <input autoComplete="off" value={vendorText} onChange={event => setVendorText(event.target.value)} onKeyDown={onEnter(() => submit())} />
          </label>
          <div className="ops-in" aria-live="polite"><span>In</span><b>{draftIn === null ? '—' : rupees(draftIn)}</b></div>
          <button type="submit" className="btn add" disabled={!!jump}>Add line</button>

          {newItemName && (
            <div className="wide">
              <p><b>{newItemName}</b> is new. What unit is it bought in? The owner sets the rest later.</p>
              <div className="chips" role="group" aria-label="Unit for the new item">
                {NEW_ITEM_UNITS.map(u => <button key={u} type="button" className="chip" onClick={() => addNewItem(u)}>{u}</button>)}
              </div>
            </div>
          )}
          {vendors.length > 0 && (
            <div className="wide chips" role="group" aria-label="Known vendors">
              {vendors.map(v => {
                const on = vendorText.trim().toLowerCase() === v.name.toLowerCase();
                return (
                  <button key={v.id} type="button" className={`chip${on ? ' on' : ''}`} aria-pressed={on} onClick={() => setVendorText(on ? '' : v.name)}>
                    {v.name}
                  </button>
                );
              })}
            </div>
          )}
          {draftIn === 0 && (
            <input
              ref={noteRef} className="wide" aria-label="Why was it free?" placeholder="Why ₹0? e.g. free from the vendor"
              value={note} onChange={event => setNote(event.target.value)} onKeyDown={onEnter(() => submit())}
            />
          )}
          {picked && !presence && perUnit(picked.current_price, picked.unit) && (
            <p className="wide muted">Last paid {perUnit(picked.current_price, picked.unit)}</p>
          )}
          {error && <p role="alert" className="wide err">{error}</p>}
          {jump && (
            <div role="alertdialog" aria-labelledby="sheet-jump" className="wide ops-jump">
              <p id="sheet-jump">
                {picked?.name} was {perUnit(jump.previous, picked!.unit)}, this is <b>{perUnit(jump.next, picked!.unit)}</b>. Is that right?
              </p>
              <button type="button" autoFocus className="btn" onClick={() => submit(true)}>Yes, add it</button>{' '}
              <button type="button" className="btn ghost" onClick={() => { setJump(null); rateRef.current?.select(); }}>Fix it</button>
            </div>
          )}
        </form>
      )}

      <div className="ops-wrap">
        <table className="ops-t ops-sheet">
          <thead>
            <tr>
              <th>Item</th><th>Brand</th><th className="n">Unit qty</th><th className="n">Rate ₹</th><th className="n">Purchased</th>
              <th className="n">In ₹</th>
              <th className="n" title="From the day's sales × recipes">Out (used)</th>
              <th className="n" title="What should be left: start of day + bought − used">Remaining</th>
              <th className="n" title="Tonight's count for this item">Day-end</th>
              <th className="n" title="Remaining − day-end">Wastage</th>
              {editable && <th><span className="sr-only">Remove</span></th>}
            </tr>
          </thead>
          <tbody>
            {dayQuery.isLoading && <tr><td colSpan={cols} className="muted">Loading…</td></tr>}
            {day && purchases.length === 0 && pending.length === 0 && (
              <tr><td colSpan={cols} className="muted">{editable ? 'Nothing bought yet today. Add the first line above.' : 'Nothing was logged this day.'}</td></tr>
            )}
            {purchases.map(purchase => (
              <SheetRow
                key={purchase.id}
                purchase={purchase}
                brand={brands.get(purchase.item_id)}
                presence={presenceIds.has(purchase.item_id)}
                columns={firstLineOf.has(purchase.id) ? day?.items[purchase.item_id] : undefined}
                editable={editable}
                onSaved={refresh}
              />
            ))}
            {editable && pending.map(entry => (
              <tr key={entry.key}>
                <td>
                  <span>{entry.label}</span>
                  {entry.error
                    ? <span role="alert" className="err">Not saved: {entry.error}</span>
                    : <span className="src">Saving…</span>}
                </td>
                <td colSpan={4}>
                  {entry.error && (
                    <>
                      <button type="button" className="btn ghost" onClick={() => save(entry)}>Retry</button>{' '}
                      <button type="button" className="btn ghost" onClick={() => setPending(list => list.filter(p => p.key !== entry.key))}>Drop</button>
                    </>
                  )}
                </td>
                <td className="n">{rupees(entry.amount)}</td>
                <td colSpan={5} />
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="tot">
              <td colSpan={5}>
                {isToday ? 'Spent today' : `Spent on ${dateLabel}`}
                {!!day?.unpriced && <span className="err">{day.unpriced} line{day.unpriced > 1 ? 's' : ''} with no amount</span>}
              </td>
              <td className="n" aria-live="polite">{rupees(dayTotal)}</td>
              <td colSpan={editable ? 5 : 4} />
            </tr>
          </tfoot>
        </table>
      </div>
    </>
  );
}

// ---------- Price approvals (owner) ----------

const money = (n: number) => `₹${(Math.round(Math.abs(n) * 100) / 100).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
const signed = (n: number) => `${n < 0 ? '−' : '+'}${money(n)}`;

function Approvals() {
  const pending = usePendingPrices(true);
  const overview = useOverview(true);
  const approveAll = useApproveAllPrices();
  // The ripple names the dishes; their margin target comes with the costing overview.
  const targets = useMemo(
    () => new Map((overview.data?.rows ?? []).filter(r => r.costing_id != null).map(r => [r.costing_id, r.target_margin_percent])),
    [overview.data],
  );

  if (pending.isError) return <p role="alert" className="err">{describeApiError(pending.error)}</p>;
  const list = pending.data ?? [];
  if (list.length === 0) return null;

  return (
    <section className="ops-approve" aria-labelledby="approve-h">
      <h2 id="approve-h">Price changes to approve ({list.length})</h2>
      {list.map(p => <ApprovalCard key={p.purchase_id} p={p} targets={targets} />)}
      <button type="button" className="btn" disabled={approveAll.isPending} onClick={() => approveAll.mutate()}>
        Approve all {list.length}
      </button>
      {approveAll.isError && <span role="alert" className="err">{describeApiError(approveAll.error)}</span>}
    </section>
  );
}

function ApprovalCard({ p, targets }: { p: PendingPrice; targets: Map<number | null, number | string | null> }) {
  const review = useReviewPrice();
  const { label, factor } = entryUnit(p.unit);
  const per = (v: number | string | null) => (v == null ? '' : money(Number(v) * factor));
  const change = p.change == null ? null : Number(p.change);
  const dishes = p.ripple?.affected_dishes ?? [];
  const deltas = dishes.map(d => Math.abs(Number(d.cost_after) - Number(d.cost_before)));
  const lo = Math.min(...deltas);
  const hi = Math.max(...deltas);
  const cheaper = dishes.length > 0 && dishes.every(d => Number(d.cost_after) < Number(d.cost_before));
  const act = (action: 'approve' | 'reject') => review.mutate({ purchaseId: p.purchase_id, action });

  return (
    <div className="chg">
      <div className="top">
        <span>
          <b>{p.item_name}{p.brand ? ` · ${p.brand}` : ''}</b>{' '}
          {p.is_new_item
            ? <>new · {per(p.new_price)} / {label}</>
            : <>{per(p.old_price)} → {per(p.new_price)} / {label}</>}{' '}
          {p.is_new_item
            ? <span className="pill">new</span>
            : change != null && <span className={`pill ${change > 0.1 ? 'bad' : 'warn'}`}>{change < 0 ? '−' : '+'}{Math.abs(Math.round(change * 100))}%</span>}
        </span>
        <span className="muted">bought by {p.recorded_by} · {showQuantity(p.quantity, p.unit)}</span>
        <span className="acts">
          <button type="button" className="btn" disabled={review.isPending} onClick={() => act('approve')}>Approve</button>
          <button type="button" className="btn ghost" disabled={review.isPending} onClick={() => act('reject')}>Not this time</button>
        </span>
      </div>
      <ul>
        {dishes.length > 0 && (
          <li>
            {dishes.length} dish{dishes.length === 1 ? '' : 'es'} cost{dishes.length === 1 ? 's' : ''} {cheaper ? 'less' : 'more'},{' '}
            {lo === hi ? `${money(lo)} a portion` : `${money(lo)} to ${money(hi)} a portion`}
          </li>
        )}
        {dishes.filter(d => d.crosses_below_target).map(d => {
          const target = targets.get(d.costing_id);
          return (
            <li key={d.costing_id}>
              <b>{d.menu_item_name}</b> drops to {d.margin_after == null ? '?' : `${Math.round(Number(d.margin_after))}%`}, below the{' '}
              {target == null ? '' : `${Math.round(Number(target))}% `}target
            </li>
          );
        })}
        {(p.ripple?.made_items ?? []).map(m => {
          const k = dishes.filter(d => d.via.includes(m.name)).length;
          return (
            <li key={m.item_id}>
              Also through <b>{m.name}</b>: {signed(Number(m.cost_after) - Number(m.cost_before))} per {m.unit} → {k} dish{k === 1 ? '' : 'es'}
            </li>
          );
        })}
        {dishes.length === 0 && <li>{p.is_new_item ? 'Not in any recipe yet' : 'No recipe uses it yet'}</li>}
      </ul>
      {review.isError && <p role="alert" className="err">{describeApiError(review.error)}</p>}
    </div>
  );
}

// ---------- Rows ----------

/**
 * One saved line. On an editable day the staff cells are inputs that save on
 * Enter or leaving the cell; the day-end cell writes tonight's count.
 */
function SheetRow({ purchase, brand, presence, columns, editable, onSaved }: {
  purchase: Purchase;
  brand?: string | null;
  presence: boolean;
  /** The owners' columns, on the item's first line of the day only. */
  columns?: DayItemColumns;
  editable: boolean;
  onSaved: () => void;
}) {
  const { unitQty, rate, count } = lineColumns(purchase.quantity, purchase.total_amount, purchase.pack_count, purchase.unit);
  const { label, factor } = entryUnit(purchase.unit);
  const [error, setError] = useState<string | null>(null);
  const [confirmRemove, setConfirmRemove] = useState(false);

  const run = async (action: () => Promise<unknown>) => {
    try {
      setError(null);
      await action();
      onSaved();
    } catch (e) {
      setError(describeApiError(e));
    }
  };

  /** Re-save the line from its three staff columns. */
  const change = (next: { unitQty?: number; rate?: number; count?: number }) => {
    const u = next.unitQty ?? unitQty;
    const r = next.rate ?? rate ?? 0;
    const c = next.count ?? count;
    run(() => inventoryApi.editPurchase(purchase.id, {
      total_amount: Math.round(r * c * 100) / 100,
      ...(presence ? {} : { quantity: u * c * factor, pack_count: c }),
    }));
  };

  const numberCell = (value: number | null, ariaLabel: string, onCommit: (n: number) => void, disabled = false) =>
    editable && !disabled
      ? <CellInput value={value} ariaLabel={`${purchase.item_name} ${ariaLabel}`} onCommit={onCommit} />
      : (value == null || disabled ? '—' : trim(value));

  const stock = (value: number | string | null | undefined, empty: string) =>
    value == null ? <span className="muted">{empty}</span> : `${trim(Number(value) / factor)} ${label}`;

  return (
    <tr>
      <td>
        <b>{purchase.item_name}</b>
        {purchase.price_status === 'pending' && <> <span className="pill warn">awaiting approval</span></>}
        {(purchase.vendor_name || purchase.notes) && <span className="src">{[purchase.vendor_name, purchase.notes].filter(Boolean).join(' · ')}</span>}
        {error && <span role="alert" className="err">{error}</span>}
      </td>
      <td>{brand ?? ''}</td>
      <td className="n">
        {numberCell(presence ? null : unitQty, 'unit quantity', n => n > 0 && change({ unitQty: n }), presence)}
        {!presence && <span className="muted"> {label}</span>}
      </td>
      <td className="n">{numberCell(rate, 'rate', n => change({ rate: n }))}</td>
      <td className="n">{numberCell(presence ? null : count, 'purchased', n => n > 0 && change({ count: n }), presence)}</td>
      <td className="n">{purchase.total_amount == null ? '—' : rupees(purchase.total_amount)}</td>
      {columns ? (
        <>
          <td className="n">{stock(columns.used, 'needs recipe')}</td>
          <td className="n">{stock(columns.remaining, '—')}</td>
          <td className="n">
            {editable ? (
              <>
                <CellInput
                  value={columns.day_end == null ? null : Number(columns.day_end) / factor}
                  placeholder="count"
                  ariaLabel={`${purchase.item_name} day-end count, in ${label}`}
                  onCommit={n => run(() => inventoryApi.setDayEnd(purchase.item_id, n * factor))}
                />
                <span className="muted"> {label}</span>
              </>
            ) : stock(columns.day_end, 'not counted')}
          </td>
          <td className={`n${columns.wastage != null && Number(columns.wastage) > 0 ? ' up' : ''}`}>{stock(columns.wastage, '—')}</td>
        </>
      ) : (
        <td colSpan={4} className="muted">same item ↑</td>
      )}
      {editable && (
        <td>
          {confirmRemove ? (
            <>
              <button type="button" className="btn ghost" onClick={() => run(() => inventoryApi.deletePurchase(purchase.id))}>Remove</button>{' '}
              <button type="button" className="btn ghost" onClick={() => setConfirmRemove(false)}>Keep</button>
            </>
          ) : (
            <button type="button" className="icon-btn" aria-label={`Remove ${purchase.item_name}`} onClick={() => setConfirmRemove(true)}>✕</button>
          )}
        </td>
      )}
    </tr>
  );
}

/** A number cell that saves on Enter or when you leave it, only if it changed. Escape undoes. */
function CellInput({ value, ariaLabel, onCommit, placeholder }: {
  value: number | null;
  ariaLabel: string;
  onCommit: (n: number) => void;
  placeholder?: string;
}) {
  const shown = value == null ? '' : trim(value);
  const [text, setText] = useState<string | null>(null);
  const cancel = useRef(false);
  const commit = () => {
    if (text === null) return;
    const n = cancel.current ? null : parseQty(text.replace(/[₹,]/g, ''));
    cancel.current = false;
    setText(null);
    if (n !== null && n >= 0 && trim(n) !== shown) onCommit(n);
  };
  return (
    <input
      className="sheet-cell"
      inputMode="decimal"
      aria-label={ariaLabel}
      placeholder={placeholder}
      value={text ?? shown}
      onFocus={event => {
        setText(shown);
        event.currentTarget.select();
      }}
      onChange={event => setText(event.target.value)}
      onBlur={commit}
      onKeyDown={event => {
        if (event.key === 'Enter') event.currentTarget.blur();
        if (event.key === 'Escape') {
          cancel.current = true;
          event.currentTarget.blur();
        }
      }}
    />
  );
}
