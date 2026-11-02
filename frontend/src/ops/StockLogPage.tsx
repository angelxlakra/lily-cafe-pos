/**
 * Stock log: record usage or a one-off correction, and read every stock
 * movement (including nightly counts) newest first. Deliveries are recorded
 * on the Daily sheet, not here.
 */

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import LoadingSpinner from '../components/LoadingSpinner';
import { inventoryApi } from '../api/inventory';
import { useInventoryTransactions, useRecordUsage, useRecordAdjustment } from '../hooks/useInventory';
import { describeApiError } from '../utils/apiError';
import { describeChange, formatQty, isPresence } from '../utils/countQuantity';
import type { InventoryTransaction, TransactionType } from '../types/inventory';

type Action = 'USAGE' | 'ADJUSTMENT';

const ACTIONS: Record<Action, {
  button: string;
  title: string;
  quantityLabel: string;
  notesPlaceholder: string;
  help?: string;
}> = {
  USAGE: {
    button: 'Record usage',
    title: 'Record usage',
    quantityLabel: 'Quantity used',
    notesPlaceholder: 'What it was used for…',
  },
  ADJUSTMENT: {
    button: 'Fix one item',
    title: "Fix one item's stock",
    quantityLabel: 'On the shelf now',
    notesPlaceholder: 'Why it was off…',
    help: "Sets one item to what's on the shelf now. For the full nightly count, use Count.",
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

export default function StockLogPage() {
  const [activeAction, setActiveAction] = useState<Action | null>(null);

  return (
    <div>
      <h1>Stock log</h1>
      <div className="ops-actions">
        {(Object.keys(ACTIONS) as Action[]).map(action => (
          <button key={action} type="button" className="btn ghost" onClick={() => setActiveAction(action)}>
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
    <section aria-label="Stock movements">
      <div className="ops-filters">
        <label>
          <span className="sr-only">Show</span>
          <select
            value={filterType}
            onChange={(e) => { setFilterType(e.target.value as TransactionType | ''); setLimit(20); }}
          >
            <option value="">Everything</option>
            <option value="PURCHASE">Deliveries</option>
            <option value="USAGE">Usage</option>
            <option value="ADJUSTMENT">Counts and corrections</option>
          </select>
        </label>
      </div>

      {isLoading ? (
        <p className="muted"><LoadingSpinner /> Loading…</p>
      ) : isError ? (
        <div role="alert">
          <p>Couldn't load the stock log.</p>
          <button type="button" className="btn ghost" onClick={() => refetch()}>Try again</button>
        </div>
      ) : transactions.length === 0 ? (
        <p className="muted">Nothing here yet. Deliveries, usage and count changes will show up here.</p>
      ) : (
        <>
          <div className="ops-wrap">
            <table className="ops-t ops-log">
              <thead>
                <tr><th>Date</th><th>Item</th><th className="n">Change</th><th>Type</th><th>Note</th></tr>
              </thead>
              <tbody>
                {transactions.map(tx => {
                  const quantity = Number(tx.quantity);
                  // Only while the numbers are yes/no-shaped: older movements of an item
                  // switched to yes/no later (5 → 3 pcs) keep reading as numbers.
                  const yesNo = isPresence(tx) && [tx.previous_quantity, tx.new_quantity].every(q => Number(q) === 0 || Number(q) === 1);
                  return (
                    <tr key={tx.id}>
                      <td>
                        {timeFormat.format(parseTimestamp(tx.created_at))}
                        <span className="src">{tx.recorded_by}</span>
                      </td>
                      <td className="item" data-l="Item">{tx.item_name ?? 'Deleted item'}</td>
                      <td className="n">
                        <b>
                          {yesNo
                            ? (quantity === 0 ? 'No change' : quantity < 0 ? 'Ran out' : 'Have it')
                            : <>{quantity > 0 ? '+' : quantity < 0 ? '−' : ''}{formatQty(Math.abs(quantity))}</>}
                        </b>
                        <span className="src">
                          {yesNo ? describeChange(tx, tx.previous_quantity, tx.new_quantity)
                            : `${formatQty(tx.previous_quantity)} → ${formatQty(tx.new_quantity)}`}
                        </span>
                      </td>
                      <td className="type" data-l="Type">{movementLabel(tx)}</td>
                      <td className="note" data-l="Note">{tx.notes && !tx.notes.startsWith('Daily count') ? tx.notes : ''}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {data && data.total > transactions.length && (
            <div className="ops-actions">
              <button type="button" className="btn ghost" onClick={() => setLimit(value => value + 20)} disabled={isFetching}>
                {isFetching ? 'Loading…' : `Show more (${data.total - transactions.length} older)`}
              </button>
            </div>
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

  const recordUsage = useRecordUsage();
  const recordAdjustment = useRecordAdjustment();
  const isSubmitting = recordUsage.isPending || recordAdjustment.isPending;

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
      if (type === 'USAGE') await recordUsage.mutateAsync({ items: [line] });
      else await recordAdjustment.mutateAsync({ item_id: itemId, new_quantity: amount, notes: notes || undefined });
      onClose();
    } catch (error) {
      setSubmitError(describeApiError(error));
    }
  };

  return (
    <div className="count-sheet-wrap">
      <div className="count-scrim" onClick={isSubmitting ? undefined : onClose} />
      <form
        role="dialog"
        aria-modal="true"
        aria-labelledby="stock-form-title"
        className="count-sheet"
        onSubmit={handleSubmit}
      >
        <div className="count-sheet-body ops-form full">
          <h2 id="stock-form-title">{copy.title}</h2>
          {copy.help && <p className="muted">{copy.help}</p>}

          <label>
            Item
            <select
              value={itemId}
              onChange={e => setItemId(e.target.value ? Number(e.target.value) : '')}
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
              <span className="muted">In stock now: {formatQty(selectedItem.current_quantity)} {selectedItem.unit}</span>
            )}
          </label>

          <label>
            {copy.quantityLabel}{selectedItem ? ` (${selectedItem.unit})` : ''}
            <input
              type="number"
              inputMode="decimal"
              step="0.01"
              min="0"
              value={quantity}
              onChange={e => setQuantity(e.target.value)}
              required
            />
          </label>

          <label>
            Note (optional)
            <input
              value={notes}
              onChange={e => setNotes(e.target.value)}
              maxLength={500}
              placeholder={copy.notesPlaceholder}
            />
          </label>

          {submitError && <p role="alert" className="err">Not saved. {submitError}</p>}
        </div>
        <div className="count-actions">
          <button type="button" className="btn ghost" onClick={onClose} disabled={isSubmitting}>Cancel</button>
          <button type="submit" className="btn grow" disabled={isSubmitting}>{isSubmitting ? 'Saving…' : 'Save'}</button>
        </div>
      </form>
    </div>
  );
}
