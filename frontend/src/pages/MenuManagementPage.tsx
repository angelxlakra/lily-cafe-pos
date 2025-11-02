// ========================================
// Menu Management Page
// Admin interface for menu CRUD operations
// ========================================

import { useState, useMemo } from 'react';
import Sidebar from '../components/Sidebar';
import MenuItemForm from '../components/MenuItemForm';
import { useMenuItems, useDeleteMenuItem } from '../hooks/useMenu';
import { formatCurrency } from '../utils/formatCurrency';
import type { MenuItem } from '../types';

export default function MenuManagementPage() {
  const { data: menuItems, isLoading, error } = useMenuItems();
  const deleteMutation = useDeleteMenuItem();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null);
  const [deleteItemId, setDeleteItemId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const items = menuItems || [];

  // Helper function to get category name (handles both string and object)
  const getCategoryName = (category: string | { name: string; id: number; created_at?: string }): string => {
    return typeof category === 'string' ? category : category.name;
  };

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set(items.map((item) => getCategoryName(item.category)));
    return ['all', ...Array.from(cats)];
  }, [items]);

  // Filter items
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const matchesSearch =
        searchQuery === '' ||
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.description?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesCategory =
        categoryFilter === 'all' || getCategoryName(item.category) === categoryFilter;

      return matchesSearch && matchesCategory;
    });
  }, [items, searchQuery, categoryFilter]);

  const handleAddNew = () => {
    setEditingItem(null);
    setIsFormOpen(true);
  };

  const handleEdit = (item: MenuItem) => {
    setEditingItem(item);
    setIsFormOpen(true);
  };

  const handleDelete = async () => {
    if (!deleteItemId) return;

    try {
      await deleteMutation.mutateAsync(deleteItemId);
      setDeleteItemId(null);
    } catch (error) {
      console.error('Failed to delete menu item:', error);
    }
  };

  const handleFormClose = () => {
    setIsFormOpen(false);
    setEditingItem(null);
  };

  return (
    <div className="flex min-h-screen bg-neutral-background">
      {/* Sidebar */}
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      {/* Main Content */}
      <div className="flex-1 lg:ml-60">
        {/* Header */}
        <header className="bg-off-white border-b border-neutral-border p-4 md:p-6">
          <div className="flex items-center gap-4 mb-4">
            {/* Hamburger Menu Button */}
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden w-10 h-10 flex items-center justify-center rounded-lg bg-coffee-brown text-cream hover:bg-coffee-dark transition-colors"
              aria-label="Open menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex-1">
              <h1 className="text-xl md:text-2xl font-bold text-coffee-brown">
                Menu Management
              </h1>
              <p className="text-sm text-neutral-text-light mt-1">
                Add, edit, and manage menu items
              </p>
            </div>
            <button
              onClick={handleAddNew}
              className="btn bg-coffee-brown text-cream hover:bg-coffee-dark whitespace-nowrap"
            >
              + Add Item
            </button>
          </div>
        </header>

        {/* Filters */}
        <div className="p-6 bg-off-white border-b border-neutral-border">
          <div className="flex gap-4">
            {/* Search */}
            <div className="flex-1">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search menu items..."
                className="w-full px-4 py-2 border border-neutral-border rounded-lg
                         focus:outline-none focus:ring-2 focus:ring-coffee-brown"
              />
            </div>

            {/* Category Filter */}
            <div className="w-48">
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="w-full px-4 py-2 border border-neutral-border rounded-lg
                         focus:outline-none focus:ring-2 focus:ring-coffee-brown"
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat === 'all' ? 'All Categories' : cat}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Content */}
        <main className="p-6">
          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <div className="animate-spin h-12 w-12 border-4 border-coffee-brown border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-neutral-text-light">Loading menu items...</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-error/10 border border-error rounded-lg p-4">
              <p className="text-error font-medium">
                {error instanceof Error ? error.message : 'Failed to load menu items'}
              </p>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && filteredItems.length === 0 && (
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <p className="text-neutral-text-light text-lg mb-2">
                  {searchQuery || categoryFilter !== 'all'
                    ? 'No items found'
                    : 'No menu items yet'}
                </p>
                <p className="text-neutral-text-light text-sm">
                  {searchQuery || categoryFilter !== 'all'
                    ? 'Try adjusting your filters'
                    : 'Add your first menu item to get started'}
                </p>
              </div>
            </div>
          )}

          {/* Table */}
          {!isLoading && filteredItems.length > 0 && (
            <div className="bg-off-white border border-neutral-border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-cream border-b border-neutral-border">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-neutral-text-dark">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-neutral-text-dark">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-neutral-text-dark">
                      Category
                    </th>
                    <th className="px-6 py-3 text-right text-sm font-semibold text-neutral-text-dark">
                      Price
                    </th>
                    <th className="px-6 py-3 text-center text-sm font-semibold text-neutral-text-dark">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-sm font-semibold text-neutral-text-dark">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-border">
                  {filteredItems.map((item) => (
                    <tr
                      key={item.id}
                      className="hover:bg-cream/50 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <p className="font-medium text-neutral-text-dark">
                          {item.name}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-neutral-text-light line-clamp-2">
                          {item.description || ''}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-block px-2 py-1 bg-lily-green/10 text-lily-green text-sm rounded-md">
                          {getCategoryName(item.category)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <p className="font-semibold text-coffee-brown">
                          {formatCurrency(item.price)}
                        </p>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span
                          className={`inline-block px-2 py-1 text-xs rounded-md ${
                            item.is_available
                              ? 'bg-success/10 text-success'
                              : 'bg-error/10 text-error'
                          }`}
                        >
                          {item.is_available ? 'Available' : 'Unavailable'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleEdit(item)}
                            className="px-3 py-1 text-sm bg-cream border border-coffee-light text-coffee-brown hover:bg-coffee-light hover:text-white rounded-md transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => setDeleteItemId(item.id)}
                            className="px-3 py-1 text-sm bg-error/10 border border-error text-error hover:bg-error hover:text-white rounded-md transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Item Count */}
          {!isLoading && filteredItems.length > 0 && (
            <div className="mt-4 text-sm text-neutral-text-light">
              Showing {filteredItems.length} of {items.length} items
            </div>
          )}
        </main>
      </div>

      {/* Menu Item Form Modal */}
      {isFormOpen && (
        <MenuItemForm item={editingItem} onClose={handleFormClose} />
      )}

      {/* Delete Confirmation Modal */}
      {deleteItemId && (
        <ConfirmDeleteModal
          onConfirm={handleDelete}
          onCancel={() => setDeleteItemId(null)}
          isLoading={deleteMutation.isPending}
        />
      )}
    </div>
  );
}

// Confirm Delete Modal
interface ConfirmDeleteModalProps {
  onConfirm: () => void;
  onCancel: () => void;
  isLoading: boolean;
}

function ConfirmDeleteModal({
  onConfirm,
  onCancel,
  isLoading,
}: ConfirmDeleteModalProps) {
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-[60]"
        onClick={onCancel}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                   w-full max-w-md bg-off-white rounded-2xl shadow-2xl z-[70] p-6"
        role="dialog"
        aria-modal="true"
      >
        <h2 className="text-xl font-bold text-neutral-text-dark mb-4">
          Remove Menu Item?
        </h2>
        <p className="text-neutral-text-light mb-6">
          This will mark the item as unavailable. It won't delete past orders. Are you sure?
        </p>

        <div className="flex gap-3">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1 btn bg-cream border border-neutral-border text-neutral-text-dark hover:bg-neutral-border"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 btn bg-error text-white hover:bg-[#D32F2F]"
          >
            {isLoading ? 'Removing...' : 'Remove'}
          </button>
        </div>
      </div>
    </>
  );
}
