/**
 * Bottom sheet shown before saving a count: what was checked, what changed
 * (big differences first, for a second look) and what wasn't counted.
 */

import { useEffect, useRef, useState } from 'react';
import { Warning } from '@phosphor-icons/react';
import LoadingSpinner from '../LoadingSpinner';
import type { InventoryItem } from '../../types/inventory';
import type { CountEntries } from '../../utils/countDraft';
import { formatQty, isBigDifference } from '../../utils/countQuantity';

interface CountReviewSheetProps {
  items: InventoryItem[];
  counts: CountEntries;
  isSaving: boolean;
  error: string | null;
  onSave: () => void;
  onClose: () => void;
  onGoToItem: (itemId: number) => void;
}

const UNCOUNTED_PREVIEW = 5;

export default function CountReviewSheet({
  items, counts, isSaving, error, onSave, onClose, onGoToItem,
}: CountReviewSheetProps) {
  const saveRef = useRef<HTMLButtonElement>(null);
  const [showAllUncounted, setShowAllUncounted] = useState(false);

  useEffect(() => {
    saveRef.current?.focus();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !isSaving) onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', onKey);
    };
  }, [isSaving, onClose]);

  const checked = items.filter(item => counts[item.id] === Number(item.current_quantity));
  const changed = items.filter(item => item.id in counts && counts[item.id] !== Number(item.current_quantity));
  const uncounted = items.filter(item => !(item.id in counts));
  const big = changed.filter(item => isBigDifference(Number(item.current_quantity), counts[item.id]));
  const shownUncounted = showAllUncounted ? uncounted : uncounted.slice(0, UNCOUNTED_PREVIEW);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <div className="absolute inset-0 bg-black/50 animate-fade-in" onClick={isSaving ? undefined : onClose} aria-hidden />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="count-review-title"
        className="relative w-full max-w-lg max-h-[88dvh] flex flex-col bg-neutral-background rounded-t-2xl shadow-strong animate-slide-up"
      >
        <div className="overflow-y-auto px-5 pt-5 pb-4">
          <h2 id="count-review-title" className="font-heading text-2xl! text-neutral-text-dark">
            Review tonight's count
          </h2>
          <p className="mt-2 tabular-nums text-neutral-text-body">
            <strong className="text-neutral-text-dark">{checked.length}</strong> checked ·{' '}
            <strong className="text-neutral-text-dark">{changed.length}</strong> changed ·{' '}
            <strong className="text-neutral-text-dark">{uncounted.length}</strong> not counted
          </p>

          {big.length > 0 && (
            <section className="mt-5" aria-labelledby="count-review-big">
              <h3 id="count-review-big" className="font-sans! text-sm! font-semibold tracking-normal! leading-normal! text-[#b45309] dark:text-warning flex items-center gap-1.5">
                <Warning size={16} weight="fill" aria-hidden />
                Big differences. Worth a second look
              </h3>
              <ul className="mt-2 divide-y divide-neutral-border rounded-lg border border-neutral-border bg-off-white">
                {big.map(item => (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => onGoToItem(item.id)}
                      className="w-full min-h-12 px-3 py-2 flex items-center justify-between gap-3 text-left hover:bg-cream/60"
                    >
                      <span className="font-medium text-neutral-text-dark min-w-0 truncate">{item.name}</span>
                      <span className="shrink-0 tabular-nums text-sm text-neutral-text-body">
                        {formatQty(item.current_quantity)} → <strong>{formatQty(counts[item.id])}</strong> {item.unit}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {uncounted.length > 0 && (
            <section className="mt-5" aria-labelledby="count-review-uncounted">
              <h3 id="count-review-uncounted" className="font-sans! text-sm! font-semibold tracking-normal! leading-normal! text-neutral-text-dark">
                Not counted
              </h3>
              <p className="mt-1 text-sm text-neutral-text-muted">
                These will be saved as not counted and keep their current stock. Tap one to count it.
              </p>
              <ul className="mt-2 divide-y divide-neutral-border rounded-lg border border-neutral-border bg-off-white">
                {shownUncounted.map(item => (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => onGoToItem(item.id)}
                      className="w-full min-h-12 px-3 py-2 flex items-center justify-between gap-3 text-left hover:bg-cream/60"
                    >
                      <span className="text-neutral-text-dark min-w-0 truncate">{item.name}</span>
                      <span className="shrink-0 text-sm text-coffee-brown font-medium">Count</span>
                    </button>
                  </li>
                ))}
              </ul>
              {uncounted.length > UNCOUNTED_PREVIEW && (
                <button
                  type="button"
                  onClick={() => setShowAllUncounted(value => !value)}
                  className="mt-2 min-h-12 text-sm font-medium text-coffee-brown"
                >
                  {showAllUncounted ? 'Show fewer' : `Show all ${uncounted.length}`}
                </button>
              )}
            </section>
          )}

          {error && (
            <div role="alert" className="mt-5 rounded-lg border border-error/40 bg-error/5 p-3 text-sm text-neutral-text-body">
              <strong className="block text-neutral-text-dark">Count not saved</strong>
              {error} Your numbers are still on this phone.
            </div>
          )}
        </div>

        <div className="flex gap-2 border-t border-neutral-border px-5 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          <button type="button" onClick={onClose} disabled={isSaving} className="btn-ghost flex-1">
            Keep counting
          </button>
          <button
            ref={saveRef}
            type="button"
            onClick={onSave}
            disabled={isSaving}
            className="btn-primary flex-[1.4] inline-flex items-center justify-center gap-2"
          >
            {isSaving ? <><LoadingSpinner size="sm" className="text-current" /> Saving…</> : error ? 'Try again' : 'Save count'}
          </button>
        </div>
      </div>
    </div>
  );
}
