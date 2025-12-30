/**
 * ItemCountRow Component
 *
 * Touch-optimized row for daily inventory counting.
 * Mobile-first design with large touch targets (48px minimum).
 */

import { useState } from 'react';
import { Warning } from '@phosphor-icons/react';
import type { InventoryItem } from '../../types/inventory';

interface ItemCountRowProps {
  item: InventoryItem;
  count: number;
  onChange: (itemId: number, newCount: number) => void;
  isChanged: boolean;
}

export default function ItemCountRow({ item, count, onChange, isChanged }: ItemCountRowProps) {
  const [isFocused, setIsFocused] = useState(false);

  const handleIncrement = (amount: number) => {
    const newCount = Math.max(0, count + amount);
    onChange(item.id, newCount);
  };

  const handleDirectInput = (value: string) => {
    // Allow decimal input
    const parsed = parseFloat(value);
    if (!isNaN(parsed) && parsed >= 0) {
      onChange(item.id, parsed);
    } else if (value === '' || value === '0') {
      onChange(item.id, 0);
    }
  };

  return (
    <div
      className={`
        border-b border-neutral-border last:border-b-0
        transition-colors
        ${isChanged ? 'bg-lily-green/5 dark:bg-lily-green/10' : ''}
        ${isFocused ? 'bg-neutral-background/50' : ''}
      `}
    >
      <div className="p-4">
        {/* Item Name & Unit */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h4 className="font-medium text-neutral-text-dark dark:text-cream">
              {item.name}
            </h4>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm text-neutral-text-muted">
                Unit: {item.unit}
              </span>
              {item.is_low_stock && (
                <span className="inline-flex items-center gap-1 text-xs text-error">
                  <Warning size={12} weight="fill" />
                  Low Stock
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Current vs New Quantity */}
        <div className="flex items-center gap-2 mb-3 text-sm">
          <span className="text-neutral-text-muted">
            Current: <span className="font-mono font-medium text-neutral-text-dark dark:text-cream">{item.current_quantity}</span>
          </span>
          {isChanged && (
            <>
              <span className="text-neutral-text-muted">→</span>
              <span className="text-lily-green dark:text-lily-green-light">
                New: <span className="font-mono font-bold">{count}</span>
              </span>
            </>
          )}
        </div>

        {/* Count Controls - Touch Optimized */}
        <div className="flex items-center gap-2">
          {/* Decrement Buttons */}
          <button
            onClick={() => handleIncrement(-5)}
            className="touch-target-large btn-secondary px-3 text-sm font-bold"
            type="button"
          >
            -5
          </button>
          <button
            onClick={() => handleIncrement(-1)}
            className="touch-target-large btn-secondary px-4 text-base font-bold"
            type="button"
          >
            -1
          </button>

          {/* Direct Input */}
          <input
            type="number"
            inputMode="decimal"
            value={count}
            onChange={(e) => handleDirectInput(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            className="
              touch-target-large count-input-mobile
              flex-1 max-w-[100px] text-center
              input-field font-mono text-lg font-bold
              focus:ring-2 focus:ring-lily-green focus:border-lily-green
            "
            step="0.01"
            min="0"
          />

          {/* Increment Buttons */}
          <button
            onClick={() => handleIncrement(1)}
            className="touch-target-large btn-secondary px-4 text-base font-bold"
            type="button"
          >
            +1
          </button>
          <button
            onClick={() => handleIncrement(5)}
            className="touch-target-large btn-secondary px-3 text-sm font-bold"
            type="button"
          >
            +5
          </button>
        </div>

        {/* Change Indicator */}
        {isChanged && (
          <div className="mt-3 text-xs text-lily-green dark:text-lily-green-light font-medium">
            Changed: {count > item.current_quantity ? '+' : ''}{(count - item.current_quantity).toFixed(2)} {item.unit}
          </div>
        )}
      </div>
    </div>
  );
}
