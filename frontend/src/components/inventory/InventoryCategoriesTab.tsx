import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, PencilSimple, Trash, ListNumbers } from '@phosphor-icons/react';
import CountOrderEditor from './CountOrderEditor';
import ConfirmDialog from '../ConfirmDialog';
import LoadingSpinner from '../LoadingSpinner';
import { inventoryApi } from '../../api/inventory';
import { useInventoryCategories, useCreateCategory, useUpdateCategory, useDeleteCategory } from '../../hooks/useInventory';
import { describeApiError } from '../../utils/apiError';
import type { InventoryCategory } from '../../types/inventory';

// Owner-only tab (hidden from admins by InventoryPage; enforced by the API).
export default function InventoryCategoriesTab() {
  const { data: categories = [], isLoading } = useInventoryCategories();
  // Item counts per category come from the count sheet (active items only).
  const { data: groups = [] } = useQuery({
    queryKey: ['inventory', 'count-sheet'],
    queryFn: inventoryApi.getCountSheet,
  });
  const createCategory = useCreateCategory();
  const updateCategory = useUpdateCategory();
  const deleteCategory = useDeleteCategory();

  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [deleting, setDeleting] = useState<InventoryCategory | null>(null);
  const [notice, setNotice] = useState<{ id: number | 'new'; text: string } | null>(null);
  const [arranging, setArranging] = useState(false);

  const itemCount = (id: number) => groups.find(group => group.category?.id === id)?.items.length ?? 0;

  if (arranging) return <CountOrderEditor onDone={() => setArranging(false)} />;

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      await createCategory.mutateAsync({ name: newName.trim() });
      setNewName('');
      setIsCreating(false);
      setNotice(null);
    } catch (error) {
      setNotice({ id: 'new', text: `Not added. ${describeApiError(error)}` });
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editName.trim() || editingId === null) return;
    try {
      await updateCategory.mutateAsync({ id: editingId, data: { name: editName.trim() } });
      setEditingId(null);
      setNotice(null);
    } catch (error) {
      setNotice({ id: editingId, text: `Not renamed. ${describeApiError(error)}` });
    }
  };

  const askDelete = (category: InventoryCategory) => {
    const count = itemCount(category.id);
    if (count > 0) {
      setNotice({ id: category.id, text: `Move or delete its ${count} item${count === 1 ? '' : 's'} first (Items tab).` });
      return;
    }
    setNotice(null);
    setDeleting(category);
  };

  const confirmDelete = async () => {
    const category = deleting;
    setDeleting(null);
    if (!category) return;
    try {
      await deleteCategory.mutateAsync(category.id);
    } catch (error) {
      setNotice({ id: category.id, text: `Not deleted. ${describeApiError(error)}` });
    }
  };

  if (isLoading) {
    return <div className="py-12 flex justify-center gap-3 text-neutral-text-muted"><LoadingSpinner /> Loading categories…</div>;
  }

  return (
    <div className="max-w-2xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-neutral-text-muted tabular-nums">
          {categories.length} categor{categories.length === 1 ? 'y' : 'ies'}
        </p>
        <div className="flex gap-2">
          <button onClick={() => setArranging(true)} className="btn-secondary flex items-center gap-2 whitespace-nowrap">
            <ListNumbers weight="bold" aria-hidden />
            Count order
          </button>
          <button
            onClick={() => { setIsCreating(true); setNotice(null); }}
            disabled={isCreating}
            className="btn-primary flex items-center gap-2 whitespace-nowrap"
          >
            <Plus weight="bold" aria-hidden />
            Add category
          </button>
        </div>
      </div>

      {isCreating && (
        <form onSubmit={handleCreate} className="card p-3 space-y-2 animate-fade-in">
          <label htmlFor="new-category" className="block text-sm font-medium text-neutral-text-body">New category</label>
          <div className="flex flex-wrap gap-2">
            <input
              id="new-category"
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="e.g. Dairy, Dry grocery"
              className="input-field flex-1 min-w-48 min-h-12"
              autoFocus
            />
            <button type="submit" className="btn-primary" disabled={createCategory.isPending || !newName.trim()}>
              {createCategory.isPending ? 'Adding…' : 'Add'}
            </button>
            <button type="button" onClick={() => { setIsCreating(false); setNewName(''); setNotice(null); }} className="btn-ghost">
              Cancel
            </button>
          </div>
          {notice?.id === 'new' && <div role="alert" className="text-sm font-medium text-error">{notice.text}</div>}
        </form>
      )}

      {categories.length === 0 && !isCreating ? (
        <div className="card p-8 text-center text-neutral-text-muted">
          No categories yet. Add one, or import the WhatsApp checklist from Daily count.
        </div>
      ) : (
        <ul className="card divide-y divide-neutral-border overflow-hidden">
          {categories.map(category => {
            const count = itemCount(category.id);
            return (
              <li key={category.id} className="pl-4 pr-2 py-2 min-h-16 flex flex-col justify-center">
                {editingId === category.id ? (
                  <form onSubmit={handleUpdate} className="flex flex-wrap gap-2 py-1">
                    <label htmlFor={`rename-${category.id}`} className="sr-only">Name for {category.name}</label>
                    <input
                      id={`rename-${category.id}`}
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="input-field flex-1 min-w-40 min-h-12"
                      autoFocus
                    />
                    <button type="submit" className="btn-primary" disabled={updateCategory.isPending || !editName.trim()}>Save</button>
                    <button type="button" onClick={() => { setEditingId(null); setNotice(null); }} className="btn-ghost">Cancel</button>
                  </form>
                ) : (
                  <div className="flex items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium leading-snug text-neutral-text-dark line-clamp-2 break-words">{category.name}</div>
                      <div className="text-xs text-neutral-text-muted tabular-nums">{count} item{count === 1 ? '' : 's'}</div>
                    </div>
                    <button
                      onClick={() => { setEditingId(category.id); setEditName(category.name.trim()); setNotice(null); }}
                      aria-label={`Rename ${category.name}`}
                      className="size-12 grid place-items-center rounded-lg text-neutral-text-light hover:text-coffee-brown hover:bg-cream/60"
                    >
                      <PencilSimple size={18} aria-hidden />
                    </button>
                    <button
                      onClick={() => askDelete(category)}
                      aria-label={`Delete ${category.name}`}
                      className="size-12 grid place-items-center rounded-lg text-neutral-text-light hover:text-error hover:bg-error/10"
                    >
                      <Trash size={18} aria-hidden />
                    </button>
                  </div>
                )}
                {notice?.id === category.id && (
                  <div role="alert" className="pb-1 text-sm font-medium text-error">{notice.text}</div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      <ConfirmDialog
        isOpen={deleting !== null}
        onClose={() => setDeleting(null)}
        onConfirm={confirmDelete}
        title={`Delete ${deleting?.name.trim() ?? 'category'}?`}
        message="It has no items, so nothing else changes."
        confirmText="Delete category"
        cancelText="Keep it"
        variant="danger"
      />
    </div>
  );
}
