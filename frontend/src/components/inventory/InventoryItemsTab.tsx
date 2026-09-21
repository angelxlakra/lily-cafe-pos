import { useEffect, useState } from 'react';
import { Plus, MagnifyingGlass, Warning, PencilSimple, Trash, X, ListNumbers } from '@phosphor-icons/react';
import CountOrderEditor from './CountOrderEditor';
import ConfirmDialog from '../ConfirmDialog';
import LoadingSpinner from '../LoadingSpinner';
import { useInventoryItems, useInventoryCategories, useCreateItem, useUpdateItem, useDeleteItem } from '../../hooks/useInventory';
import { useAuth } from '../../hooks/useAuth';
import { describeApiError } from '../../utils/apiError';
import { formatQty } from '../../utils/countQuantity';
import type { InventoryCategory, InventoryItem, InventoryItemCreate } from '../../types/inventory';

export default function InventoryItemsTab() {
  const [search, setSearch] = useState('');
  const [categoryId, setCategoryId] = useState<number | undefined>(undefined);
  const [showLowStock, setShowLowStock] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [deletingItem, setDeletingItem] = useState<InventoryItem | null>(null);
  const [arranging, setArranging] = useState(false);

  // Items are master data (cost prices, reorder levels), so only the owner
  // may add, change or remove them. Enforced on the API too.
  const { isOwner } = useAuth();

  const { data: itemsData, isLoading } = useInventoryItems({
    search,
    category_id: categoryId,
    low_stock: showLowStock,
    is_active: true
  });
  const { data: categories = [] } = useInventoryCategories();
  const deleteItem = useDeleteItem();

  if (arranging) return <CountOrderEditor onDone={() => setArranging(false)} />;

  // Group by category in count order; the API returns items in count order
  // within each category.
  const items = itemsData?.items ?? [];
  const groups = [
    ...categories.map(category => ({ key: String(category.id), name: category.name, items: items.filter(i => i.category_id === category.id) })),
    { key: 'none', name: 'Uncategorized', items: items.filter(i => !categories.some(c => c.id === i.category_id)) },
  ].filter(group => group.items.length > 0);
  const filtered = search !== '' || categoryId !== undefined || showLowStock;

  return (
    <div className="space-y-4">
      {/* Summary and actions */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-neutral-text-muted tabular-nums" aria-live="polite">
          {itemsData ? `${itemsData.total} item${itemsData.total === 1 ? '' : 's'}${itemsData.low_stock_count ? ` · ${itemsData.low_stock_count} low on stock` : ''}` : ' '}
        </p>
        {isOwner && (
          <div className="flex gap-2">
            <button onClick={() => setArranging(true)} className="btn-secondary flex items-center gap-2 whitespace-nowrap">
              <ListNumbers weight="bold" aria-hidden />
              Count order
            </button>
            <button onClick={() => setIsCreating(true)} className="btn-primary flex items-center gap-2 whitespace-nowrap">
              <Plus weight="bold" aria-hidden />
              Add item
            </button>
          </div>
        )}
      </div>

      {/* Filters: search gets its own full row on a phone */}
      <div className="flex flex-col sm:flex-row gap-2">
        <label className="relative flex-1 min-w-0">
          <span className="sr-only">Search items</span>
          <MagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-text-muted" size={18} aria-hidden />
          <input
            type="search"
            placeholder="Search items"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-field pl-10 min-h-12"
          />
        </label>
        <div className="flex gap-2">
          <label className="flex-1 sm:w-48 sm:flex-none">
            <span className="sr-only">Category</span>
            <select
              value={categoryId ?? ''}
              onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : undefined)}
              className="input-field min-h-12"
            >
              <option value="">All categories</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </label>
          <button
            onClick={() => setShowLowStock(!showLowStock)}
            aria-pressed={showLowStock}
            className={`btn-secondary flex items-center gap-2 whitespace-nowrap ${showLowStock ? 'border-[#b45309] text-[#b45309] dark:border-warning dark:text-warning' : ''}`}
          >
            <Warning size={18} weight={showLowStock ? 'fill' : 'regular'} aria-hidden />
            Low stock
          </button>
        </div>
      </div>

      {deleteItem.isError && (
        <div role="alert" className="card p-3 border border-error/40 bg-error/5 text-sm">
          Couldn't delete the item. {describeApiError(deleteItem.error)}
        </div>
      )}

      {isLoading ? (
        <div className="py-12 flex justify-center gap-3 text-neutral-text-muted"><LoadingSpinner /> Loading items…</div>
      ) : groups.length === 0 ? (
        <div className="card p-8 text-center text-neutral-text-muted">
          {filtered ? 'No items match these filters.' : 'No items yet.'}
        </div>
      ) : (
        groups.map(group => (
          <section key={group.key} aria-labelledby={`items-group-${group.key}`}>
            <h2 id={`items-group-${group.key}`} className="font-heading text-lg! leading-tight! text-neutral-text-dark mt-2 mb-2 px-1">
              {group.name}
            </h2>
            <ul className="card divide-y divide-neutral-border overflow-hidden">
              {group.items.map(item => (
                <ItemRow
                  key={item.id}
                  item={item}
                  canEdit={isOwner}
                  onEdit={() => setEditingItem(item)}
                  onDelete={() => setDeletingItem(item)}
                />
              ))}
            </ul>
          </section>
        ))
      )}

      {(isCreating || editingItem) && isOwner && (
        <ItemFormModal
          categories={categories}
          item={editingItem}
          onClose={() => {
            setIsCreating(false);
            setEditingItem(null);
          }}
        />
      )}

      <ConfirmDialog
        isOpen={deletingItem !== null}
        onClose={() => setDeletingItem(null)}
        onConfirm={() => {
          if (deletingItem) deleteItem.mutate(deletingItem.id);
          setDeletingItem(null);
        }}
        title={`Delete ${deletingItem?.name ?? 'item'}?`}
        message="It will no longer appear in the nightly count. Its stock log stays."
        confirmText="Delete item"
        cancelText="Keep it"
        variant="danger"
      />
    </div>
  );
}

function ItemRow({ item, canEdit, onEdit, onDelete }: {
  item: InventoryItem;
  canEdit: boolean;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const cost = Number(item.cost_per_unit);
  return (
    <li className="flex items-center gap-3 pl-4 pr-2 py-2 min-h-16">
      <div className="flex-1 min-w-0">
        <div className="font-medium leading-snug text-neutral-text-dark line-clamp-2 break-words">{item.name}</div>
        <div className="text-xs text-neutral-text-muted tabular-nums">
          Alert below {formatQty(item.min_threshold)}
          {cost > 0 && <> · ₹{cost.toLocaleString('en-IN')}/{item.unit}</>}
        </div>
      </div>
      <div className="shrink-0 text-right tabular-nums">
        <div className="font-semibold text-neutral-text-dark">
          {formatQty(item.current_quantity)} <span className="text-xs font-normal text-neutral-text-muted">{item.unit}</span>
        </div>
        {item.is_low_stock && (
          <div className="inline-flex items-center gap-1 text-xs font-medium text-[#b45309] dark:text-warning">
            <Warning size={12} weight="fill" aria-hidden /> Low
          </div>
        )}
      </div>
      {canEdit && (
        <div className="flex shrink-0">
          <button
            onClick={onEdit}
            aria-label={`Edit ${item.name}`}
            className="size-12 grid place-items-center rounded-lg text-neutral-text-light hover:text-coffee-brown hover:bg-cream/60"
          >
            <PencilSimple size={18} aria-hidden />
          </button>
          <button
            onClick={onDelete}
            aria-label={`Delete ${item.name}`}
            className="size-12 grid place-items-center rounded-lg text-neutral-text-light hover:text-[#c0392b] hover:bg-error/10"
          >
            <Trash size={18} aria-hidden />
          </button>
        </div>
      )}
    </li>
  );
}

function ItemFormModal({ categories, item, onClose }: { categories: InventoryCategory[], item: InventoryItem | null, onClose: () => void }) {
  const createItem = useCreateItem();
  const updateItem = useUpdateItem();
  const [error, setError] = useState<string | null>(null);
  const saving = createItem.isPending || updateItem.isPending;

  const [formData, setFormData] = useState<InventoryItemCreate>({
    name: item?.name || '',
    category_id: item?.category_id,
    unit: item?.unit || 'pcs',
    current_quantity: Number(item?.current_quantity ?? 0),
    min_threshold: Number(item?.min_threshold ?? 5),
    cost_per_unit: Number(item?.cost_per_unit ?? 0),
  });

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => event.key === 'Escape' && !saving && onClose();
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose, saving]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      if (item) {
        await updateItem.mutateAsync({
          id: item.id,
          data: {
            name: formData.name,
            category_id: formData.category_id,
            unit: formData.unit,
            min_threshold: formData.min_threshold,
            cost_per_unit: formData.cost_per_unit
          }
        });
      } else {
        await createItem.mutateAsync(formData);
      }
      onClose();
    } catch (err) {
      setError(describeApiError(err));
    }
  };

  const field = 'block text-sm font-medium text-neutral-text-body mb-1';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in" onClick={saving ? undefined : onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="item-form-title"
        className="card w-full max-w-md max-h-[90dvh] overflow-y-auto p-6 shadow-strong animate-scale-in"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
          <h2 id="item-form-title" className="font-heading text-2xl! text-neutral-text-dark">
            {item ? 'Edit item' : 'New item'}
          </h2>
          <button onClick={onClose} aria-label="Close" className="size-12 -mr-3 grid place-items-center text-neutral-text-muted hover:text-neutral-text-dark">
            <X size={22} aria-hidden />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="item-name" className={field}>Name</label>
            <input
              id="item-name"
              type="text"
              required
              value={formData.name}
              onChange={e => setFormData({...formData, name: e.target.value})}
              className="input-field"
              placeholder="e.g. Milk, Eggs"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="item-category" className={field}>Category</label>
              <select
                id="item-category"
                value={formData.category_id ?? ''}
                onChange={e => setFormData({...formData, category_id: e.target.value ? Number(e.target.value) : undefined})}
                className="input-field"
              >
                <option value="">None</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="item-unit" className={field}>Unit</label>
              <select
                id="item-unit"
                value={formData.unit}
                onChange={e => setFormData({...formData, unit: e.target.value})}
                className="input-field"
              >
                <option value="pcs">Pieces (pcs)</option>
                <option value="kg">Kilograms (kg)</option>
                <option value="g">Grams (g)</option>
                <option value="L">Litres (L)</option>
                <option value="ml">Millilitres (ml)</option>
              </select>
            </div>
          </div>

          {!item && (
            <div>
              <label htmlFor="item-quantity" className={field}>Stock right now</label>
              <input
                id="item-quantity"
                type="number"
                min="0"
                step="0.01"
                value={formData.current_quantity}
                onChange={e => setFormData({...formData, current_quantity: Number(e.target.value)})}
                className="input-field"
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="item-min" className={field}>Low-stock alert below</label>
              <input
                id="item-min"
                type="number"
                min="0"
                step="0.01"
                value={formData.min_threshold}
                onChange={e => setFormData({...formData, min_threshold: Number(e.target.value)})}
                className="input-field"
              />
            </div>
            <div>
              <label htmlFor="item-cost" className={field}>Cost per unit (₹)</label>
              <input
                id="item-cost"
                type="number"
                min="0"
                step="0.01"
                value={formData.cost_per_unit}
                onChange={e => setFormData({...formData, cost_per_unit: Number(e.target.value)})}
                className="input-field"
              />
            </div>
          </div>

          {error && (
            <div role="alert" className="text-sm font-medium text-[#c0392b] dark:text-error">Not saved. {error}</div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} disabled={saving} className="btn-ghost">Cancel</button>
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? 'Saving…' : item ? 'Save changes' : 'Add item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
