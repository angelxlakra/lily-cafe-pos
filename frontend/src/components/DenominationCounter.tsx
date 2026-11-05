/**
 * DenominationCounter Component
 *
 * Touch-optimized component for counting Indian currency denominations.
 * Displays rows for ₹500 down to ₹10 notes, then ₹20, ₹10, ₹5, ₹2 and ₹1 coins.
 * Auto-calculates total from denomination counts.
 */

import { useState } from 'react';
import { CurrencyInr } from '@phosphor-icons/react';

// Each row: the API field suffix (opening_<key>) and its rupee value. Notes first, then coins.
export const DENOMINATION_ROWS = [
  { key: '500s', value: 500, coin: false },
  { key: '200s', value: 200, coin: false },
  { key: '100s', value: 100, coin: false },
  { key: '50s', value: 50, coin: false },
  { key: '20s', value: 20, coin: false },
  { key: '10s', value: 10, coin: false },
  { key: 'coin_20s', value: 20, coin: true },
  { key: 'coin_10s', value: 10, coin: true },
  { key: '5s', value: 5, coin: true },
  { key: '2s', value: 2, coin: true },
  { key: '1s', value: 1, coin: true },
] as const;

export type DenominationKey = (typeof DENOMINATION_ROWS)[number]['key'];
export type Denominations = Record<DenominationKey, number>;

interface DenominationCounterProps {
  denominations: Denominations;
  onChange: (denom: DenominationKey, count: number) => void;
  readOnly?: boolean;
}

export const emptyDenominations = (): Denominations =>
  Object.fromEntries(DENOMINATION_ROWS.map(r => [r.key, 0])) as Denominations;

export const denominationsTotal = (counts: Denominations) =>
  DENOMINATION_ROWS.reduce((sum, r) => sum + r.value * counts[r.key], 0);

/** The API's field names for one stage: { opening_500s: 2, …, opening_1s: 0 }. */
export const denominationFields = <S extends 'opening' | 'closing'>(stage: S, counts: Denominations) =>
  Object.fromEntries(DENOMINATION_ROWS.map(r => [`${stage}_${r.key}`, counts[r.key]])) as Record<`${S}_${DenominationKey}`, number>;

export default function DenominationCounter({
  denominations,
  onChange,
  readOnly = false
}: DenominationCounterProps) {
  const [focusedDenom, setFocusedDenom] = useState<DenominationKey | null>(null);

  const handleIncrement = (denom: DenominationKey, amount: number) => {
    const newCount = Math.max(0, denominations[denom] + amount);
    onChange(denom, newCount);
  };

  const handleDirectInput = (denom: DenominationKey, value: string) => {
    // Parse integer value
    const parsed = parseInt(value, 10);
    if (!isNaN(parsed) && parsed >= 0) {
      onChange(denom, parsed);
    } else if (value === '' || value === '0') {
      onChange(denom, 0);
    }
  };

  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(17rem,1fr))] gap-2">
      {DENOMINATION_ROWS.map(({ key: denom, value, coin }) => {
          const count = denominations[denom];
          const subtotal = count * value;
          const label = `₹${value} ${coin ? 'coin' : 'note'}`;
          const isFocused = focusedDenom === denom;

          return (
            <div
              key={denom}
              className={`
                border border-neutral-border rounded-lg p-2
                transition-all
                ${isFocused ? 'ring-2 ring-lily-green border-lily-green' : ''}
                ${count > 0 ? 'bg-lily-green/5 dark:bg-lily-green/10' : 'bg-off-white'}
              `}
            >
              {/* Denomination Label & Subtotal */}
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1">
                  <CurrencyInr size={16} weight="bold" className="text-lily-ink" />
                  <span className="text-sm font-bold text-neutral-text-dark dark:text-cream">
                    {value}
                  </span>
                  {coin && <span className="text-xs text-neutral-text-muted">coin</span>}
                </div>
                <div className={`text-xs font-mono font-bold ${count > 0 ? 'text-lily-ink' : 'text-neutral-text-muted'}`}>
                  ₹{subtotal.toLocaleString('en-IN')}
                </div>
              </div>

              {/* Count Controls */}
              <div className="flex items-center gap-1">
                {/* Decrement Buttons */}
                <button
                  onClick={() => handleIncrement(denom, -5)}
                  disabled={readOnly || count === 0}
                  className="touch-target-large btn-secondary px-1.5 text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                  type="button"
                  aria-label={`Decrease ${label} count by 5`}
                >
                  -5
                </button>
                <button
                  onClick={() => handleIncrement(denom, -1)}
                  disabled={readOnly || count === 0}
                  className="touch-target-large btn-secondary px-2 text-sm font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                  type="button"
                  aria-label={`Decrease ${label} count by 1`}
                >
                  -1
                </button>

                {/* Direct Input */}
                <input
                  type="number"
                  inputMode="numeric"
                  value={count === 0 ? '' : count}
                  placeholder="0"
                  onChange={(e) => handleDirectInput(denom, e.target.value)}
                  onFocus={(e) => {
                    setFocusedDenom(denom);
                    // Select all text on focus for easy replacement
                    e.target.select();
                  }}
                  onBlur={() => setFocusedDenom(null)}
                  disabled={readOnly}
                  className="
                    touch-target-large count-input-mobile
                    flex-1 max-w-[60px] text-center
                    input-field font-mono text-sm font-bold
                    focus:ring-2 focus:ring-lily-green focus:border-lily-green
                    disabled:opacity-50 disabled:cursor-not-allowed
                  "
                  min="0"
                  step="1"
                  aria-label={`Count of ${label}s`}
                />

                {/* Increment Buttons */}
                <button
                  onClick={() => handleIncrement(denom, 1)}
                  disabled={readOnly}
                  className="touch-target-large btn-secondary px-2 text-sm font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                  type="button"
                  aria-label={`Increase ${label} count by 1`}
                >
                  +1
                </button>
                <button
                  onClick={() => handleIncrement(denom, 5)}
                  disabled={readOnly}
                  className="touch-target-large btn-secondary px-1.5 text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                  type="button"
                  aria-label={`Increase ${label} count by 5`}
                >
                  +5
                </button>
              </div>
            </div>
          );
        })}
    </div>
  );
}
