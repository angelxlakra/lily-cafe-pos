import { useState } from 'react';
import { Plus, PencilSimple, Trash, X, Check } from '@phosphor-icons/react';
import { useInventoryCategories, useCreateCategory, useUpdateCategory, useDeleteCategory } from '../../hooks/useInventory';

export default function InventoryCategoriesTab() {
  const { data: categories, isLoading } = useInventoryCategories();
  const createCategory = useCreateCategory();
  const updateCategory = useUpdateCategory();
  const deleteCategory = useDeleteCategory();

  const [isCreating, setIsCreating] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCategoryName.trim()) return;
    
    try {
      await createCategory.mutateAsync({ name: newCategoryName });
      setNewCategoryName('');
      setIsCreating(false);
    } catch (error) {
      console.error("Failed to create category", error);
    }
  };

  const startEditing = (category: { id: number; name: string }) => {
    setEditingId(category.id);
    setEditName(category.name);
  };

  const handleUpdate = async () => {
    if (!editName.trim() || !editingId) return;
    
    try {
      await updateCategory.mutateAsync({ id: editingId, data: { name: editName } });
      setEditingId(null);
    } catch (error) {
      console.error("Failed to update category", error);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this category?')) {
      try {
        await deleteCategory.mutateAsync(id);
      } catch (error) {
        alert("Cannot delete category that has items.");
      }
    }
  };

  if (isLoading) {
    return <div className="p-8 text-center text-neutral-text-muted">Loading categories...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header & Actions */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-heading text-coffee-brown dark:text-cream">Categories</h2>
        <button
          onClick={() => setIsCreating(true)}
          className="btn-primary flex items-center gap-2"
          disabled={isCreating}
        >
          <Plus weight="bold" />
          <span>Add Category</span>
        </button>
      </div>

      {/* Create Form */}
      {isCreating && (
        <form onSubmit={handleCreate} className="card p-4 flex items-center gap-4 animate-fade-in">
          <input
            type="text"
            value={newCategoryName}
            onChange={(e) => setNewCategoryName(e.target.value)}
            placeholder="Category Name (e.g., Dairy, Grains)"
            className="input-field flex-1"
            autoFocus
          />
          <div className="flex gap-2">
            <button type="submit" className="btn-success p-2 rounded-lg" disabled={createCategory.isPending}>
              <Check size={20} weight="bold" />
            </button>
            <button 
              type="button" 
              onClick={() => setIsCreating(false)}
              className="btn-ghost p-2 rounded-lg text-error hover:bg-error/10"
            >
              <X size={20} weight="bold" />
            </button>
          </div>
        </form>
      )}

      {/* Categories List */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {categories?.map((category) => (
          <div key={category.id} className="card p-4 flex justify-between items-center group hover:shadow-md transition-shadow">
            {editingId === category.id ? (
              <div className="flex items-center gap-2 w-full">
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="input-field py-1 px-2 text-sm"
                  autoFocus
                />
                <button onClick={handleUpdate} className="text-success hover:bg-success/10 p-1 rounded">
                  <Check size={18} weight="bold" />
                </button>
                <button onClick={() => setEditingId(null)} className="text-neutral-text-muted hover:bg-neutral-text-muted/10 p-1 rounded">
                  <X size={18} weight="bold" />
                </button>
              </div>
            ) : (
              <>
                <span className="font-medium text-lg text-neutral-text-dark">{category.name}</span>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button 
                    onClick={() => startEditing(category)}
                    className="p-2 text-neutral-text-muted hover:text-coffee-brown hover:bg-coffee-brown/10 rounded-lg transition-colors"
                    title="Edit"
                  >
                    <PencilSimple size={18} />
                  </button>
                  <button 
                    onClick={() => handleDelete(category.id)}
                    className="p-2 text-neutral-text-muted hover:text-error hover:bg-error/10 rounded-lg transition-colors"
                    title="Delete"
                  >
                    <Trash size={18} />
                  </button>
                </div>
              </>
            )}
          </div>
        ))}

        {(!categories || categories.length === 0) && !isCreating && (
          <div className="col-span-full text-center py-12 text-neutral-text-muted bg-neutral-background rounded-xl border-2 border-dashed border-neutral-border">
            <Tag size={48} className="mx-auto mb-3 opacity-50" />
            <p>No categories found. Create one to get started.</p>
          </div>
        )}
      </div>
    </div>
  );
}

import { Tag } from '@phosphor-icons/react';
