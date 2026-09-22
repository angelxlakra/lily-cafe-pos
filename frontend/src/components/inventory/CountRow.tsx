/**
 * One item in the nightly count: name on the left, controls on the right
 * where a right thumb reaches. ✓ confirms the shelf matches the system;
 * − / + / typing records a different number.
 */

import { memo, useRef, useState } from 'react';
import { Check, Minus, Plus, Warning } from '@phosphor-icons/react';
import type { InventoryItem } from '../../types/inventory';
import { formatQty, isBigDifference, parseQty } from '../../utils/countQuantity';

interface CountRowProps {
  item: InventoryItem;
  /** Counted quantity, or undefined if not counted yet. */
  counted: number | undefined;
  onChange: (itemId: number, counted: number | null) => void;
  /** Adds delta to the latest count (or the system quantity), never below 0. */
  onStep: (itemId: number, delta: number, system: number) => void;
}

/** Click steps once; holding repeats (keyboard users get the click path). */
function useHoldToRepeat(step: () => void) {
  const timers = useRef<{ delay?: number; repeat?: number }>({});
  const repeated = useRef(false);

  const stop = () => {
    window.clearTimeout(timers.current.delay);
    window.clearInterval(timers.current.repeat);
  };

  return {
    onPointerDown: () => {
      repeated.current = false;
      stop();
      timers.current.delay = window.setTimeout(() => {
        repeated.current = true;
        step();
        timers.current.repeat = window.setInterval(step, 90);
      }, 400);
    },
    onPointerUp: stop,
    onPointerLeave: stop,
    onPointerCancel: stop,
    onClick: () => {
      if (!repeated.current) step();
      repeated.current = false;
    },
  };
}

function CountRow({ item, counted, onChange, onStep }: CountRowProps) {
  const system = Number(item.current_quantity);
  const status = counted === undefined ? 'untouched' : counted === system ? 'checked' : 'changed';
  const [draftText, setDraftText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const errorId = `count-error-${item.id}`;
  const cancelTyping = useRef(false);

  // Stepping goes through a functional state update in the parent, so fast
  // taps and hold-to-repeat never read a stale value.
  const stepBy = (delta: number) => {
    setError(null);
    onStep(item.id, delta, system);
  };
  const minus = useHoldToRepeat(() => stepBy(-1));
  const plus = useHoldToRepeat(() => stepBy(1));

  const commitTyped = () => {
    if (draftText === null) return;
    if (cancelTyping.current) {
      cancelTyping.current = false;
      setDraftText(null);
      return;
    }
    const parsed = parseQty(draftText);
    setDraftText(null);
    if (draftText.trim() === '') {
      setError(null);
      onChange(item.id, null);
    } else if (parsed === null) {
      setError('Enter a number like 3, 2.5 or 1½.');
    } else if (parsed < 0) {
      setError("Stock can't be below 0. Enter 0 if it's run out.");
    } else {
      setError(null);
      onChange(item.id, parsed);
    }
  };

  const diff = counted === undefined ? 0 : counted - system;
  const big = status === 'changed' && isBigDifference(system, counted!);

  return (
    <li
      id={`count-item-${item.id}`}
      className={`scroll-mt-20 border-b border-neutral-border/70 transition-colors duration-200 ${
        status === 'checked' ? 'bg-lily-green/10' : status === 'changed' ? 'bg-cream/50' : ''
      }`}
    >
      <div className="flex items-center gap-2 px-3 py-2 min-h-16">
        <div className="flex-1 min-w-0">
          <div className="font-medium leading-snug text-neutral-text-dark line-clamp-2 break-words">
            {item.name}
          </div>
          <div className="mt-0.5 text-xs tabular-nums text-neutral-text-muted flex items-center gap-1">
            {status === 'untouched' && <>System {formatQty(system)} {item.unit}</>}
            {status === 'checked' && <>Matches · {formatQty(system)} {item.unit}</>}
            {status === 'changed' && (
              <>
                {big && <Warning size={14} weight="fill" className="text-[#b45309] shrink-0" aria-hidden />}
                <span className={big ? 'font-semibold text-[#b45309] dark:text-warning' : undefined}>
                  Was {formatQty(system)} · {diff > 0 ? '+' : '−'}{formatQty(Math.abs(diff))} {item.unit}
                  {big && <span className="sr-only"> (big difference)</span>}
                </span>
              </>
            )}
          </div>
          {error && (
            <div id={errorId} role="alert" className="mt-1 text-xs font-medium text-[#c0392b] dark:text-error">
              {error}
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={() => {
            setError(null);
            onChange(item.id, status === 'checked' ? null : system);
          }}
          aria-pressed={status === 'checked'}
          aria-label={`${item.name} matches ${formatQty(system)} ${item.unit}`}
          className={`size-12 shrink-0 grid place-items-center rounded-lg border transition-colors duration-[var(--dur-press)] ${
            status === 'checked'
              ? 'bg-lily-green-deep border-lily-green-deep text-white'
              : 'border-neutral-border text-neutral-text-muted hover:border-lily-green-deep hover:text-lily-green-deep'
          }`}
        >
          <Check size={22} weight="bold" aria-hidden />
        </button>

        <div className="flex items-center shrink-0 rounded-lg border border-neutral-border bg-off-white">
          <button
            type="button"
            {...minus}
            aria-label={`One less ${item.name}`}
            className="size-12 grid place-items-center text-coffee-brown active:bg-cream rounded-l-lg select-none touch-manipulation"
          >
            <Minus size={18} weight="bold" aria-hidden />
          </button>
          <input
            type="text"
            inputMode="decimal"
            enterKeyHint="done"
            autoComplete="off"
            value={draftText ?? (counted === undefined ? '' : formatQty(counted))}
            placeholder={formatQty(system)}
            onFocus={event => {
              setDraftText(counted === undefined ? '' : formatQty(counted));
              event.currentTarget.select();
            }}
            onChange={event => setDraftText(event.target.value)}
            onBlur={commitTyped}
            onKeyDown={event => {
              if (event.key === 'Enter') {
                commitTyped();
                event.currentTarget.blur();
              }
              if (event.key === 'Escape') {
                cancelTyping.current = true;
                event.currentTarget.blur();
              }
            }}
            aria-label={`Count for ${item.name}, in ${item.unit}`}
            aria-invalid={error !== null}
            aria-describedby={error ? errorId : undefined}
            className="w-14 h-12 bg-transparent text-center text-lg font-semibold tabular-nums text-neutral-text-dark placeholder:text-neutral-text-muted placeholder:font-normal focus:outline-none focus:bg-white dark:focus:bg-neutral-background"
          />
          <button
            type="button"
            {...plus}
            aria-label={`One more ${item.name}`}
            className="size-12 grid place-items-center text-coffee-brown active:bg-cream rounded-r-lg select-none touch-manipulation"
          >
            <Plus size={18} weight="bold" aria-hidden />
          </button>
        </div>
      </div>
    </li>
  );
}

export default memo(CountRow);
