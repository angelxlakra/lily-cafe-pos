/**
 * Tonight's Count: a focused, full-screen stock count for the counter admin
 * at close. One pinned bar on top (exit, where you are, progress), one line
 * per item, finished categories fold away, and the actions sit at the
 * bottom in thumb reach. Entries are kept on the phone until saved.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, CaretDown, Check, CheckCircle } from '@phosphor-icons/react';
import { inventoryApi } from '../api/inventory';
import CountRow from '../components/inventory/CountRow';
import CountReviewSheet from '../components/inventory/CountReviewSheet';
import LoadingSpinner from '../components/LoadingSpinner';
import { describeApiError } from '../utils/apiError';
import { useDialogFocus } from '../hooks/useDialogFocus';
import { bigDifferenceItems } from '../utils/countQuantity';
import { clearCountDraft, loadCountDraft, saveCountDraft, type CountEntries } from '../utils/countDraft';
import type { CountResult, CountSheetGroup } from '../types/inventory';

const groupKey = (group: CountSheetGroup) => String(group.category?.id ?? 'none');
const groupName = (group: CountSheetGroup) => group.category?.name ?? 'Uncategorized';
const formatTime = (date: Date) => date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });

export default function InventoryCountPage() {
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

  const goToItem = useCallback((itemId: number) => {
    setReviewing(false);
    // A finished category may be folded: open it, and wait for the unfold
    // (300ms) before scrolling so the row is where the scroll expects it.
    const group = groups?.find(g => g.items.some(item => item.id === itemId));
    const key = group ? groupKey(group) : null;
    const needsUnfold = !!key && !reopened.has(key) && group!.items.every(item => item.id in counts);
    if (needsUnfold) setReopened(previous => new Set(previous).add(key!));
    window.setTimeout(() => {
      const row = document.getElementById(`count-item-${itemId}`);
      row?.scrollIntoView({ block: 'center', behavior: 'smooth' });
      row?.querySelector<HTMLInputElement>('input')?.focus({ preventScroll: true });
    }, needsUnfold ? 320 : 0);
  }, [groups, reopened, counts]);

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
      <main className="min-h-dvh grid place-items-center bg-neutral-background px-6 py-10">
        <div className="w-full max-w-sm text-center animate-fade-in">
          <div className="mx-auto size-20 rounded-full bg-lily-green/20 grid place-items-center">
            <svg className="size-10 text-lily-ink" viewBox="0 0 24 24" fill="none" aria-hidden>
              <path
                d="M5 12.5l4.5 4.5L19 7.5"
                pathLength={1}
                strokeDasharray={1}
                stroke="currentColor"
                strokeWidth={2.5}
                strokeLinecap="round"
                strokeLinejoin="round"
                className="animate-draw"
              />
            </svg>
          </div>
          <h1 className="mt-5 font-heading text-neutral-text-dark">Count saved</h1>
          <p className="mt-2 text-neutral-text-body">Saved at {formatTime(at)} by {count.counted_by}.</p>
          <p className="mt-1 tabular-nums text-neutral-text-dark font-medium">
            {count.items_checked} checked · {count.items_changed} changed · {count.items_skipped} not counted
          </p>
          {count.emailed && <p className="mt-1 text-sm text-neutral-text-muted">A report is on its way to the owner by email.</p>}
          <button type="button" onClick={() => navigate('/admin/inventory')} className="btn-primary w-full mt-8">
            Done
          </button>
        </div>
      </main>
    );
  }

  const currentGroup = groups?.find(group => groupKey(group) === currentKey) ?? groups?.[0];
  const progress = items.length ? (countedTotal / items.length) * 100 : 0;

  return (
    <div className="min-h-dvh bg-neutral-background">
      <h1 className="sr-only">Tonight's count</h1>

      {/* The one pinned layer: exit, where you are, progress */}
      <header className="sticky top-0 z-20 bg-off-white border-b border-neutral-border">
        <div className="max-w-2xl mx-auto flex items-center gap-1 h-14 px-1">
          <button
            type="button"
            onClick={() => navigate('/admin/inventory')}
            className="h-12 px-3 inline-flex items-center gap-1.5 rounded-lg text-coffee-brown font-medium hover:bg-cream/60"
            aria-label={countedTotal > 0 ? 'Exit. Your count stays on this phone' : 'Exit'}
          >
            <ArrowLeft size={20} weight="bold" aria-hidden />
            Exit
          </button>
          <button
            type="button"
            onClick={() => setJumpOpen(true)}
            disabled={!groups?.length}
            aria-haspopup="dialog"
            className="flex-1 min-w-0 h-12 px-2 inline-flex items-center justify-center gap-1 rounded-lg text-neutral-text-dark font-semibold hover:bg-cream/60"
          >
            <span className="truncate">{currentGroup ? groupName(currentGroup) : "Tonight's count"}</span>
            <CaretDown size={16} weight="bold" className="shrink-0" aria-hidden />
            <span className="sr-only">. Jump to a category</span>
          </button>
          <span className="w-20 pr-3 text-right text-sm font-semibold tabular-nums text-neutral-text-body">
            {countedTotal}/{items.length}
            <span className="sr-only"> counted</span>
          </span>
        </div>
        <div
          className="h-1 bg-neutral-border/60"
          role="progressbar"
          aria-label="Items counted"
          aria-valuemin={0}
          aria-valuemax={items.length}
          aria-valuenow={countedTotal}
        >
          <div
            className="h-full origin-left bg-lily-green-deep transition-transform duration-300 ease-(--ease-settle)"
            style={{ transform: `scaleX(${progress / 100})` }}
          />
        </div>
      </header>

      <main className="max-w-2xl mx-auto pb-32">
        {isLoading && (
          <div className="py-16 flex justify-center text-neutral-text-muted gap-3">
            <LoadingSpinner /> Loading items…
          </div>
        )}

        {isError && (
          <div role="alert" className="m-4 card p-4">
            <p className="font-medium text-neutral-text-dark">Couldn't load the items to count.</p>
            <p className="text-sm mt-1">Check the Wi-Fi and try again. Anything you already entered is kept on this phone.</p>
            <button type="button" onClick={() => refetch()} className="btn-secondary mt-3">Try again</button>
          </div>
        )}

        {groups && groups.length === 0 && (
          <div className="m-4 card p-6 text-center">
            <p className="font-medium text-neutral-text-dark">No items to count yet.</p>
            <p className="text-sm mt-1">The owner can add them from the Items tab or import the WhatsApp checklist.</p>
          </div>
        )}

        {initialDraft && Object.keys(initialDraft.counts).length > 0 && countedTotal > 0 && (
          <p className="mx-3 mt-3 text-sm text-neutral-text-muted" role="status">
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
                className="scroll-mt-16 px-3 pt-5 pb-2"
              >
                <h2 id={`count-group-${key}`} className="font-heading text-xl! leading-tight! text-neutral-text-dark">
                  {done ? (
                    <button
                      type="button"
                      onClick={toggle}
                      aria-expanded={!folded}
                      className={`w-full min-h-12 flex items-center justify-between gap-3 text-left rounded-lg transition-colors duration-200 ${
                        folded ? 'bg-lily-green/10 px-3 py-2' : ''
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        <Check size={18} weight="bold" className="text-lily-ink shrink-0" aria-hidden />
                        {groupName(group)}
                      </span>
                      <span className="shrink-0 font-sans text-sm tracking-normal tabular-nums text-neutral-text-muted">
                        {counted.length - changed} checked · {changed} changed
                      </span>
                    </button>
                  ) : (
                    <span className="flex items-center justify-between gap-3">
                      {groupName(group)}
                      <span className="shrink-0 font-sans text-sm tracking-normal tabular-nums text-neutral-text-muted">
                        {counted.length}/{group.items.length}
                        <span className="sr-only"> counted</span>
                      </span>
                    </span>
                  )}
                </h2>
              </div>

              {/* Finished categories fold away; the grid-rows transition animates the height. */}
              <div
                className={`grid transition-[grid-template-rows] duration-300 ease-(--ease-settle) ${folded ? 'grid-rows-[0fr]' : 'grid-rows-[1fr]'}`}
                {...(folded ? { inert: '' } : {})}
              >
                <ul className="min-h-0 overflow-hidden bg-off-white border-y border-neutral-border/70">
                  {group.items.map(item => (
                    <CountRow key={item.id} item={item} counted={counts[item.id]} big={bigIds.has(item.id)} onChange={handleChange} />
                  ))}
                </ul>
              </div>
            </section>
          );
        })}
      </main>

      {/* Actions in thumb reach */}
      {items.length > 0 && (
        <div className="fixed bottom-0 inset-x-0 z-20 bg-off-white border-t border-neutral-border">
          <div className="max-w-2xl mx-auto flex gap-2 px-3 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
            {!allCounted && (
              <button type="button" onClick={goToNextUncounted} className="btn-secondary flex-1 whitespace-nowrap">
                Next uncounted
              </button>
            )}
            <button
              type="button"
              onClick={() => {
                saveMutation.reset();
                setReviewing(true);
              }}
              className="btn-primary flex-1 whitespace-nowrap inline-flex items-center justify-center gap-2"
            >
              {allCounted && <CheckCircle size={20} weight="fill" aria-hidden />}
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
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <div className="absolute inset-0 bg-black/50 animate-fade-in" onClick={onClose} aria-hidden />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Jump to a category"
        className="relative w-full max-w-lg max-h-[80dvh] overflow-y-auto bg-neutral-background rounded-t-2xl shadow-strong animate-slide-up pb-[env(safe-area-inset-bottom)]"
      >
        <ul ref={listRef} className="py-2">
          {groups.map(group => {
            const counted = group.items.filter(item => item.id in counts).length;
            const done = counted === group.items.length;
            return (
              <li key={groupKey(group)}>
                <button
                  type="button"
                  onClick={() => onPick(groupKey(group))}
                  className="w-full min-h-14 px-5 flex items-center justify-between gap-3 text-left hover:bg-cream/60"
                >
                  <span className="font-medium text-neutral-text-dark truncate">{groupName(group)}</span>
                  <span className={`shrink-0 text-sm tabular-nums inline-flex items-center gap-1 ${done ? 'text-lily-ink font-medium' : 'text-neutral-text-muted'}`}>
                    {done && <Check size={14} weight="bold" aria-hidden />}
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
