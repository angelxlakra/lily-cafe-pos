/**
 * Bottom sheet shown before saving a count: what was checked, what changed
 * (big differences first, for a second look), yes/no items that flipped,
 * and what wasn't counted.
 */

import { useEffect, useRef, useState } from 'react';
import { useDialogFocus } from '../hooks/useDialogFocus';
import type { InventoryItem } from '../types/inventory';
import type { CountEntries } from '../utils/countDraft';
import { describeChange, formatQty, isPresence } from '../utils/countQuantity';

interface CountReviewSheetProps {
  items: InventoryItem[];
  counts: CountEntries;
  /** The few changes worth a second look, most extreme first (see pickBigDifferences). */
  bigDifferences: InventoryItem[];
  isSaving: boolean;
  error: string | null;
  onSave: () => void;
  onClose: () => void;
  onGoToItem: (itemId: number) => void;
}

const UNCOUNTED_PREVIEW = 5;

export default function CountReviewSheet({
  items, counts, bigDifferences: big, isSaving, error, onSave, onClose, onGoToItem,
}: CountReviewSheetProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const saveRef = useRef<HTMLButtonElement>(null);
  const keepCountingRef = useRef<HTMLButtonElement>(null);
  const errorRef = useRef<HTMLDivElement>(null);
  const [showAllUncounted, setShowAllUncounted] = useState(false);
  useDialogFocus(dialogRef, onClose, isSaving);

  const checked = items.filter(item => counts[item.id] === Number(item.current_quantity));
  const changed = items.filter(item => item.id in counts && counts[item.id] !== Number(item.current_quantity));
  const uncounted = items.filter(item => !(item.id in counts));
  // Never in the big differences (an answer can't be mistyped), but worth seeing: this is what ran out.
  const flipped = changed.filter(isPresence);
  const shownUncounted = showAllUncounted ? uncounted : uncounted.slice(0, UNCOUNTED_PREVIEW);
  const nothingCounted = uncounted.length === items.length;
  const mostlyUncounted = !nothingCounted && uncounted.length > items.length / 2;

  useEffect(() => {
    (nothingCounted ? keepCountingRef : saveRef).current?.focus();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // The error sits at the end of a long scroll area; bring it into view so it can't be missed.
  useEffect(() => {
    if (error) errorRef.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [error]);

  return (
    <div className="count-sheet-wrap">
      <div className="count-scrim" onClick={isSaving ? undefined : onClose} aria-hidden />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="count-review-title"
        className="count-sheet"
      >
        <div className="count-sheet-body">
          <h2 id="count-review-title">
            Review tonight's count
          </h2>
          <p className="count-totals">
            <strong>{checked.length}</strong> checked ·{' '}
            <strong>{changed.length}</strong> changed ·{' '}
            <strong>{uncounted.length}</strong> not counted
          </p>

          {big.length > 0 && (
            <section aria-labelledby="count-review-big">
              <h3 id="count-review-big" className="warn">
                <span aria-hidden>⚠ </span>
                Big differences. Worth a second look
              </h3>
              <ul className="count-list">
                {big.map(item => (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => onGoToItem(item.id)}
                      className="count-pick"
                    >
                      <span className="nm">{item.name}</span>
                      <span className="val">
                        {formatQty(item.current_quantity)} → <strong>{formatQty(counts[item.id])}</strong> {item.unit}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {flipped.length > 0 && (
            <section aria-labelledby="count-review-flipped">
              <h3 id="count-review-flipped">
                Yes / no changes
              </h3>
              <ul className="count-list">
                {flipped.map(item => (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => onGoToItem(item.id)}
                      className="count-pick"
                    >
                      <span className="nm">{item.name}</span>
                      <span className="val">
                        {describeChange(item, item.current_quantity, counts[item.id])}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {uncounted.length > 0 && (
            <section aria-labelledby="count-review-uncounted">
              <h3 id="count-review-uncounted">
                Not counted
              </h3>
              <p className="muted">
                These will be saved as not counted and keep their current stock. Tap one to count it.
              </p>
              <ul className="count-list">
                {shownUncounted.map(item => (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => onGoToItem(item.id)}
                      className="count-pick"
                    >
                      <span className="nm">{item.name}</span>
                      <span className="val go">Count</span>
                    </button>
                  </li>
                ))}
              </ul>
              {uncounted.length > UNCOUNTED_PREVIEW && (
                <button
                  type="button"
                  onClick={() => setShowAllUncounted(value => !value)}
                  className="count-more"
                >
                  {showAllUncounted ? 'Show fewer' : `Show all ${uncounted.length}`}
                </button>
              )}
            </section>
          )}

          {nothingCounted && (
            <p className="count-note">
              Nothing has been counted yet, so there's nothing to save.
            </p>
          )}
          {mostlyUncounted && (
            <p className="count-note warn">
              More than half the items haven't been counted. You can still save; they'll be recorded as not counted.
            </p>
          )}

          {error && (
            <div ref={errorRef} role="alert" className="count-fail">
              <strong>Count not saved</strong>
              {error} Your numbers are still on this phone.
            </div>
          )}
        </div>

        <div className="count-actions">
          <button ref={keepCountingRef} type="button" onClick={onClose} disabled={isSaving} className="btn ghost">
            Keep counting
          </button>
          <button
            ref={saveRef}
            type="button"
            onClick={onSave}
            disabled={isSaving || nothingCounted}
            className="btn grow"
          >
            {isSaving
              ? "Saving…"
              : error ? 'Try again'
              : mostlyUncounted ? `Save with ${uncounted.length} not counted`
              : 'Save count'}
          </button>
        </div>
      </div>
    </div>
  );
}
