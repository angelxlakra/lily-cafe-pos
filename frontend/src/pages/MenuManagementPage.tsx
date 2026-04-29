// ========================================
// Menu Management Page
// Admin interface for menu CRUD operations
// ========================================

import { useState, useMemo } from 'react';
import PageHeader from '../components/PageHeader';
import MenuItemForm from '../components/MenuItemForm';
import EmptyState from '../components/EmptyState';
import ConfirmDialog from '../components/ConfirmDialog';
import SortableTableHeader from '../components/SortableTableHeader';
import { useMenuItems, useDeleteMenuItem, useUpdateMenuItem } from '../hooks/useMenu';
import { useSortableTable } from '../hooks/useSortableTable';
import { formatCurrency } from '../utils/formatCurrency';
import { toast } from '../utils/toast';
import type { MenuItem } from '../types';
import { ForkKnife } from '@phosphor-icons/react';

export default function MenuManagementPage() {
  const { data: menuItems, isLoading, error } = useMenuItems();
  const deleteMutation = useDeleteMenuItem();
  const updateMenuItemMutation = useUpdateMenuItem();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null);
  const [deleteItemId, setDeleteItemId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [optimisticAvail, setOptimisticAvail] = useState<Record<number, boolean>>({});
  const hasFilters = searchQuery !== '' || categoryFilter !== 'all';

  const items = menuItems || [];

  const getCategoryName = (menuItem: MenuItem): string => {
    return menuItem.category?.name || 'Other';
  };

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set(items.map((item) => getCategoryName(item)));
    return Array.from(cats);
  }, [items]);

  // Filter items
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const matchesSearch =
        searchQuery === '' ||
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.description?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesCategory =
        categoryFilter === 'all' || getCategoryName(item) === categoryFilter;

      return matchesSearch && matchesCategory;
    });
  }, [items, searchQuery, categoryFilter]);

  // Add sorting to filtered items
  const { sortedData: sortedItems, sortConfig, requestSort } = useSortableTable(
    filteredItems,
    'name' as keyof MenuItem,
    'asc'
  );

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
      toast.success("Menu item removed successfully");
      setDeleteItemId(null);
    } catch (error) {
      console.error('Failed to delete menu item:', error);
      toast.error("Failed to remove menu item", {
        description: error instanceof Error ? error.message : "Please try again."
      });
    }
  };

  const handleFormClose = () => {
    setIsFormOpen(false);
    setEditingItem(null);
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setCategoryFilter('all');
  };

  const handleToggleAvailability = (item: MenuItem) => {
    const newValue = !(optimisticAvail[item.id] ?? item.is_available);
    setOptimisticAvail(prev => ({ ...prev, [item.id]: newValue }));
    updateMenuItemMutation.mutate(
      { id: item.id, data: { is_available: newValue } },
      {
        onSuccess: () => {
          setOptimisticAvail(prev => { const n = { ...prev }; delete n[item.id]; return n; });
        },
        onError: () => {
          setOptimisticAvail(prev => { const n = { ...prev }; delete n[item.id]; return n; });
          toast.error('Failed to update availability');
        },
      }
    );
  };

  return (
    <div className="flex flex-col h-full bg-neutral-background">
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <PageHeader
          title="Menu Management"
          action={
            <button
              onClick={handleAddNew}
              className="flex items-center gap-1.5 bg-coffee-brown text-cream text-sm font-semibold px-4 py-2 rounded-lg hover:bg-coffee-dark transition-colors w-full justify-center lg:w-auto"
            >
              <span className="text-lg leading-none">+</span>
              Add Item
            </button>
          }
        />

        {/* Consolidated toolbar — search + category chips */}
        <div className="px-4 py-3 border-b border-neutral-border bg-off-white space-y-2 relative z-10">
          {/* Search input */}
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search menu items..."
              className="w-full px-4 py-2 border border-neutral-border rounded-lg
                       focus:outline-none focus:ring-2 focus:ring-coffee-brown"
            />
          </div>

          {/* Category chips — horizontal scroll */}
          <div className="flex gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
            <button
              onClick={() => setCategoryFilter('all')}
              className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                categoryFilter === 'all'
                  ? 'bg-coffee-brown text-cream'
                  : 'bg-cream border border-neutral-border text-coffee-dark hover:border-coffee-brown'
              }`}
            >
              All
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                  categoryFilter === cat
                    ? 'bg-coffee-brown text-cream'
                    : 'bg-cream border border-neutral-border text-coffee-dark hover:border-coffee-brown'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <main className="flex-1 overflow-auto">
          {/* Skeleton Loading State */}
          {isLoading && (
            <div className="p-6 animate-pulse space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-10 w-full bg-neutral-border/50 rounded" />
              ))}
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="m-4 bg-error/10 border border-error rounded-lg p-4">
              <p className="text-error font-medium">
                {error instanceof Error ? error.message : 'Failed to load menu items'}
              </p>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && filteredItems.length === 0 && (
            <div className="p-4 sm:p-6">
              <EmptyState
                icon={<ForkKnife size={32} weight="duotone" />}
                title={hasFilters ? 'No menu items match' : 'No menu items yet'}
                description={
                  hasFilters
                    ? 'Try adjusting your search or selecting a different category.'
                    : 'Add your first menu item to start building the cafe menu.'
                }
                actionLabel={hasFilters ? 'Reset filters' : 'Add menu item'}
                onAction={hasFilters ? handleResetFilters : handleAddNew}
              />
            </div>
          )}

          {/* Table */}
          {!isLoading && filteredItems.length > 0 && (
            <div className="p-4 sm:p-6">
              <div className="bg-off-white border border-neutral-border rounded-lg overflow-hidden">
                {/* Desktop Table */}
                <div className="hidden md:block">
                  <table className="w-full">
                    <thead className="bg-cream border-b border-neutral-border">
                      <tr>
                        <SortableTableHeader
                          label="Name"
                          sortKey={'name' as keyof MenuItem}
                          currentSortKey={sortConfig.key as keyof MenuItem}
                          sortDirection={sortConfig.direction}
                          onSort={requestSort}
                          align="left"
                        />
                        <th className="px-4 py-3 text-left text-sm font-semibold text-neutral-text-light uppercase tracking-wider">
                          Description
                        </th>
                        <SortableTableHeader
                          label="Category"
                          sortKey={'category' as keyof MenuItem}
                          currentSortKey={sortConfig.key as keyof MenuItem}
                          sortDirection={sortConfig.direction}
                          onSort={requestSort}
                          align="left"
                        />
                        <SortableTableHeader
                          label="Price"
                          sortKey={'price' as keyof MenuItem}
                          currentSortKey={sortConfig.key as keyof MenuItem}
                          sortDirection={sortConfig.direction}
                          onSort={requestSort}
                          align="right"
                        />
                        <th className="px-4 py-3 text-center text-sm font-semibold text-neutral-text-light uppercase tracking-wider">
                          Station
                        </th>
                        <SortableTableHeader
                          label="Available"
                          sortKey={'is_available' as keyof MenuItem}
                          currentSortKey={sortConfig.key as keyof MenuItem}
                          sortDirection={sortConfig.direction}
                          onSort={requestSort}
                          align="center"
                        />
                        <th className="px-4 py-3 text-right text-sm font-semibold text-neutral-text-light uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedItems.map((item) => {
                        const effectiveAvail = optimisticAvail[item.id] ?? item.is_available;
                        return (
                          <tr
                            key={item.id}
                            className="hover:bg-cream/40 transition-colors"
                          >
                            <td className="py-3 px-4 border-b border-[#F5E6D3]">
                              <p className={`font-medium ${effectiveAvail ? 'text-neutral-text-dark' : 'text-neutral-text-light'}`}>
                                {item.name}
                              </p>
                            </td>
                            <td className="py-3 px-4 border-b border-[#F5E6D3]">
                              <p className="text-sm text-neutral-text-light line-clamp-2">
                                {item.description || 'N/A'}
                              </p>
                            </td>
                            <td className="py-3 px-4 border-b border-[#F5E6D3]">
                              <span className="inline-block px-2 py-1 bg-lily-green/10 text-lily-green text-sm rounded-md">
                                {getCategoryName(item)}
                              </span>
                            </td>
                            <td className="py-3 px-4 border-b border-[#F5E6D3] text-right">
                              <p className={`font-semibold ${effectiveAvail ? 'text-coffee-brown' : 'text-neutral-text-light'}`}>
                                {formatCurrency(item.price)}
                              </p>
                            </td>
                            <td className="py-3 px-4 border-b border-[#F5E6D3] text-center">
                              <span
                                className={`inline-block px-2 py-1 text-xs rounded-md font-medium ${
                                  item.is_beverage
                                    ? 'bg-blue-100 text-blue-700'
                                    : 'bg-orange-100 text-orange-700'
                                }`}
                              >
                                {item.is_beverage ? 'Bar' : 'Kitchen'}
                              </span>
                            </td>
                            {/* Inline availability toggle */}
                            <td className="py-3 px-4 border-b border-[#F5E6D3]">
                              <label className="flex items-center gap-1.5 cursor-pointer w-fit mx-auto">
                                <button
                                  role="switch"
                                  aria-checked={effectiveAvail}
                                  onClick={() => handleToggleAvailability(item)}
                                  className={`relative inline-flex w-8 h-5 rounded-full transition-colors ${
                                    effectiveAvail ? 'bg-lily-green' : 'bg-neutral-border'
                                  }`}
                                >
                                  <span className={`inline-block w-3.5 h-3.5 rounded-full bg-white shadow transition-transform absolute top-[3px] ${
                                    effectiveAvail ? 'translate-x-[14px]' : 'translate-x-[3px]'
                                  }`} />
                                </button>
                                <span className={`text-xs font-semibold ${
                                  effectiveAvail ? 'text-lily-green' : 'text-neutral-text-light'
                                }`}>
                                  {effectiveAvail ? 'On' : 'Off'}
                                </span>
                              </label>
                            </td>
                            <td className="py-3 px-4 border-b border-[#F5E6D3]">
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
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Mobile Cards */}
                <div className="md:hidden p-4 space-y-4">
                  {sortedItems.map((item) => {
                    const effectiveAvail = optimisticAvail[item.id] ?? item.is_available;
                    return (
                      <div
                        key={item.id}
                        className="rounded-xl border border-neutral-border bg-cream/50 p-4 space-y-3"
                      >
                        <div className="flex flex-wrap justify-between gap-2">
                          <div>
                            <p className={`text-sm font-semibold ${effectiveAvail ? 'text-neutral-text-dark' : 'text-neutral-text-light'}`}>
                              {item.name}
                            </p>
                            <p className="text-xs text-neutral-text-light">
                              {getCategoryName(item)}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-neutral-text-light uppercase tracking-wide">
                              Price
                            </p>
                            <p className={`font-semibold ${effectiveAvail ? 'text-coffee-brown' : 'text-neutral-text-light'}`}>
                              {formatCurrency(item.price)}
                            </p>
                          </div>
                        </div>

                        {item.description && (
                          <p className="text-sm text-neutral-text-light">
                            {item.description}
                          </p>
                        )}

                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span
                              className={`inline-block px-2 py-1 text-xs rounded-md font-medium ${
                                item.is_beverage
                                  ? 'bg-blue-100 text-blue-700'
                                  : 'bg-orange-100 text-orange-700'
                              }`}
                            >
                              {item.is_beverage ? 'Bar' : 'Kitchen'}
                            </span>
                            {/* Mobile inline toggle */}
                            <label className="flex items-center gap-1.5 cursor-pointer w-fit">
                              <button
                                role="switch"
                                aria-checked={effectiveAvail}
                                onClick={() => handleToggleAvailability(item)}
                                className={`relative inline-flex w-8 h-5 rounded-full transition-colors ${
                                  effectiveAvail ? 'bg-lily-green' : 'bg-neutral-border'
                                }`}
                              >
                                <span className={`inline-block w-3.5 h-3.5 rounded-full bg-white shadow transition-transform absolute top-[3px] ${
                                  effectiveAvail ? 'translate-x-[14px]' : 'translate-x-[3px]'
                                }`} />
                              </button>
                              <span className={`text-xs font-semibold ${
                                effectiveAvail ? 'text-lily-green' : 'text-neutral-text-light'
                              }`}>
                                {effectiveAvail ? 'On' : 'Off'}
                              </span>
                            </label>
                          </div>
                          <div className="flex items-center gap-2">
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
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Menu Item Form Modal */}
      {isFormOpen && (
        <MenuItemForm item={editingItem} onClose={handleFormClose} />
      )}

      {/* Delete Confirmation Dialog */}
      {deleteItemId && (
        <ConfirmDialog
          isOpen={true}
          onClose={() => setDeleteItemId(null)}
          onConfirm={handleDelete}
          title="Remove Menu Item?"
          message={`This will mark "${items.find(i => i.id === deleteItemId)?.name || 'this item'}" as unavailable. It won't delete past orders. Are you sure?`}
          confirmText="Yes, Remove"
          cancelText="Cancel"
          variant="danger"
          isLoading={deleteMutation.isPending}
        />
      )}
    </div>
  );
}
