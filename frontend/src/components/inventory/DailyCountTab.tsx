/**
 * DailyCountTab Component
 *
 * Primary interface for end-of-day stock counting.
 * Mobile-first design optimized for quick counting workflow.
 */

import { useState, useEffect, useMemo } from 'react';
import { FloppyDisk, CheckCircle, X, Upload } from '@phosphor-icons/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryApi } from '../../api/inventory';
import CategorySection from './CategorySection';
import TemplateImportModal from './TemplateImportModal';
import type { AdjustmentItem, InventoryItem } from '../../types/inventory';

export default function DailyCountTab() {
  const queryClient = useQueryClient();
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  // Fetch items grouped by category
  const { data: categorizedItems, isLoading } = useQuery({
    queryKey: ['inventory', 'categorized'],
    queryFn: inventoryApi.getItemsByCategory,
  });

  // Fetch categories for import modal
  const { data: categories = [] } = useQuery({
    queryKey: ['inventory', 'categories'],
    queryFn: inventoryApi.getCategories,
  });

  // Local state for counts
  const [counts, setCounts] = useState<Record<number, number>>({});
  const [changedItems, setChangedItems] = useState<Set<number>>(new Set());

  // Initialize counts when items load
  useEffect(() => {
    if (categorizedItems) {
      const initialCounts: Record<number, number> = {};
      Object.values(categorizedItems).forEach(({ items }) => {
        items.forEach((item: InventoryItem) => {
          initialCounts[item.id] = item.current_quantity;
        });
      });
      setCounts(initialCounts);
    }
  }, [categorizedItems]);

  // Calculate totals
  const { totalItems, countedItems } = useMemo(() => {
    if (!categorizedItems) return { totalItems: 0, countedItems: 0 };

    let total = 0;
    Object.values(categorizedItems).forEach(({ items }) => {
      total += items.length;
    });

    return {
      totalItems: total,
      countedItems: changedItems.size
    };
  }, [categorizedItems, changedItems]);

  // Batch adjustment mutation
  const saveMutation = useMutation({
    mutationFn: async () => {
      const adjustments: AdjustmentItem[] = [];

      // Collect all changed items
      changedItems.forEach(itemId => {
        const newQuantity = counts[itemId];
        if (newQuantity !== undefined) {
          adjustments.push({
            item_id: itemId,
            new_quantity: newQuantity,
            notes: `Daily count`
          });
        }
      });

      if (adjustments.length === 0) {
        throw new Error('No changes to save');
      }

      return inventoryApi.recordBatchAdjustment({
        adjustments,
        recorded_by: 'Staff' // TODO: Get from auth context
      });
    },
    onSuccess: (data) => {
      // Clear changed items
      setChangedItems(new Set());

      // Refetch items to get updated quantities
      queryClient.invalidateQueries({ queryKey: ['inventory'] });

      // Show success message
      alert(`✅ Success! Updated ${data.items_changed} items\n\n${data.message}`);
    },
    onError: (error: any) => {
      alert(`❌ Error saving changes: ${error.message || 'Unknown error'}`);
    }
  });

  const handleCountChange = (itemId: number, newCount: number) => {
    setCounts(prev => ({ ...prev, [itemId]: newCount }));

    // Find original quantity
    let originalQuantity = 0;
    if (categorizedItems) {
      Object.values(categorizedItems).forEach(({ items }) => {
        const item = items.find((i: InventoryItem) => i.id === itemId);
        if (item) {
          originalQuantity = item.current_quantity;
        }
      });
    }

    // Track if changed
    const isChanged = newCount !== originalQuantity;
    setChangedItems(prev => {
      const next = new Set(prev);
      if (isChanged) {
        next.add(itemId);
      } else {
        next.delete(itemId);
      }
      return next;
    });
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all changes?')) {
      // Reset to original quantities
      if (categorizedItems) {
        const resetCounts: Record<number, number> = {};
        Object.values(categorizedItems).forEach(({ items }) => {
          items.forEach((item: InventoryItem) => {
            resetCounts[item.id] = item.current_quantity;
          });
        });
        setCounts(resetCounts);
      }
      setChangedItems(new Set());
    }
  };

  const handleSave = () => {
    if (changedItems.size === 0) {
      alert('No changes to save');
      return;
    }

    if (confirm(`Save changes to ${changedItems.size} items?`)) {
      saveMutation.mutate();
    }
  };

  if (isLoading) {
    return (
      <div className="p-8 text-center">
        <div className="text-neutral-text-muted">Loading inventory items...</div>
      </div>
    );
  }

  // Check if there are actually any items across all categories
  const hasItems = categorizedItems && Object.values(categorizedItems).some(({ items }) => items.length > 0);

  if (!hasItems) {
    return (
      <>
        <div className="card p-8 text-center">
          <div className="mb-4">
            <Upload size={48} className="mx-auto text-neutral-text-muted mb-3" />
            <h3 className="text-lg font-heading text-neutral-text-dark mb-2">
              No Inventory Items
            </h3>
            <p className="text-neutral-text-muted mb-6">
              Get started by importing your items from WhatsApp template or add them manually in the Items tab.
            </p>
          </div>
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="btn-primary inline-flex items-center gap-2"
          >
            <Upload size={20} weight="fill" />
            Import from WhatsApp Template
          </button>
        </div>

        <TemplateImportModal
          isOpen={isImportModalOpen}
          onClose={() => setIsImportModalOpen(false)}
          existingCategories={categories}
        />
      </>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Progress */}
      <div className="card p-4 sticky top-0 z-20 shadow-md">
        <div className="flex items-center justify-between gap-4 mb-3">
          <div>
            <h2 className="text-lg font-heading text-neutral-text-dark">
              Daily Inventory Count
            </h2>
            <p className="text-sm text-neutral-text-muted mt-1">
              Count physical stock and update quantities
            </p>
          </div>

          {/* Progress Badge */}
          <div className="flex items-center gap-2">
            <div className={`badge text-sm ${changedItems.size > 0 ? 'bg-lily-green/20 text-lily-green' : 'bg-neutral-background'}`}>
              {countedItems}/{totalItems} counted
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-2 bg-neutral-background rounded-full overflow-hidden mb-3">
          <div
            className="h-full bg-lily-green transition-all duration-300"
            style={{ width: `${totalItems > 0 ? (countedItems / totalItems) * 100 : 0}%` }}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={changedItems.size === 0 || saveMutation.isPending}
            className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saveMutation.isPending ? (
              <>
                <span className="animate-spin">⏳</span>
                Saving...
              </>
            ) : (
              <>
                <FloppyDisk size={20} weight="fill" />
                Save Changes ({changedItems.size})
              </>
            )}
          </button>

          {changedItems.size > 0 && (
            <button
              onClick={handleReset}
              disabled={saveMutation.isPending}
              className="btn-ghost flex items-center gap-2"
            >
              <X size={20} />
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Success Message */}
      {saveMutation.isSuccess && (
        <div className="card p-4 bg-lily-green/10 border-lily-green animate-fade-in">
          <div className="flex items-center gap-2 text-lily-green">
            <CheckCircle size={20} weight="fill" />
            <span className="font-medium">Changes saved successfully!</span>
          </div>
        </div>
      )}

      {/* Category Sections */}
      <div className="space-y-4">
        {Object.entries(categorizedItems)
          .filter(([_, { items }]) => items.length > 0) // Only show categories with items
          .sort(([aId, a], [bId, b]) => {
            // Sort: named categories first (alphabetically), then uncategorized last
            if (aId === '0') return 1;
            if (bId === '0') return -1;
            return (a.category?.name || '').localeCompare(b.category?.name || '');
          })
          .map(([catId, { category, items }]) => (
            <CategorySection
              key={catId}
              categoryName={category?.name || 'Uncategorized'}
              items={items}
              counts={counts}
              changedItems={changedItems}
              onCountChange={handleCountChange}
              defaultExpanded={true}
            />
          ))}
      </div>

      {/* Floating Save Button (Mobile) */}
      {changedItems.size > 0 && (
        <div className="fixed bottom-20 right-4 lg:bottom-6 z-30 animate-scale-in">
          <button
            onClick={handleSave}
            disabled={saveMutation.isPending}
            className="btn-primary shadow-strong rounded-full px-6 py-4 flex items-center gap-2 touch-target-large"
          >
            <FloppyDisk size={24} weight="fill" />
            <span className="font-bold">Save ({changedItems.size})</span>
          </button>
        </div>
      )}

      {/* Template Import Modal */}
      <TemplateImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        existingCategories={categories}
      />
    </div>
  );
}
