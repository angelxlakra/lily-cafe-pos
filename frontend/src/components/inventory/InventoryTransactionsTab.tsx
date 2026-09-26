/**
 * Stock log: record a delivery, usage, or a one-off correction, and read
 * every stock movement (including nightly counts) newest first.
 */

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, Minus, ArrowsLeftRight, X } from '@phosphor-icons/react';
import LoadingSpinner from '../LoadingSpinner';
import { inventoryApi } from '../../api/inventory';
import { useInventoryTransactions, useRecordPurchase, useRecordUsage, useRecordAdjustment } from '../../hooks/useInventory';
import { describeApiError } from '../../utils/apiError';
import { describeChange, formatQty, isPresence } from '../../utils/countQuantity';
import type { InventoryTransaction, TransactionType } from '../../types/inventory';

type Action = 'PURCHASE' | 'USAGE' | 'ADJUSTMENT';

const ACTIONS: Record<Action, {
  button: string;
  title: string;
  quantityLabel: string;
  notesPlaceholder: string;
  help?: string;
  icon: JSX.Element;
}> = {
  PURCHASE: {
    button: 'Delivery received',
    title: 'Delivery received',
    quantityLabel: 'Quantity received',
    notesPlaceholder: 'Supplier, bill number…',
    icon: <Plus size={18} weight="bold" aria-hidden />,
  },
  USAGE: {
    button: 'Record usage',
    title: 'Record usage',
    quantityLabel: 'Quantity used',
    notesPlaceholder: 'What it was used for…',
    icon: <Minus size={18} weight="bold" aria-hidden />,
  },
  ADJUSTMENT: {
    button: 'Fix one item',
    title: "Fix one item's stock",
    quantityLabel: 'On the shelf now',
    notesPlaceholder: 'Why it was off…',
    help: "Sets one item to what's on the shelf now. For the full nightly count, use Daily count.",
    icon: <ArrowsLeftRight size={18} weight="bold" aria-hidden />,
  },
};

/** Stored timestamps are UTC; SQLite returns them without an offset. */
const parseTimestamp = (value: string) =>
  new Date(/([zZ]|[+-]\d\d:?\d\d)$/.test(value) ? value : `${value}Z`);

const timeFormat = new Intl.DateTimeFormat('en-IN', {
  timeZone: 'Asia/Kolkata',
  day: 'numeric',
  month: 'short',
  hour: 'numeric',
  minute: '2-digit',
});

const movementLabel = (tx: InventoryTransaction) => {
  if (tx.transaction_type === 'PURCHASE') return 'Delivery';
  if (tx.transaction_type === 'USAGE') return 'Used';
  return tx.notes?.startsWith('Daily count') ? 'Nightly count' : 'Correction';
};

export default function InventoryTransactionsTab() {
  const [activeAction, setActiveAction] = useState<Action | null>(null);

  return (
    <div className="space-y-6">
      <div className="grid gap-2 sm:grid-cols-3">
        {(Object.keys(ACTIONS) as Action[]).map(action => (
          <button
            key={action}
            onClick={() => setActiveAction(action)}
            className="btn-secondary inline-flex items-center justify-center gap-2 whitespace-nowrap [&>svg]:shrink-0"
          >
            {ACTIONS[action].icon}
            {ACTIONS[action].button}
          </button>
        ))}
      </div>

      {activeAction && <TransactionFormModal type={activeAction} onClose={() => setActiveAction(null)} />}

      <StockLog />
    </div>
  );
}

function StockLog() {
  const [filterType, setFilterType] = useState<TransactionType | ''>('');
  const [limit, setLimit] = useState(20);
  const { data, isLoading, isError, refetch, isFetching } = useInventoryTransactions({
    transaction_type: filterType || undefined,
    limit,
  });
  const transactions = data?.transactions ?? [];

  return (
    <section aria-labelledby="stock-log-title">
      <div className="flex items-center justify-between gap-3 mb-2">
        <h2 id="stock-log-title" className="font-heading text-xl! leading-tight! text-neutral-text-dark">Stock log</h2>
        <label>
          <span className="sr-only">Show</span>
          <select
            value={filterType}
            onChange={(e) => { setFilterType(e.target.value as TransactionType | ''); setLimit(20); }}
            className="input-field w-auto min-h-12 py-2"
          >
            <option value="">Everything</option>
            <option value="PURCHASE">Deliveries</option>
            <option value="USAGE">Usage</option>
            <option value="ADJUSTMENT">Counts and corrections</option>
          </select>
        </label>
      </div>

      {isLoading ? (
        <div className="py-10 flex justify-center gap-3 text-neutral-text-muted"><LoadingSpinner /> Loading…</div>
      ) : isError ? (
        <div role="alert" className="card p-4">
          <p className="text-neutral-text-dark">Couldn't load the stock log.</p>
          <button onClick={() => refetch()} className="btn-secondary mt-3">Try again</button>
        </div>
      ) : transactions.length === 0 ? (
        <div className="card p-8 text-center text-neutral-text-muted">
          Nothing here yet. Deliveries, usage and count changes will show up here.
        </div>
      ) : (
        <>
          <ul className="card divide-y divide-neutral-border overflow-hidden">
            {transactions.map(tx => {
              const quantity = Number(tx.quantity);
              // Only while the numbers are yes/no-shaped: older movements of an item
              // switched to yes/no later (5 → 3 pcs) keep reading as numbers.
              const yesNo = isPresence(tx) && [tx.previous_quantity, tx.new_quantity].every(q => Number(q) === 0 || Number(q) === 1);
              return (
                <li key={tx.id} className="flex items-start gap-3 px-4 py-3">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium leading-snug text-neutral-text-dark break-words">{tx.item_name ?? 'Deleted item'}</div>
                    <div className="text-xs text-neutral-text-muted">
                      {movementLabel(tx)} · {timeFormat.format(parseTimestamp(tx.created_at))} · {tx.recorded_by}
                    </div>
                    {tx.notes && !tx.notes.startsWith('Daily count') && (
                      <div className="mt-0.5 text-sm text-neutral-text-body break-words">{tx.notes}</div>
                    )}
                  </div>
                  <div className="shrink-0 text-right tabular-nums">
                    <div className="font-semibold text-neutral-text-dark">
                      {yesNo
                        ? (quantity === 0 ? 'No change' : quantity < 0 ? 'Ran out' : 'Have it')
                        : <>{quantity > 0 ? '+' : quantity < 0 ? '−' : ''}{formatQty(Math.abs(quantity))}</>}
                    </div>
                    <div className="text-xs text-neutral-text-muted">
                      {yesNo ? describeChange(tx, tx.previous_quantity, tx.new_quantity)
                        : `${formatQty(tx.previous_quantity)} → ${formatQty(tx.new_quantity)}`}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
          {data && data.total > transactions.length && (
            <button onClick={() => setLimit(value => value + 20)} disabled={isFetching} className="btn-ghost w-full mt-2">
              {isFetching ? 'Loading…' : `Show more (${data.total - transactions.length} older)`}
            </button>
          )}
        </>
      )}
    </section>
  );
}

function TransactionFormModal({ type, onClose }: { type: Action; onClose: () => void }) {
  const copy = ACTIONS[type];
  const [itemId, setItemId] = useState<number | ''>('');
  // Kept as the raw input string so 0 ("ran out") is a real value, not "empty".
  const [quantity, setQuantity] = useState('');
  const [notes, setNotes] = useState('');
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Items grouped by category in count order, so a long list is scannable.
  const { data: groups = [] } = useQuery({
    queryKey: ['inventory', 'count-sheet'],
    queryFn: inventoryApi.getCountSheet,
  });
  // Yes/no items are answered in the nightly count, not moved by quantity:
  // "used 3 chilli oil" has no meaning, so they aren't offered here.
  const pickable = groups
    .map(group => ({ ...group, items: group.items.filter(item => !isPresence(item)) }))
    .filter(group => group.items.length > 0);
  const selectedItem = pickable.flatMap(group => group.items).find(item => item.id === itemId);

  const recordPurchase = useRecordPurchase();
  const recordUsage = useRecordUsage();
  const recordAdjustment = useRecordAdjustment();
  const isSubmitting = recordPurchase.isPending || recordUsage.isPending || recordAdjustment.isPending;

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => event.key === 'Escape' && !isSubmitting && onClose();
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose, isSubmitting]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!itemId || quantity === '') return;
    const amount = Number(quantity);
    if (type !== 'ADJUSTMENT' && amount <= 0) {
      setSubmitError('Enter a quantity above 0.');
      return;
    }
    setSubmitError(null);

    try {
      const line = { item_id: itemId, quantity: amount, notes: notes || undefined };
      if (type === 'PURCHASE') await recordPurchase.mutateAsync({ items: [line] });
      else if (type === 'USAGE') await recordUsage.mutateAsync({ items: [line] });
      else await recordAdjustment.mutateAsync({ item_id: itemId, new_quantity: amount, notes: notes || undefined });
      onClose();
    } catch (error) {
      setSubmitError(describeApiError(error));
    }
  };

  const field = 'block text-sm font-medium text-neutral-text-body mb-1';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in" onClick={isSubmitting ? undefined : onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="stock-form-title"
        className="card w-full max-w-md max-h-[90dvh] overflow-y-auto p-6 shadow-strong animate-scale-in"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex justify-between items-start gap-3 mb-4">
          <div>
            <h2 id="stock-form-title" className="font-heading text-2xl! text-neutral-text-dark">{copy.title}</h2>
            {copy.help && <p className="mt-1 text-sm text-neutral-text-muted">{copy.help}</p>}
          </div>
          <button onClick={onClose} aria-label="Close" className="size-12 -mr-3 -mt-2 shrink-0 grid place-items-center text-neutral-text-muted hover:text-neutral-text-dark">
            <X size={22} aria-hidden />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="stock-item" className={field}>Item</label>
            <select
              id="stock-item"
              value={itemId}
              onChange={e => setItemId(e.target.value ? Number(e.target.value) : '')}
              className="input-field"
              required
            >
              <option value="">Choose an item…</option>
              {pickable.map(group => (
                <optgroup key={group.category?.id ?? 'none'} label={group.category?.name ?? 'Uncategorized'}>
                  {group.items.map(item => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </optgroup>
              ))}
            </select>
            {selectedItem && (
              <p className="mt-1 text-sm text-neutral-text-muted tabular-nums">
                In stock now: {formatQty(selectedItem.current_quantity)} {selectedItem.unit}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="stock-quantity" className={field}>{copy.quantityLabel}</label>
            <div className="flex items-center gap-2">
              <input
                id="stock-quantity"
                type="number"
                inputMode="decimal"
                step="0.01"
                min="0"
                value={quantity}
                onChange={e => setQuantity(e.target.value)}
                className="input-field"
                required
              />
              {selectedItem && <span className="text-neutral-text-muted font-medium">{selectedItem.unit}</span>}
            </div>
          </div>

          <div>
            <label htmlFor="stock-notes" className={field}>Note <span className="font-normal text-neutral-text-muted">(optional)</span></label>
            <textarea
              id="stock-notes"
              value={notes}
              onChange={e => setNotes(e.target.value)}
              maxLength={500}
              className="input-field min-h-20"
              placeholder={copy.notesPlaceholder}
            />
          </div>

          {submitError && (
            <div role="alert" className="text-sm font-medium text-error">Not saved. {submitError}</div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} disabled={isSubmitting} className="btn-ghost">Cancel</button>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
