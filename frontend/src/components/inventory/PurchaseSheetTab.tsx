/**
 * The day's purchase sheet, as the owners drew it: one table per day.
 *
 *   Item · Unit qty · Rate · Purchased · In · Used · Remaining · Day-end · Wastage
 *
 * Staff fill unit qty, rate and how many were bought; In is rate × purchased.
 * Used comes from the day's sales × recipes, Remaining is what should be left,
 * Day-end is tonight's count for that item (the same number the count screen
 * saves), and Wastage is the gap. Rows are only what was bought.
 *
 * Adding a line must stay quick — about 90 seconds for a day's shopping — so
 * the new row below the table is keyboard-first and saves in the background.
 * Each day's sheet is kept; staff see today's, the owner can open any day.
 */

import { useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Warning, X } from '@phosphor-icons/react';
import { inventoryApi } from '../../api/inventory';
import { useAuth } from '../../hooks/useAuth';
import { describeApiError } from '../../utils/apiError';
import { isPresence, parseQty } from '../../utils/countQuantity';
import { entryUnit, isPriceJump, lineColumns, parseRupees, pickItems, rupees, trim } from '../../utils/purchaseSheet';
import type { DayItemColumns, InventoryItem, Purchase, PurchaseItem } from '../../types/inventory';

const NEW_ITEM_UNITS = ['kg', 'L', 'pcs', 'pack', 'bottle'];

const field =
  'h-12 rounded-lg border border-neutral-border bg-off-white px-3 text-base text-neutral-text-dark placeholder:text-neutral-text-muted focus:outline-none focus:border-lily-ink focus:bg-white dark:focus:bg-neutral-background';
const cell = 'h-10 px-2 rounded bg-transparent text-right tabular-nums outline-none focus:ring-2 focus:ring-coffee-brown focus:bg-white dark:focus:bg-neutral-background';
const th = 'px-2 py-2 text-right text-xs font-medium text-neutral-text-muted whitespace-nowrap';
const td = 'border-b border-neutral-border/70 px-1 py-1 text-right tabular-nums whitespace-nowrap';

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

const localToday = () => new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD

export default function PurchaseSheetTab() {
  const queryClient = useQueryClient();
  const { isOwner } = useAuth();
  // '' = today, as the server reckons it (the count night, which runs to 04:00).
  const [date, setDate] = useState('');

  const { data: itemsResponse } = useQuery({
    queryKey: ['inventory', 'items', { is_active: true }],
    queryFn: () => inventoryApi.getItems({ is_active: true }),
  });
  const { data: frequent = [] } = useQuery({
    queryKey: ['inventory', 'purchases', 'frequent'],
    queryFn: inventoryApi.getFrequentPurchases,
  });
  const { data: day, error: dayError } = useQuery({
    queryKey: ['inventory', 'purchases', 'day', date],
    queryFn: () => inventoryApi.getPurchases(date || undefined),
  });
  const { data: vendors = [] } = useQuery({ queryKey: ['inventory', 'vendors'], queryFn: inventoryApi.getVendors });
  const items = useMemo(() => itemsResponse?.items ?? [], [itemsResponse]);
  const presenceIds = useMemo(() => new Set(items.filter(isPresence).map(item => item.id)), [items]);
  const editable = day?.editable ?? !date;

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

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['inventory'] });

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
    // Mid-screen: clear of the pinned total, with room for the picker below.
    searchRef.current?.scrollIntoView({ block: 'center' });
  };

  const vendorId = (name: string): Promise<number | null> => {
    if (!name) return Promise.resolve(null);
    const known = vendors.find(v => v.name.toLowerCase() === name.toLowerCase());
    if (known) return Promise.resolve(known.id);
    const key = name.toLowerCase();
    if (!vendorIds.current.has(key)) {
      vendorIds.current.set(key, inventoryApi.createVendor(name).then(made => {
        queryClient.invalidateQueries({ queryKey: ['inventory', 'vendors'] });
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
      await queryClient.invalidateQueries({ queryKey: ['inventory', 'purchases', 'day'] });
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

  const dateLabel = day
    ? new Date(`${day.business_date}T00:00`).toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })
    : '';

  return (
    <div className="pb-28">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-heading text-xl! text-neutral-text-dark">Purchases · {dateLabel}</h2>
          <p className="text-sm text-neutral-text-muted">
            {editable
              ? 'Unit qty × rate × how many. Stock goes up as each line is added.'
              : 'A past day: read only.'}
          </p>
        </div>
        {isOwner && (
          <label className="flex items-center gap-2 text-sm text-neutral-text-body">
            Day
            <input
              type="date"
              value={date || day?.business_date || ''}
              max={localToday()}
              onChange={event => setDate(event.target.value === localToday() ? '' : event.target.value)}
              className={`${field} h-11`}
            />
          </label>
        )}
      </div>

      {dayError && <p role="alert" className="mb-3 text-sm font-medium text-error">{describeApiError(dayError)}</p>}

      {/* relative: the sr-only header is absolutely placed; without a positioned
          scroller it escapes the clip and widens the whole page on a phone. */}
      <div className="card relative overflow-x-auto">
        <table className="w-full min-w-[56rem] border-separate border-spacing-0 text-sm">
          <thead>
            <tr>
              <th className={`${th.replace('text-right', 'text-left')} sticky left-0 z-10 bg-off-white min-w-40`}>Item</th>
              <th className={th}>Unit qty</th>
              <th className={th}>Rate ₹</th>
              <th className={th}>Purchased</th>
              <th className={th}>In ₹</th>
              <th className={th} title="From the day's sales × recipes">Used</th>
              <th className={th} title="What should be left: start of day + bought − used">Remaining</th>
              <th className={th} title="Tonight's count for this item">Day-end</th>
              <th className={th} title="Remaining − day-end">Wastage</th>
              {editable && <th className={th}><span className="sr-only">Remove</span></th>}
            </tr>
          </thead>
          <tbody>
            {purchases.length === 0 && pending.length === 0 && (
              <tr>
                <td colSpan={10} className="px-3 py-4 text-neutral-text-muted">
                  {editable ? 'Nothing bought yet today. Add the first line below.' : 'Nothing was logged this day.'}
                </td>
              </tr>
            )}
            {purchases.map(purchase => (
              <SheetRow
                key={purchase.id}
                purchase={purchase}
                presence={presenceIds.has(purchase.item_id)}
                columns={firstLineOf.has(purchase.id) ? day?.items[purchase.item_id] : undefined}
                editable={editable}
                onSaved={refresh}
              />
            ))}
            {editable && pending.map(entry => (
              <tr key={entry.key}>
                <td className="sticky left-0 z-10 bg-off-white border-b border-neutral-border/70 px-2 py-2">
                  <span className="block font-medium text-neutral-text-dark">{entry.label}</span>
                  {entry.error
                    ? <span role="alert" className="block text-xs font-medium text-error">Not saved: {entry.error}</span>
                    : <span className="block text-xs text-neutral-text-muted">Saving…</span>}
                </td>
                <td className={td} colSpan={3}>
                  {entry.error && (
                    <span className="inline-flex gap-1">
                      <button type="button" onClick={() => save(entry)} className="h-10 px-3 rounded-lg font-semibold text-coffee-brown">Retry</button>
                      <button type="button" onClick={() => setPending(list => list.filter(p => p.key !== entry.key))} className="h-10 px-3 rounded-lg text-neutral-text-muted">Drop</button>
                    </span>
                  )}
                </td>
                <td className={`${td} px-2 font-semibold text-neutral-text-muted`}>{rupees(entry.amount)}</td>
                <td className={td} colSpan={5} />
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editable && (
        <div className="card mt-3 p-3">
          <div className="text-xs font-medium uppercase tracking-wide text-neutral-text-muted mb-2">New line</div>
          <div className="relative">
            <label htmlFor="purchase-item" className="sr-only">Item bought</label>
            <input
              id="purchase-item"
              ref={searchRef}
              role="combobox"
              aria-expanded={pickerOpen && optionCount > 0}
              aria-controls="purchase-item-options"
              aria-activedescendant={pickerOpen ? `purchase-option-${highlight}` : undefined}
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
              className={`${field} w-full font-medium`}
            />
            {pickerOpen && optionCount > 0 && (
              <ul
                id="purchase-item-options"
                role="listbox"
                className="absolute z-20 left-0 right-0 mt-1 card shadow-lg max-h-80 overflow-y-auto py-1"
              >
                {!query.trim() && (
                  <li role="presentation" className="px-3 pt-1 pb-1.5 text-xs font-medium uppercase tracking-wide text-neutral-text-muted">
                    Bought often
                  </li>
                )}
                {options.map((item, index) => (
                  <li
                    key={item.id}
                    id={`purchase-option-${index}`}
                    role="option"
                    aria-selected={highlight === index}
                    onMouseDown={event => event.preventDefault()}
                    onClick={() => choose(item)}
                    className={`flex items-center justify-between gap-3 px-3 min-h-11 cursor-pointer ${highlight === index ? 'bg-cream' : ''}`}
                  >
                    <span className="truncate text-neutral-text-dark">{item.name}</span>
                    <span className="shrink-0 text-xs text-neutral-text-muted">
                      {isPresence(item) ? 'yes/no' : entryUnit(item.unit).label}
                    </span>
                  </li>
                ))}
                {offerNew && (
                  <li
                    id={`purchase-option-${options.length}`}
                    role="option"
                    aria-selected={highlight === options.length}
                    onMouseDown={event => event.preventDefault()}
                    onClick={() => {
                      setNewItemName(query.trim());
                      setPickerOpen(false);
                    }}
                    className={`flex items-center gap-2 px-3 min-h-11 cursor-pointer text-coffee-brown font-medium ${highlight === options.length ? 'bg-cream' : ''}`}
                  >
                    <Plus size={16} aria-hidden /> Add “{query.trim()}” as a new item
                  </li>
                )}
              </ul>
            )}
          </div>

          {newItemName && (
            <div className="mt-2 rounded-lg border border-neutral-border p-3">
              <p className="text-sm text-neutral-text-body">
                <span className="font-medium">{newItemName}</span> is new. What unit is it bought in? The owner sets the rest later.
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {NEW_ITEM_UNITS.map(u => (
                  <button
                    key={u}
                    type="button"
                    onClick={() => addNewItem(u)}
                    className="h-11 min-w-14 px-3 rounded-lg border border-neutral-border bg-white dark:bg-neutral-background font-medium hover:border-lily-ink"
                  >
                    {u}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="mt-2 grid grid-cols-3 gap-2">
            <label className="block">
              <span className="block text-xs text-neutral-text-muted mb-1">Unit qty</span>
              <span className="relative block">
                <input
                  inputMode="decimal"
                  autoComplete="off"
                  disabled={presence}
                  placeholder={presence ? '—' : '1'}
                  value={unitQtyText}
                  onChange={event => setUnitQtyText(event.target.value)}
                  onKeyDown={onEnter(() => rateRef.current?.focus())}
                  className={`${field} w-full pr-10 tabular-nums disabled:opacity-50`}
                />
                <span className="absolute right-2 top-1/2 -translate-y-1/2 text-sm text-neutral-text-muted pointer-events-none">
                  {presence ? '' : unit?.label ?? ''}
                </span>
              </span>
            </label>
            <label className="block">
              <span className="block text-xs text-neutral-text-muted mb-1">Rate ₹</span>
              <input
                ref={rateRef}
                inputMode="decimal"
                enterKeyHint="next"
                autoComplete="off"
                placeholder={picked?.current_price ? String(Math.round(Number(picked.current_price) * (unit?.factor ?? 1) * (unitQty ?? 1))) : ''}
                value={rateText}
                onChange={event => {
                  setRateText(event.target.value);
                  setJump(null);
                }}
                onKeyDown={onEnter(() => (presence ? submit() : countRef.current?.focus()))}
                className={`${field} w-full tabular-nums font-semibold`}
              />
            </label>
            <label className="block">
              <span className="block text-xs text-neutral-text-muted mb-1">Purchased</span>
              <input
                ref={countRef}
                inputMode="decimal"
                enterKeyHint="done"
                autoComplete="off"
                disabled={presence}
                placeholder={presence ? '1' : ''}
                value={countText}
                onChange={event => {
                  setCountText(event.target.value);
                  setJump(null);
                }}
                onKeyDown={onEnter(() => submit())}
                className={`${field} w-full tabular-nums disabled:opacity-50`}
              />
            </label>
          </div>

          <div className="mt-2 flex items-center gap-2">
            <label htmlFor="purchase-vendor" className="sr-only">Vendor (optional)</label>
            {/* No datalist: its popup swallows Enter, so the line wouldn't save. */}
            <input
              id="purchase-vendor"
              autoComplete="off"
              placeholder="Vendor (optional)"
              value={vendorText}
              onChange={event => setVendorText(event.target.value)}
              onKeyDown={onEnter(() => submit())}
              className={`${field} flex-1 min-w-0`}
            />
            <span className="shrink-0 w-28 text-right tabular-nums">
              <span className="block text-xs text-neutral-text-muted">In</span>
              <span className="font-semibold text-neutral-text-dark">{draftIn === null ? '—' : rupees(draftIn)}</span>
            </span>
          </div>

          {vendors.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5" role="group" aria-label="Known vendors">
              {vendors.map(v => {
                const on = vendorText.trim().toLowerCase() === v.name.toLowerCase();
                return (
                  <button
                    key={v.id}
                    type="button"
                    aria-pressed={on}
                    onClick={() => setVendorText(on ? '' : v.name)}
                    className={`h-9 px-3 rounded-full border text-sm ${on ? 'border-coffee-brown bg-cream text-neutral-text-dark font-medium' : 'border-neutral-border text-neutral-text-body'}`}
                  >
                    {v.name}
                  </button>
                );
              })}
            </div>
          )}

          {draftIn === 0 && (
            <input
              ref={noteRef}
              aria-label="Why was it free?"
              placeholder="Why ₹0? e.g. free from the vendor"
              value={note}
              onChange={event => setNote(event.target.value)}
              onKeyDown={onEnter(() => submit())}
              className={`${field} w-full mt-2`}
            />
          )}

          {picked && !presence && perUnit(picked.current_price, picked.unit) && (
            <p className="mt-2 text-xs text-neutral-text-muted">Last paid {perUnit(picked.current_price, picked.unit)}</p>
          )}

          {error && <p role="alert" className="mt-2 text-sm font-medium text-error">{error}</p>}

          {jump ? (
            <div role="alertdialog" aria-labelledby="purchase-jump" ref={el => el?.scrollIntoView({ block: 'center' })} className="mt-3 rounded-lg border border-warning bg-warning/10 p-3">
              <p id="purchase-jump" className="flex gap-2 text-sm text-neutral-text-dark">
                <Warning size={18} weight="fill" className="text-warning shrink-0 mt-0.5" aria-hidden />
                <span>
                  {picked?.name} was {perUnit(jump.previous, picked!.unit)}, this is{' '}
                  <strong>{perUnit(jump.next, picked!.unit)}</strong>. Is that right?
                </span>
              </p>
              <div className="mt-3 flex gap-2">
                <button type="button" autoFocus onClick={() => submit(true)} className="btn-primary h-11 px-4 rounded-lg font-semibold">
                  Yes, add it
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setJump(null);
                    rateRef.current?.select();
                  }}
                  className="h-11 px-4 rounded-lg border border-neutral-border font-medium"
                >
                  Fix it
                </button>
              </div>
            </div>
          ) : (
            <button type="button" onClick={() => submit()} className="btn-primary mt-3 w-full h-12 rounded-lg font-semibold">
              Add line
            </button>
          )}
        </div>
      )}

      {/* The number to check against the cash spent. Below lg the admin layout
          scrolls as a document, so "sticky" would sit at the end; pin it instead. */}
      <div className="fixed inset-x-0 bottom-0 z-30 px-4 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] bg-off-white border-t border-neutral-border flex items-baseline justify-between gap-3 lg:sticky lg:mt-4 lg:rounded-b-lg">
        <span className="text-sm text-neutral-text-body">
          {editable ? "Today's total" : 'Day total'}
          {editable && draftIn !== null && draftIn > 0 && (
            <span className="block text-xs text-neutral-text-muted">incl. {rupees(draftIn)} not added yet</span>
          )}
          {!!day?.unpriced && (
            <span className="block text-xs text-warning">{day.unpriced} line{day.unpriced > 1 ? 's' : ''} with no amount</span>
          )}
        </span>
        <span aria-live="polite" className="font-heading text-2xl font-semibold tabular-nums text-neutral-text-dark">
          {rupees(dayTotal + (editable && draftIn ? draftIn : 0))}
        </span>
      </div>
    </div>
  );
}

/**
 * One saved line. On today's sheet the staff cells are inputs that save on
 * Enter or leaving the cell; the day-end cell writes tonight's count.
 */
function SheetRow({ purchase, presence, columns, editable, onSaved }: {
  purchase: Purchase;
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
    editable && !disabled ? (
      <CellInput value={value} ariaLabel={`${purchase.item_name} ${ariaLabel}`} onCommit={onCommit} />
    ) : (
      <span className="block px-2">{value == null || disabled ? '—' : trim(value)}</span>
    );

  const stock = (value: number | string | null | undefined, empty: string) =>
    value == null ? <span className="text-neutral-text-muted text-xs">{empty}</span> : `${trim(Number(value) / factor)} ${label}`;

  return (
    <tr>
      <td className="sticky left-0 z-10 bg-off-white border-b border-neutral-border/70 px-2 py-1.5 align-top">
        <span className="block font-medium text-neutral-text-dark">{purchase.item_name}</span>
        {(purchase.vendor_name || purchase.notes) && (
          <span className="block text-xs text-neutral-text-muted">{[purchase.vendor_name, purchase.notes].filter(Boolean).join(' · ')}</span>
        )}
        {error && <span role="alert" className="block text-xs font-medium text-error">{error}</span>}
      </td>
      <td className={td}>
        <span className="flex items-center justify-end">
          {numberCell(presence ? null : unitQty, 'unit quantity', n => n > 0 && change({ unitQty: n }), presence)}
          {!presence && <span className="text-xs text-neutral-text-muted pr-1">{label}</span>}
        </span>
      </td>
      <td className={td}>{numberCell(rate, 'rate', n => change({ rate: n }))}</td>
      <td className={td}>{numberCell(presence ? null : count, 'purchased', n => n > 0 && change({ count: n }), presence)}</td>
      <td className={`${td} px-2 font-semibold text-neutral-text-dark`}>
        {purchase.total_amount == null ? '—' : rupees(purchase.total_amount)}
      </td>
      {columns ? (
        <>
          <td className={`${td} px-2`}>{stock(columns.used, 'needs recipe')}</td>
          <td className={`${td} px-2`}>{stock(columns.remaining, '—')}</td>
          <td className={td}>
            {editable ? (
              <span className="flex items-center justify-end">
                <CellInput
                  value={columns.day_end == null ? null : Number(columns.day_end) / factor}
                  placeholder="count"
                  ariaLabel={`${purchase.item_name} day-end count, in ${label}`}
                  onCommit={n => run(() => inventoryApi.setDayEnd(purchase.item_id, n * factor))}
                />
                <span className="text-xs text-neutral-text-muted pr-1">{label}</span>
              </span>
            ) : (
              <span className="block px-2">{stock(columns.day_end, 'not counted')}</span>
            )}
          </td>
          <td className={`${td} px-2 ${columns.wastage != null && Number(columns.wastage) > 0 ? 'font-semibold text-warning' : ''}`}>
            {stock(columns.wastage, '—')}
          </td>
        </>
      ) : (
        <td className={`${td} px-2 text-xs text-neutral-text-muted`} colSpan={4}>
          {/* A second line for an item already shown above. */}
          same item ↑
        </td>
      )}
      {editable && (
        <td className={td}>
          {confirmRemove ? (
            <span className="inline-flex gap-1">
              <button type="button" onClick={() => run(() => inventoryApi.deletePurchase(purchase.id))} className="h-10 px-2 rounded-lg font-semibold text-error">Remove</button>
              <button type="button" onClick={() => setConfirmRemove(false)} className="h-10 px-2 rounded-lg text-neutral-text-muted">Keep</button>
            </span>
          ) : (
            <button
              type="button"
              aria-label={`Remove ${purchase.item_name}`}
              onClick={() => setConfirmRemove(true)}
              className="size-10 grid place-items-center rounded-lg text-neutral-text-light hover:text-error hover:bg-error/10"
            >
              <X size={16} aria-hidden />
            </button>
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
      className={`${cell} w-20 placeholder:text-neutral-text-light`}
    />
  );
}
