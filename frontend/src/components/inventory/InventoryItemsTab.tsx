import { useState } from 'react';
import { Plus, MagnifyingGlass, Warning, PencilSimple, Trash, X } from '@phosphor-icons/react';
import { useInventoryItems, useInventoryCategories, useCreateItem, useUpdateItem, useDeleteItem } from '../../hooks/useInventory';
import type { InventoryItem, InventoryItemCreate } from '../../types/inventory';

export default function InventoryItemsTab() {
  const [search, setSearch] = useState('');
  const [categoryId, setCategoryId] = useState<number | undefined>(undefined);
  const [showLowStock, setShowLowStock] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);

  const { data: itemsData, isLoading } = useInventoryItems({
    search,
    category_id: categoryId,
    low_stock: showLowStock,
    is_active: true
  });

  const { data: categories } = useInventoryCategories();
  const deleteItem = useDeleteItem();

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      await deleteItem.mutateAsync(id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Filters & Actions */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
        <div className="flex flex-1 gap-2 w-full md:w-auto">
          <div className="relative flex-1 md:max-w-xs">
            <MagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-text-muted" size={18} />
            <input
              type="text"
              placeholder="Search items..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field pl-10 py-2"
            />
          </div>
          
          <select
            value={categoryId || ''}
            onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : undefined)}
            className="input-field w-auto py-2"
          >
            <option value="">All Categories</option>
            {categories?.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>

          <button
            onClick={() => setShowLowStock(!showLowStock)}
            className={`btn-secondary flex items-center gap-2 ${showLowStock ? 'bg-warning/20 border-warning text-warning-dark' : ''}`}
          >
            <Warning size={18} weight={showLowStock ? "fill" : "regular"} />
            <span className="hidden sm:inline">Low Stock</span>
          </button>
        </div>

        <button
          onClick={() => setIsCreating(true)}
          className="btn-primary flex items-center gap-2 whitespace-nowrap"
        >
          <Plus weight="bold" />
          <span>Add Item</span>
        </button>
      </div>

      {/* Create/Edit Form Modal */}
      {(isCreating || editingItem) && (
        <ItemFormModal
          categories={categories || []}
          item={editingItem}
          onClose={() => {
            setIsCreating(false);
            setEditingItem(null);
          }}
        />
      )}

      {/* Items Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-neutral-background border-b border-neutral-border text-neutral-text-muted text-sm uppercase tracking-wider">
                <th className="p-4 font-medium">Item Name</th>
                <th className="p-4 font-medium">Category</th>
                <th className="p-4 font-medium text-right">Stock Level</th>
                <th className="p-4 font-medium text-right">Unit</th>
                <th className="p-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-border">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-neutral-text-muted">Loading items...</td>
                </tr>
              ) : !itemsData?.items || itemsData.items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-neutral-text-muted">No items found matching your filters.</td>
                </tr>
              ) : (
                itemsData.items.map((item) => (
                  <tr key={item.id} className="group hover:bg-neutral-background/50 transition-colors">
                    <td className="p-4">
                      <div className="font-medium text-neutral-text-dark">{item.name}</div>
                      {item.is_low_stock && (
                        <div className="text-xs text-error flex items-center gap-1 mt-1">
                          <Warning size={12} weight="fill" />
                          Low Stock (Min: {item.min_threshold})
                        </div>
                      )}
                    </td>
                    <td className="p-4 text-neutral-text-body">
                      <span className="badge bg-neutral-background border border-neutral-border">
                        {item.category_name || 'Uncategorized'}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <span className={`font-mono font-medium ${item.is_low_stock ? 'text-error' : 'text-success'}`}>
                        {item.current_quantity}
                      </span>
                    </td>
                    <td className="p-4 text-right text-neutral-text-muted text-sm">{item.unit}</td>
                    <td className="p-4 text-right">
                      <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => setEditingItem(item)}
                          className="p-2 text-neutral-text-muted hover:text-coffee-brown hover:bg-coffee-brown/10 rounded-lg"
                          title="Edit"
                        >
                          <PencilSimple size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(item.id)}
                          className="p-2 text-neutral-text-muted hover:text-error hover:bg-error/10 rounded-lg"
                          title="Delete"
                        >
                          <Trash size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function ItemFormModal({ categories, item, onClose }: { categories: any[], item: InventoryItem | null, onClose: () => void }) {
  const createItem = useCreateItem();
  const updateItem = useUpdateItem();
  
  const [formData, setFormData] = useState<InventoryItemCreate>({
    name: item?.name || '',
    category_id: item?.category_id,
    unit: item?.unit || 'pcs',
    current_quantity: item?.current_quantity || 0,
    min_threshold: item?.min_threshold || 5,
    cost_per_unit: item?.cost_per_unit || 0
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
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
    } catch (error) {
      console.error("Failed to save item", error);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="card w-full max-w-md p-6 shadow-strong animate-scale-in" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-heading text-neutral-text-dark">
            {item ? 'Edit Item' : 'New Item'}
          </h3>
          <button onClick={onClose} className="text-neutral-text-muted hover:text-neutral-text-dark">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-text-muted mb-1">Item Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={e => setFormData({...formData, name: e.target.value})}
              className="input-field"
              placeholder="e.g., Milk, Eggs"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-neutral-text-muted mb-1">Category</label>
              <select
                value={formData.category_id || ''}
                onChange={e => setFormData({...formData, category_id: Number(e.target.value)})}
                className="input-field"
              >
                <option value="">Select Category</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-text-muted mb-1">Unit</label>
              <select
                value={formData.unit}
                onChange={e => setFormData({...formData, unit: e.target.value})}
                className="input-field"
              >
                <option value="pcs">Pieces (pcs)</option>
                <option value="kg">Kilograms (kg)</option>
                <option value="g">Grams (g)</option>
                <option value="L">Liters (L)</option>
                <option value="ml">Milliliters (ml)</option>
              </select>
            </div>
          </div>

          {!item && (
            <div>
              <label className="block text-sm font-medium text-neutral-text-muted mb-1">Initial Quantity</label>
              <input
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
              <label className="block text-sm font-medium text-neutral-text-muted mb-1">Min Threshold</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={formData.min_threshold}
                onChange={e => setFormData({...formData, min_threshold: Number(e.target.value)})}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-text-muted mb-1">Cost per Unit</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={formData.cost_per_unit}
                onChange={e => setFormData({...formData, cost_per_unit: Number(e.target.value)})}
                className="input-field"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button type="button" onClick={onClose} className="btn-ghost">Cancel</button>
            <button type="submit" className="btn-primary">
              {item ? 'Update Item' : 'Create Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
