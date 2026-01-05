/**
 * CategorySection Component
 *
 * Collapsible section grouping inventory items by category.
 * Sticky header for easy navigation while scrolling.
 */

import { useState } from 'react';
import { CaretDown, CaretRight } from '@phosphor-icons/react';
import type { InventoryItem } from '../../types/inventory';
import ItemCountRow from './ItemCountRow';

interface CategorySectionProps {
  categoryName: string;
  items: InventoryItem[];
  counts: Record<number, number | null>;
  changedItems: Set<number>;
  onCountChange: (itemId: number, newCount: number | null) => void;
  defaultExpanded?: boolean;
}

export default function CategorySection({
  categoryName,
  items,
  counts,
  changedItems,
  onCountChange,
  defaultExpanded = true
}: CategorySectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  // Calculate progress
  const countedItems = items.filter(item => changedItems.has(item.id)).length;
  const totalItems = items.length;
  const progressPercentage = totalItems > 0 ? (countedItems / totalItems) * 100 : 0;

  return (
    <div className="mb-4">
      {/* Sticky Category Header */}
      <div
        className="sticky-category-header z-10 bg-coffee-brown dark:bg-coffee-dark backdrop-blur-sm"
        style={{ top: 0 }}
      >
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between p-4 text-left hover:bg-coffee-light/10 transition-colors"
          type="button"
        >
          <div className="flex items-center gap-3 flex-1">
            {/* Expand/Collapse Icon */}
            <span className="text-white">
              {isExpanded ? <CaretDown size={20} weight="bold" /> : <CaretRight size={20} weight="bold" />}
            </span>

            {/* Category Name */}
            <h3 className="font-heading text-lg text-white">
              {categoryName}
            </h3>

            {/* Item Count Badge */}
            <span className="badge bg-white/20 text-white text-sm">
              {totalItems} items
            </span>

            {/* Progress Badge */}
            {countedItems > 0 && (
              <span className="badge bg-lily-green/20 text-lily-green-light text-sm">
                {countedItems}/{totalItems} counted
              </span>
            )}
          </div>

          {/* Progress Bar */}
          <div className="hidden sm:flex items-center gap-3 ml-4">
            <div className="w-24 h-2 bg-cream/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-lily-green transition-all duration-300"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            <span className="text-white/80 text-sm font-medium min-w-[3rem] text-right">
              {Math.round(progressPercentage)}%
            </span>
          </div>
        </button>

        {/* Mobile Progress Bar */}
        <div className="sm:hidden px-4 pb-3">
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-cream/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-lily-green transition-all duration-300"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            <span className="text-white/80 text-sm font-medium min-w-[3rem]">
              {Math.round(progressPercentage)}%
            </span>
          </div>
        </div>
      </div>

      {/* Items List */}
      {isExpanded && (
        <div className="card overflow-hidden animate-fade-in">
          {items.length === 0 ? (
            <div className="p-8 text-center text-neutral-text-muted">
              No items in this category
            </div>
          ) : (
            items.map((item) => (
              <ItemCountRow
                key={item.id}
                item={item}
                count={counts[item.id] ?? null}
                onChange={onCountChange}
                isChanged={changedItems.has(item.id)}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}
