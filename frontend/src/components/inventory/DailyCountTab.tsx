/**
 * DailyCountTab Component
 *
 * Primary interface for end-of-day stock counting.
 * Mobile-first design optimized for quick counting workflow.
 */

import { useState, useMemo, useEffect, useRef } from 'react';
import { FloppyDisk, CheckCircle, X, Upload, ClockCounterClockwise } from '@phosphor-icons/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryApi } from '../../api/inventory';
import CategorySection from './CategorySection';
import TemplateImportModal from './TemplateImportModal';
import ConfirmDialog from '../ConfirmDialog';
import LoadingSpinner from '../LoadingSpinner';
import { useAuth } from '../../hooks/useAuth';
import { describeApiError } from '../../utils/apiError';
import type { AdjustmentItem, InventoryItem } from '../../types/inventory';

// Unsaved counts live on this device so a tab switch, reload or closed
// browser never loses a half-finished count.
const DRAFT_KEY = 'lily.inventoryCountDraft';
// ponytail: expiry by age of the last entry, not by business date, so a count
// that runs past midnight survives; stale drafts from a previous night expire.
const DRAFT_MAX_AGE_MS = 12 * 60 * 60 * 1000;

type CountDraft = { savedAt: number; counts: Record<number, number> };

function loadDraft(): CountDraft | null {
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    if (!raw) return null;
    const draft = JSON.parse(raw) as CountDraft;
    if (!draft?.counts || Date.now() - draft.savedAt > DRAFT_MAX_AGE_MS) {
      localStorage.removeItem(DRAFT_KEY);
      return null;
    }
    return draft;
  } catch {
    return null;
  }
}

/** Returns false when the browser won't let us store the draft. */
function saveDraft(counts: Record<number, number>): boolean {
  try {
    if (Object.keys(counts).length === 0) localStorage.removeItem(DRAFT_KEY);
    else localStorage.setItem(DRAFT_KEY, JSON.stringify({ savedAt: Date.now(), counts }));
    return true;
  } catch {
    return false;
  }
}

const formatTime = (date: Date) =>
  date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });

export default function DailyCountTab() {
  const queryClient = useQueryClient();
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  // Importing a template creates inventory categories and items — master
  // data, so owner-only. The daily count itself stays open to admin.
  const { isOwner } = useAuth();

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

  // Entered counts, keyed by item id. A missing key means "not touched",
  // so the input shows the system quantity as its placeholder.
  const [restoredDraft] = useState(loadDraft);
  const [counts, setCounts] = useState<Record<number, number>>(() => restoredDraft?.counts ?? {});
  const [showRestored, setShowRestored] = useState(() => Object.keys(restoredDraft?.counts ?? {}).length > 0);
  const [confirmingSave, setConfirmingSave] = useState(false);
  const [confirmingReset, setConfirmingReset] = useState(false);
  const [lastSave, setLastSave] = useState<{ itemsChanged: number; at: Date } | null>(null);
  const draftStored = useRef(true);

  useEffect(() => {
    draftStored.current = saveDraft(counts);
  }, [counts]);

  const systemQuantities = useMemo(() => {
    const quantities = new Map<number, number>();
    Object.values(categorizedItems ?? {}).forEach(({ items }) =>
      items.forEach((item: InventoryItem) => quantities.set(item.id, item.current_quantity))
    );
    return quantities;
  }, [categorizedItems]);

  // Items whose entered count differs from the system. Derived rather than
  // stored, so a restored draft and fresh server data can never disagree.
  const changedItems = useMemo(() => {
    const changed = new Set<number>();
    Object.entries(counts).forEach(([id, count]) => {
      const itemId = Number(id);
      if (systemQuantities.has(itemId) && systemQuantities.get(itemId) !== count) changed.add(itemId);
    });
    return changed;
  }, [counts, systemQuantities]);

  const totalItems = systemQuantities.size;
  const countedItems = changedItems.size;

  // Only nag on leave when the draft couldn't be kept on this device.
  useEffect(() => {
    if (changedItems.size === 0) return;
    const warn = (event: BeforeUnloadEvent) => {
      if (draftStored.current) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [changedItems.size]);

  const saveMutation = useMutation({
    mutationFn: () => {
      const adjustments: AdjustmentItem[] = [...changedItems].map(itemId => ({
        item_id: itemId,
        new_quantity: counts[itemId],
        notes: 'Daily count',
      }));
      return inventoryApi.recordBatchAdjustment({
        adjustments,
        recorded_by: 'Staff' // TODO: Get from auth context
      });
    },
    onSuccess: (data) => {
      setCounts({});
      setShowRestored(false);
      setLastSave({ itemsChanged: data.items_changed, at: new Date() });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });

  const handleCountChange = (itemId: number, newCount: number | null) => {
    setLastSave(null);
    setCounts(prev => {
      const next = { ...prev };
      if (newCount === null) delete next[itemId];
      else next[itemId] = newCount;
      return next;
    });
  };

  const handleReset = () => {
    setCounts({});
    setShowRestored(false);
    setConfirmingReset(false);
    saveMutation.reset();
  };

  const handleSave = () => {
    setConfirmingSave(false);
    saveMutation.mutate();
  };

  const itemsLabel = (n: number) => `${n} item${n === 1 ? '' : 's'}`;

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
              {isOwner
                ? 'Get started by importing your items from WhatsApp template or add them manually in the Items tab.'
                : 'No items to count yet.'}
            </p>
          </div>
          {isOwner && (
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="btn-primary inline-flex items-center gap-2"
            >
              <Upload size={20} weight="fill" />
              Import from WhatsApp Template
            </button>
          )}
        </div>

        <TemplateImportModal
          isOpen={isImportModalOpen && isOwner}
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
            onClick={() => setConfirmingSave(true)}
            disabled={changedItems.size === 0 || saveMutation.isPending}
            className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saveMutation.isPending ? (
              <>
                <LoadingSpinner size="sm" className="text-current" />
                Saving…
              </>
            ) : (
              <>
                <FloppyDisk size={20} weight="fill" />
                Save Changes ({changedItems.size})
              </>
            )}
          </button>

          {Object.keys(counts).length > 0 && (
            <button
              onClick={() => setConfirmingReset(true)}
              disabled={saveMutation.isPending}
              className="btn-ghost flex items-center gap-2"
            >
              <X size={20} />
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Draft restored after a tab switch, reload or closed browser */}
      {showRestored && restoredDraft && (
        <div className="card p-4 flex items-start gap-3 border border-lily-green/40 bg-lily-green/10" role="status">
          <ClockCounterClockwise size={20} weight="bold" className="text-coffee-brown shrink-0 mt-0.5" aria-hidden />
          <p className="flex-1 text-sm text-neutral-text-dark">
            <span className="font-medium">Picked up where you left off.</span>{' '}
            {Object.keys(restoredDraft.counts).length === 1 ? '1 entry' : `${Object.keys(restoredDraft.counts).length} entries`} restored from {formatTime(new Date(restoredDraft.savedAt))}.
          </p>
          <button
            onClick={() => setShowRestored(false)}
            className="btn-ghost -m-2 shrink-0"
            aria-label="Dismiss"
          >
            <X size={18} />
          </button>
        </div>
      )}

      {/* Save failed: entries are kept, offer a retry */}
      {saveMutation.isError && (
        <div className="card p-4 border border-error/40 bg-error/5" role="alert">
          <p className="font-medium text-neutral-text-dark">Count not saved</p>
          <p className="text-sm text-neutral-text-body mt-1">
            {describeApiError(saveMutation.error)} Your numbers are still here
            {draftStored.current ? ' and kept on this phone' : ''}.
          </p>
          <button
            onClick={() => saveMutation.mutate()}
            disabled={changedItems.size === 0}
            className="btn-secondary mt-3"
          >
            Try again
          </button>
        </div>
      )}

      {/* Success Message */}
      {lastSave && (
        <div className="card p-4 bg-lily-green/10 border border-lily-green/40" role="status">
          <div className="flex items-center gap-2 text-neutral-text-dark">
            <CheckCircle size={20} weight="fill" className="text-lily-green" />
            <span className="font-medium">
              Count saved at {formatTime(lastSave.at)}. {itemsLabel(lastSave.itemsChanged)} updated.
            </span>
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
            onClick={() => setConfirmingSave(true)}
            disabled={saveMutation.isPending}
            className="btn-primary shadow-strong rounded-full px-6 py-4 flex items-center gap-2 touch-target-large"
          >
            <FloppyDisk size={24} weight="fill" />
            <span className="font-bold">Save ({changedItems.size})</span>
          </button>
        </div>
      )}

      <ConfirmDialog
        isOpen={confirmingSave}
        onClose={() => setConfirmingSave(false)}
        onConfirm={handleSave}
        title="Save tonight's count?"
        message={`Stock will be updated for ${itemsLabel(changedItems.size)}. Items you didn't change keep their current numbers.`}
        confirmText="Save count"
        cancelText="Keep counting"
        variant="info"
      />

      <ConfirmDialog
        isOpen={confirmingReset}
        onClose={() => setConfirmingReset(false)}
        onConfirm={handleReset}
        title="Clear all entries?"
        message={`This removes ${Object.keys(counts).length === 1 ? 'the number' : `all ${Object.keys(counts).length} numbers`} you've entered. Saved stock doesn't change.`}
        confirmText="Clear entries"
        cancelText="Keep counting"
        variant="danger"
      />

      {/* Template Import Modal */}
      <TemplateImportModal
        isOpen={isImportModalOpen && isOwner}
        onClose={() => setIsImportModalOpen(false)}
        existingCategories={categories}
      />
    </div>
  );
}
