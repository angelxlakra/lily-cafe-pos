/**
 * DenominationCounter Component
 *
 * Touch-optimized component for counting Indian currency denominations.
 * Displays rows for ₹500, ₹200, ₹100, ₹50, ₹20, ₹10 notes.
 * Auto-calculates total from denomination counts.
 */

import { useState } from 'react';
import { CurrencyInr } from '@phosphor-icons/react';

export interface Denominations {
  500: number;
  200: number;
  100: number;
  50: number;
  20: number;
  10: number;
}

interface DenominationCounterProps {
  denominations: Denominations;
  onChange: (denom: keyof Denominations, count: number) => void;
  readOnly?: boolean;
}

// Define denominations in descending order
const DENOMINATION_VALUES: (keyof Denominations)[] = [500, 200, 100, 50, 20, 10];

export default function DenominationCounter({
  denominations,
  onChange,
  readOnly = false
}: DenominationCounterProps) {
  const [focusedDenom, setFocusedDenom] = useState<keyof Denominations | null>(null);

  const handleIncrement = (denom: keyof Denominations, amount: number) => {
    const newCount = Math.max(0, denominations[denom] + amount);
    onChange(denom, newCount);
  };

  const handleDirectInput = (denom: keyof Denominations, value: string) => {
    // Parse integer value
    const parsed = parseInt(value, 10);
    if (!isNaN(parsed) && parsed >= 0) {
      onChange(denom, parsed);
    } else if (value === '' || value === '0') {
      onChange(denom, 0);
    }
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
      {DENOMINATION_VALUES.map((denom) => {
          const count = denominations[denom];
          const subtotal = count * denom;
          const isFocused = focusedDenom === denom;

          return (
            <div
              key={denom}
              className={`
                border border-neutral-border rounded-lg p-2
                transition-all
                ${isFocused ? 'ring-2 ring-lily-green border-lily-green' : ''}
                ${count > 0 ? 'bg-lily-green/5 dark:bg-lily-green/10' : 'bg-white dark:bg-neutral-900'}
              `}
            >
              {/* Denomination Label & Subtotal */}
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1">
                  <CurrencyInr size={16} weight="bold" className="text-lily-green" />
                  <span className="text-sm font-bold text-neutral-text-dark dark:text-cream">
                    {denom}
                  </span>
                </div>
                <div className={`text-xs font-mono font-bold ${count > 0 ? 'text-lily-green dark:text-lily-green-light' : 'text-neutral-text-muted'}`}>
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
                  aria-label={`Decrease ₹${denom} count by 5`}
                >
                  -5
                </button>
                <button
                  onClick={() => handleIncrement(denom, -1)}
                  disabled={readOnly || count === 0}
                  className="touch-target-large btn-secondary px-2 text-sm font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                  type="button"
                  aria-label={`Decrease ₹${denom} count by 1`}
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
                  aria-label={`Count of ₹${denom} notes`}
                />

                {/* Increment Buttons */}
                <button
                  onClick={() => handleIncrement(denom, 1)}
                  disabled={readOnly}
                  className="touch-target-large btn-secondary px-2 text-sm font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                  type="button"
                  aria-label={`Increase ₹${denom} count by 1`}
                >
                  +1
                </button>
                <button
                  onClick={() => handleIncrement(denom, 5)}
                  disabled={readOnly}
                  className="touch-target-large btn-secondary px-1.5 text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                  type="button"
                  aria-label={`Increase ₹${denom} count by 5`}
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
