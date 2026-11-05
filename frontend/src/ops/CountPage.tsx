/**
 * Tonight's Count: a focused, full-screen stock count for the counter admin
 * at close. One pinned bar on top (exit, where you are, progress), one line
 * per item, finished categories fold away, and the actions sit at the
 * bottom in thumb reach. Entries are kept on the phone until saved.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { inventoryApi } from '../api/inventory';
import CountRow from './CountRow';
import CountReviewSheet from './CountReviewSheet';
import { describeApiError } from '../utils/apiError';
import { useDialogFocus } from '../hooks/useDialogFocus';
import { bigDifferenceItems, isPresence } from '../utils/countQuantity';
import { clearCountDraft, loadCountDraft, saveCountDraft, type CountEntries } from '../utils/countDraft';
import type { CountResult, CountSheetGroup } from '../types/inventory';
import './ops.css';

const groupKey = (group: CountSheetGroup) => String(group.category?.id ?? 'none');
const groupName = (group: CountSheetGroup) => group.category?.name ?? 'Uncategorized';
/** Longer than a double tap, and than a finished category's 300ms fold, so the scroll lands true. */
const ADVANCE_DELAY_MS = 350;
const formatTime = (date: Date) => date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });

export default function CountPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: groups, isLoading, isError, refetch } = useQuery({
    queryKey: ['inventory', 'count-sheet'],
    queryFn: inventoryApi.getCountSheet,
  });

  const [initialDraft] = useState(loadCountDraft);
  const startedAt = useRef(initialDraft?.startedAt ?? Date.now());
  const [counts, setCounts] = useState<CountEntries>(() => initialDraft?.counts ?? {});
  const draftStored = useRef(true);
  const [reopened, setReopened] = useState<Set<string>>(new Set());
  const [reviewing, setReviewing] = useState(false);
  const [jumpOpen, setJumpOpen] = useState(false);
  const [result, setResult] = useState<{ count: CountResult; at: Date } | null>(null);

  useEffect(() => {
    if (!result) draftStored.current = saveCountDraft(counts, startedAt.current);
  }, [counts, result]);

  const items = useMemo(() => groups?.flatMap(group => group.items) ?? [], [groups]);
  // A draft kept from before the owner made an item yes/no may hold ½ for it: read as have it / out.
  useEffect(() => {
    setCounts(previous => {
      const stale = items.filter(item => isPresence(item) && item.id in previous && ![0, 1].includes(previous[item.id]));
      if (stale.length === 0) return previous;
      const next = { ...previous };
      for (const item of stale) next[item.id] = next[item.id] > 0 ? 1 : 0;
      return next;
    });
  }, [items]);
  const countedTotal = items.filter(item => item.id in counts).length;
  const allCounted = items.length > 0 && countedTotal === items.length;
  // Ranked across the whole count, so the row icons and the review sheet flag the same few items.
  const bigDifferences = useMemo(() => bigDifferenceItems(items, counts), [items, counts]);
  const bigIds = useMemo(() => new Set(bigDifferences.map(item => item.id)), [bigDifferences]);

  // Only nag on leave when the draft couldn't be kept on this device.
  useEffect(() => {
    if (countedTotal === 0 || result) return;
    const warn = (event: BeforeUnloadEvent) => {
      if (draftStored.current) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [countedTotal, result]);

  const handleChange = useCallback((itemId: number, value: number | null) => {
    setCounts(previous => {
      const next = { ...previous };
      if (value === null) delete next[itemId];
      else next[itemId] = value;
      return next;
    });
  }, []);

  // Which category the top bar names: the last header scrolled past it.
  const headerRefs = useRef(new Map<string, HTMLElement>());
  const [currentKey, setCurrentKey] = useState<string | null>(null);
  useEffect(() => {
    let frame = 0;
    const update = () => {
      frame = 0;
      let current: string | null = null;
      headerRefs.current.forEach((element, key) => {
        if (element.getBoundingClientRect().top <= 72) current = key;
      });
      setCurrentKey(current);
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      cancelAnimationFrame(frame);
    };
  }, [groups]);

  // Read through refs so goToItem, and the rows' onAnswer, stay stable across
  // taps; otherwise every answer would re-render every memoized row.
  const countsRef = useRef(counts);
  countsRef.current = counts;
  const reopenedRef = useRef(reopened);
  reopenedRef.current = reopened;

  const isFolded = useCallback((group: CountSheetGroup, entries: CountEntries) =>
    !reopenedRef.current.has(groupKey(group)) && group.items.every(item => item.id in entries), []);

  const goToItem = useCallback((itemId: number) => {
    setReviewing(false);
    // A finished category may be folded: open it, and wait for the unfold
    // (300ms) before scrolling so the row is where the scroll expects it.
    const group = groups?.find(g => g.items.some(item => item.id === itemId));
    const needsUnfold = !!group && isFolded(group, countsRef.current);
    if (needsUnfold) setReopened(previous => new Set(previous).add(groupKey(group!)));
    window.setTimeout(() => {
      const row = document.getElementById(`count-item-${itemId}`);
      row?.scrollIntoView({ block: 'center', behavior: 'smooth' });
      // The row's box, or a yes/no row's Have it button.
      row?.querySelector<HTMLElement>('[data-count-control]')?.focus({ preventScroll: true });
    }, needsUnfold ? 320 : 0);
  }, [groups, isFolded]);

  // A yes/no answer is one tap, so it moves on to the next uncounted row, but
  // not instantly: scrolling under a double tap would put the next row's
  // button under the second tap and answer it. Waiting lets that second tap
  // land on the same button, un-answer the row, and cancel the move.
  const pendingAdvance = useRef<number>();
  useEffect(() => () => window.clearTimeout(pendingAdvance.current), []);
  const handleAnswer = useCallback((itemId: number, value: number | null) => {
    window.clearTimeout(pendingAdvance.current);
    handleChange(itemId, value);
    if (value === null) return;
    pendingAdvance.current = window.setTimeout(() => {
      const answered = countsRef.current;
      if (!(itemId in answered)) return;
      const index = items.findIndex(item => item.id === itemId);
      const next = [...items.slice(index + 1), ...items.slice(0, index)].find(item => !(item.id in answered));
      if (next) goToItem(next.id);
    }, ADVANCE_DELAY_MS);
  }, [items, handleChange, goToItem]);

  const goToNextUncounted = () => {
    const next = items.find(item => !(item.id in counts));
    if (next) goToItem(next.id);
  };

  const goToGroup = (key: string) => {
    setJumpOpen(false);
    headerRefs.current.get(key)?.scrollIntoView({ block: 'start', behavior: 'smooth' });
  };

  const saveMutation = useMutation({
    mutationFn: () =>
      inventoryApi.saveCount(items.map(item => ({ item_id: item.id, counted_quantity: counts[item.id] ?? null }))),
    onSuccess: count => {
      clearCountDraft();
      setResult({ count, at: new Date() });
      setReviewing(false);
      window.scrollTo(0, 0);
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });

  if (result) {
    const { count, at } = result;
    return (
      <main className="ops ops-count ops-count-done">
        <div className="done-card">
          <div className="done-mark" aria-hidden>✓</div>
          <h1>Count saved</h1>
          <p>Saved at {formatTime(at)} by {count.counted_by}.</p>
          <p><b>{count.items_checked} checked · {count.items_changed} changed · {count.items_skipped} not counted</b></p>
          {count.emailed && <p className="muted">A report is on its way to the owner by email.</p>}
          {/* Low stock exists to drive ordering: the count ends on the order messages. */}
          <button type="button" onClick={() => navigate('/admin/ops/order')} className="btn">
            Send tonight's order
          </button>
          <button type="button" onClick={() => navigate('/admin/ops/inventory')} className="btn ghost">
            Done
          </button>
        </div>
      </main>
    );
  }

  const currentGroup = groups?.find(group => groupKey(group) === currentKey) ?? groups?.[0];
  const progress = items.length ? (countedTotal / items.length) * 100 : 0;

  return (
    <div className="ops ops-count">
      <h1 className="sr-only">Tonight's count</h1>

      {/* The one pinned layer: exit, where you are, progress */}
      <header className="count-top">
        <div className="count-top-row">
          <button
            type="button"
            onClick={() => navigate('/admin/ops/inventory')}
            className="count-exit"
            aria-label={countedTotal > 0 ? 'Exit. Your count stays on this phone' : 'Exit'}
          >
            <span aria-hidden>←</span> Exit
          </button>
          <button
            type="button"
            onClick={() => setJumpOpen(true)}
            disabled={!groups?.length}
            aria-haspopup="dialog"
            className="count-jump"
          >
            <span className="truncate">{currentGroup ? groupName(currentGroup) : "Tonight's count"}</span>
            <span aria-hidden>▾</span>
            <span className="sr-only">. Jump to a category</span>
          </button>
          <span className="count-prog">
            {countedTotal}/{items.length}
            <span className="sr-only"> counted</span>
          </span>
        </div>
        <div
          className="count-bar"
          role="progressbar"
          aria-label="Items counted"
          aria-valuemin={0}
          aria-valuemax={items.length}
          aria-valuenow={countedTotal}
        >
          <div style={{ transform: `scaleX(${progress / 100})` }} />
        </div>
      </header>

      <main className="count-main">
        {isLoading && (
          <p className="muted count-pad">Loading items…</p>
        )}

        {isError && (
          <div role="alert" className="count-card">
            <p><b>Couldn't load the items to count.</b></p>
            <p className="muted">Check the Wi-Fi and try again. Anything you already entered is kept on this phone.</p>
            <button type="button" onClick={() => refetch()} className="btn ghost">Try again</button>
          </div>
        )}

        {groups && groups.length === 0 && (
          <div className="count-card">
            <p><b>No items to count yet.</b></p>
            <p className="muted">The owner can add them from Setup or import the WhatsApp checklist.</p>
          </div>
        )}

        {initialDraft && Object.keys(initialDraft.counts).length > 0 && countedTotal > 0 && (
          <p className="muted count-pad" role="status">
            Picked up where you left off. Started at {formatTime(new Date(initialDraft.startedAt))}.
          </p>
        )}

        {groups?.map(group => {
          const key = groupKey(group);
          const counted = group.items.filter(item => item.id in counts);
          const changed = counted.filter(item => counts[item.id] !== Number(item.current_quantity)).length;
          const done = counted.length === group.items.length;
          const folded = done && !reopened.has(key);
          const toggle = () =>
            setReopened(previous => {
              const next = new Set(previous);
              if (next.has(key)) next.delete(key);
              else next.add(key);
              return next;
            });

          return (
            <section key={key} aria-labelledby={`count-group-${key}`}>
              <div
                ref={element => {
                  if (element) headerRefs.current.set(key, element);
                  else headerRefs.current.delete(key);
                }}
                className="count-head"
              >
                <h2 id={`count-group-${key}`}>
                  {done ? (
                    <button
                      type="button"
                      onClick={toggle}
                      aria-expanded={!folded}
                      className={`count-fold${folded ? ' folded' : ''}`}
                    >
                      <span>
                        <span aria-hidden>✓ </span>
                        {groupName(group)}
                      </span>
                      <span className="tally">
                        {counted.length - changed} checked · {changed} changed
                      </span>
                    </button>
                  ) : (
                    <span className="count-fold plain">
                      {groupName(group)}
                      <span className="tally">
                        {counted.length}/{group.items.length}
                        <span className="sr-only"> counted</span>
                      </span>
                    </span>
                  )}
                </h2>
              </div>

              {/* Finished categories fold away; the grid-rows transition animates the height. */}
              <div
                className={`count-fold-box${folded ? ' folded' : ''}`}
                {...(folded ? { inert: '' } : {})}
              >
                <ul className="count-items">
                  {group.items.map(item => (
                    <CountRow
                      key={item.id}
                      item={item}
                      counted={counts[item.id]}
                      big={bigIds.has(item.id)}
                      onChange={handleChange}
                      onAnswer={handleAnswer}
                    />
                  ))}
                </ul>
              </div>
            </section>
          );
        })}
      </main>

      {/* Actions in thumb reach */}
      {items.length > 0 && (
        <div className="count-foot">
          <div className="count-foot-row">
            {!allCounted && (
              <button type="button" onClick={goToNextUncounted} className="btn ghost grow">
                Next uncounted
              </button>
            )}
            <button
              type="button"
              onClick={() => {
                saveMutation.reset();
                setReviewing(true);
              }}
              className="btn grow"
            >
              {allCounted ? 'Review & save' : `Review · ${countedTotal}/${items.length}`}
            </button>
          </div>
        </div>
      )}

      {jumpOpen && groups && (
        <CategoryJumpSheet
          groups={groups}
          counts={counts}
          onPick={goToGroup}
          onClose={() => setJumpOpen(false)}
        />
      )}

      {reviewing && (
        <CountReviewSheet
          items={items}
          counts={counts}
          bigDifferences={bigDifferences}
          isSaving={saveMutation.isPending}
          error={saveMutation.isError ? describeApiError(saveMutation.error) : null}
          onSave={() => saveMutation.mutate()}
          onClose={() => setReviewing(false)}
          onGoToItem={goToItem}
        />
      )}
    </div>
  );
}

function CategoryJumpSheet({
  groups, counts, onPick, onClose,
}: {
  groups: CountSheetGroup[];
  counts: CountEntries;
  onPick: (key: string) => void;
  onClose: () => void;
}) {
  const listRef = useRef<HTMLUListElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocus(dialogRef, onClose);
  useEffect(() => {
    listRef.current?.querySelector('button')?.focus();
  }, []);

  return (
    <div className="count-sheet-wrap">
      <div className="count-scrim" onClick={onClose} aria-hidden />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Jump to a category"
        className="count-sheet jump"
      >
        <ul ref={listRef} className="count-jump-list">
          {groups.map(group => {
            const counted = group.items.filter(item => item.id in counts).length;
            const done = counted === group.items.length;
            return (
              <li key={groupKey(group)}>
                <button
                  type="button"
                  onClick={() => onPick(groupKey(group))}
                  className="count-pick"
                >
                  <span className="nm">{groupName(group)}</span>
                  <span className={`val${done ? ' done' : ''}`}>
                    {done && <span aria-hidden>✓ </span>}
                    {counted}/{group.items.length}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
