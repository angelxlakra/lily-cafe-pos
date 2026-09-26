/**
 * One item in the nightly count: name on the left, one control on the right
 * where a right thumb reaches. The item decides the control, never the
 * counter: a number item gets a box (placeholder = system quantity, unit
 * beside it); a yes/no item gets two buttons, Out and Have it.
 */

import { memo, useRef, useState } from 'react';
import { Warning } from '@phosphor-icons/react';
import type { InventoryItem } from '../../types/inventory';
import { formatQty, hadIt, haveIt, isPresence, parseQty } from '../../utils/countQuantity';

interface CountRowProps {
  item: InventoryItem;
  /** Counted quantity, or undefined if not counted yet. */
  counted: number | undefined;
  /** One of the few changes flagged for a second look across the whole count. */
  big: boolean;
  onChange: (itemId: number, counted: number | null) => void;
  /** A yes/no answer (or null to un-answer); the page moves on to the next uncounted row. */
  onAnswer: (itemId: number, counted: number | null) => void;
}

function CountRow({ item, counted, big, onChange, onAnswer }: CountRowProps) {
  return isPresence(item)
    ? <PresenceRow item={item} counted={counted} onAnswer={onAnswer} />
    : <NumberRow item={item} counted={counted} big={big} onChange={onChange} />;
}

const rowTone = (status: 'untouched' | 'checked' | 'changed') =>
  status === 'checked' ? 'bg-lily-green/10' : status === 'changed' ? 'bg-cream/50' : '';

function NumberRow({ item, counted, big: flagged, onChange }: Omit<CountRowProps, 'onAnswer'>) {
  const system = Number(item.current_quantity);
  const status = counted === undefined ? 'untouched' : counted === system ? 'checked' : 'changed';
  const [draftText, setDraftText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const errorId = `count-error-${item.id}`;
  const cancelTyping = useRef(false);

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
  const big = status === 'changed' && flagged;

  return (
    <li
      id={`count-item-${item.id}`}
      className={`scroll-mt-20 border-b border-neutral-border/70 transition-colors duration-200 ${rowTone(status)}`}
    >
      <div className="flex items-center gap-2 px-2.5 py-2 min-h-16">
        <div className="flex-1 min-w-0">
          <div className="font-medium leading-snug text-neutral-text-dark line-clamp-3 break-words">
            {item.name}
          </div>
          <div className="mt-0.5 text-[0.8125rem] leading-snug tabular-nums text-neutral-text-muted flex items-center gap-1">
            {status === 'untouched' && <>System {formatQty(system)} {item.unit}</>}
            {status === 'checked' && <>Matches · {formatQty(system)} {item.unit}</>}
            {status === 'changed' && (
              <>
                {big && <Warning size={14} weight="fill" className="text-warning shrink-0" aria-hidden />}
                <span className={big ? 'font-semibold text-warning' : undefined}>
                  Was {formatQty(system)} · {diff > 0 ? '+' : '−'}{formatQty(Math.abs(diff))} {item.unit}
                  {big && <span className="sr-only"> (big difference)</span>}
                </span>
              </>
            )}
          </div>
          {error && (
            <div id={errorId} role="alert" className="mt-1 text-xs font-medium text-error">
              {error}
            </div>
          )}
        </div>

        <div className="shrink-0 flex items-center gap-2">
          <input
            data-count-control
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
            className="w-24 h-12 rounded-lg border border-neutral-border bg-off-white text-center text-lg font-semibold tabular-nums text-neutral-text-dark placeholder:text-neutral-text-muted placeholder:font-normal focus:outline-none focus:border-lily-ink focus:bg-white dark:focus:bg-neutral-background"
          />
          <span className="w-10 text-[0.8125rem] text-neutral-text-muted">{item.unit}</span>
        </div>
      </div>
      {/* Says whether the typed number matches the system, which the box alone doesn't. */}
      <span className="sr-only" aria-live="polite">
        {status === 'untouched' ? '' : status === 'checked'
          ? `${item.name} matches, ${formatQty(system)}`
          : `${item.name} ${formatQty(counted!)}, ${diff > 0 ? 'more' : 'less'} than system by ${formatQty(Math.abs(diff))}`}
      </span>
    </li>
  );
}

/**
 * A yes/no item: same height and left column as a number row, no unit, no
 * keyboard. Two 68×48 buttons fill the same 144px slot, Have it on the right
 * because it is the common answer. Tapping the filled one again un-answers,
 * so a stray double tap leaves the row visibly blank rather than answered.
 */
function PresenceRow({ item, counted, onAnswer }: Pick<CountRowProps, 'item' | 'counted' | 'onAnswer'>) {
  const system = Number(item.current_quantity) > 0 ? 1 : 0;
  const status = counted === undefined ? 'untouched' : counted === system ? 'checked' : 'changed';

  const choice = (label: string, value: 0 | 1) => {
    const chosen = counted === value;
    return (
      <button
        type="button"
        aria-pressed={chosen}
        // "Next uncounted" lands here: the common answer.
        {...(value === 1 ? { 'data-count-control': '' } : {})}
        onClick={() => onAnswer(item.id, chosen ? null : value)}
        className={`w-[68px] h-12 touch-manipulation rounded-lg border text-sm font-semibold leading-tight transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-lily-ink ${
          !chosen
            ? 'border-neutral-border bg-off-white text-neutral-text-body'
            : status === 'checked'
              ? 'border-lily-ink bg-lily-green/35 text-neutral-text-dark'
              : 'border-coffee-brown bg-cream text-neutral-text-dark'
        }`}
      >
        {label}
      </button>
    );
  };

  return (
    <li
      id={`count-item-${item.id}`}
      className={`scroll-mt-20 border-b border-neutral-border/70 transition-colors duration-200 ${rowTone(status)}`}
    >
      <div className="flex items-center gap-2 px-2.5 py-2 min-h-16">
        <div className="flex-1 min-w-0">
          <div id={`count-name-${item.id}`} className="font-medium leading-snug text-neutral-text-dark line-clamp-3 break-words">
            {item.name}
          </div>
          <div className="mt-0.5 text-[0.8125rem] leading-snug text-neutral-text-muted">
            {status === 'untouched' && <>Last count: {hadIt(system)}</>}
            {status === 'checked' && <>Same · {hadIt(system)}</>}
            {status === 'changed' && <>Was {hadIt(system)} · now {haveIt(counted!)}</>}
          </div>
        </div>

        <div role="group" aria-labelledby={`count-name-${item.id}`} className="shrink-0 w-36 flex items-center gap-2">
          {choice('Out', 0)}
          {choice('Have it', 1)}
        </div>
      </div>
      <span className="sr-only" aria-live="polite">
        {status === 'untouched' ? '' : status === 'checked'
          ? `${item.name}: ${haveIt(counted!)}, same as last count`
          : `${item.name}: ${haveIt(counted!)}, was ${hadIt(system)}`}
      </span>
    </li>
  );
}

export default memo(CountRow);
