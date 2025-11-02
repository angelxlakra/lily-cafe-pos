// ========================================
// Menu Item Form Component
// Modal form for creating/editing menu items
// ========================================

import { useState, FormEvent, useEffect } from "react";
import {
  useCategories,
  useCreateMenuItem,
  useUpdateMenuItem,
  useCreateCategory,
} from "../hooks/useMenu";
import type { MenuItem } from "../types";

interface MenuItemFormProps {
  item: MenuItem | null; // null for new item, MenuItem for edit
  onClose: () => void;
}

export default function MenuItemForm({ item, onClose }: MenuItemFormProps) {
  const { data: categories } = useCategories();
  const createMutation = useCreateMenuItem();
  const updateMutation = useUpdateMenuItem();
  const createCategoryMutation = useCreateCategory();

  const isEditing = !!item;

  const [name, setName] = useState(item?.name || "");
  const [description, setDescription] = useState(item?.description || "");
  const [price, setPrice] = useState(
    item ? ((item.price ?? 0) / 100).toString() : ""
  );
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>(
    item ? String(item.category_id) : ""
  );
  const [isAvailable, setIsAvailable] = useState(item?.is_available ?? true);
  const [error, setError] = useState("");
  const [showNewCategory, setShowNewCategory] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState("");

  const categoryList = categories || [];

  useEffect(() => {
    if (item) {
      setSelectedCategoryId(String(item.category_id));
      setPrice((item.price / 100).toString());
    }
  }, [item]);

  const handleCategorySelect = (value: string) => {
    if (value === "__new__") {
      setShowNewCategory(true);
      return;
    }
    setSelectedCategoryId(value);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    if (!name.trim()) {
      setError("Please enter item name");
      return;
    }

    const priceValue = parseFloat(price);
    if (!price || Number.isNaN(priceValue) || priceValue <= 0) {
      setError("Please enter a valid price");
      return;
    }

    if (!selectedCategoryId) {
      setError("Please select a category");
      return;
    }

    const pricePaise = Math.round(priceValue * 100);
    const categoryId = Number(selectedCategoryId);

    try {
      if (isEditing) {
        // Update existing item
        await updateMutation.mutateAsync({
          id: item.id,
          data: {
            name: name.trim(),
            description: description.trim() || null,
            price: pricePaise,
            category_id: categoryId,
            is_available: isAvailable,
          },
        });
      } else {
        // Create new item
        const createdItem = await createMutation.mutateAsync({
          name: name.trim(),
          description: description.trim() || null,
          price: pricePaise,
          category_id: categoryId,
        });

        // If the item should start as unavailable, apply an update after creation
        if (!isAvailable && createdItem) {
          await updateMutation.mutateAsync({
            id: createdItem.id,
            data: { is_available: false },
          });
        }
      }

      // Close modal on success
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save menu item");
    }
  };

  const handleCreateCategory = async () => {
    if (!newCategoryName.trim()) {
      setError("Please enter category name");
      return;
    }

    try {
      const newCat = await createCategoryMutation.mutateAsync({
        name: newCategoryName.trim(),
      });

      // Select the new category
      setSelectedCategoryId(String(newCat.id));
      setNewCategoryName("");
      setShowNewCategory(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create category"
      );
    }
  };

  const isProcessing = createMutation.isPending || updateMutation.isPending;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-[60]"
        onClick={!isProcessing ? onClose : undefined}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                   w-full max-w-lg bg-off-white rounded-2xl shadow-2xl z-[70]
                   flex flex-col max-h-[90vh]"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-border">
          <h2 className="text-xl font-bold text-neutral-text-dark">
            {isEditing ? "Edit Menu Item" : "Add New Menu Item"}
          </h2>
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-neutral-border transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <span className="text-xl text-neutral-text-light">&times;</span>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6">
          <div className="space-y-5">
            {/* Name */}
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-neutral-text-dark mb-2"
              >
                Item Name *
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={isProcessing}
                className="w-full px-4 py-3 border border-neutral-border rounded-lg
                         focus:outline-none focus:ring-2 focus:ring-coffee-brown
                         disabled:bg-neutral-border disabled:cursor-not-allowed"
                placeholder="e.g., Masala Dosa"
                autoFocus
              />
            </div>

            {/* Description */}
            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium text-neutral-text-dark mb-2"
              >
                Description
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={isProcessing}
                className="w-full px-4 py-3 border border-neutral-border rounded-lg
                         focus:outline-none focus:ring-2 focus:ring-coffee-brown
                         disabled:bg-neutral-border disabled:cursor-not-allowed
                         resize-none"
                placeholder="e.g., Crispy dosa with potato filling"
                rows={3}
              />
            </div>

            {/* Price */}
            <div>
              <label
                htmlFor="price"
                className="block text-sm font-medium text-neutral-text-dark mb-2"
              >
                Price *
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-text-light">
                  ₹
                </span>
                <input
                  id="price"
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  disabled={isProcessing}
                  className="w-full pl-8 pr-4 py-3 border border-neutral-border rounded-lg
                           focus:outline-none focus:ring-2 focus:ring-coffee-brown
                           disabled:bg-neutral-border disabled:cursor-not-allowed"
                  placeholder="0"
                  min="1"
                  step="1"
                />
              </div>
              <p className="mt-1 text-xs text-neutral-text-light">
                Enter amount in rupees (whole numbers only)
              </p>
            </div>

            {/* Category */}
            <div>
              <label
                htmlFor="category"
                className="block text-sm font-medium text-neutral-text-dark mb-2"
              >
                Category *
              </label>
              {!showNewCategory ? (
                <div className="flex gap-2">
                  <select
                    id="category"
                    value={selectedCategoryId}
                    onChange={(e) => handleCategorySelect(e.target.value)}
                    disabled={isProcessing}
                    className="flex-1 px-4 py-3 border border-neutral-border rounded-lg
                             focus:outline-none focus:ring-2 focus:ring-coffee-brown
                             disabled:bg-neutral-border disabled:cursor-not-allowed"
                  >
                    <option value="">Select a category</option>
                    {categoryList.map((cat) => (
                      <option key={cat.id} value={String(cat.id)}>
                        {cat.name}
                      </option>
                    ))}
                    <option value="__new__">+ Create New Category</option>
                  </select>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newCategoryName}
                      onChange={(e) => setNewCategoryName(e.target.value)}
                      disabled={createCategoryMutation.isPending}
                      className="flex-1 px-4 py-3 border border-neutral-border rounded-lg
                               focus:outline-none focus:ring-2 focus:ring-coffee-brown
                               disabled:bg-neutral-border disabled:cursor-not-allowed"
                      placeholder="New category name"
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={handleCreateCategory}
                      disabled={createCategoryMutation.isPending}
                      className="btn bg-lily-green text-white hover:bg-[#7A8C75] whitespace-nowrap"
                    >
                      {createCategoryMutation.isPending
                        ? "Creating..."
                        : "Create"}
                    </button>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setShowNewCategory(false);
                      setNewCategoryName("");
                    }}
                    className="text-sm text-neutral-text-light hover:text-coffee-brown transition-colors"
                  >
                    � Back to select
                  </button>
                </div>
              )}
            </div>

            {/* Availability */}
            <div>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isAvailable}
                  onChange={(e) => setIsAvailable(e.target.checked)}
                  disabled={isProcessing}
                  className="w-5 h-5 border border-neutral-border rounded
                           focus:outline-none focus:ring-2 focus:ring-coffee-brown
                           disabled:cursor-not-allowed"
                />
                <span className="text-sm font-medium text-neutral-text-dark">
                  Available for ordering
                </span>
              </label>
              <p className="mt-1 ml-8 text-xs text-neutral-text-light">
                Uncheck to temporarily hide this item from the menu
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-error/10 border border-error rounded-lg p-3">
                <p className="text-sm text-error font-medium">{error}</p>
              </div>
            )}
          </div>
        </form>

        {/* Footer */}
        <div className="p-6 border-t border-neutral-border">
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isProcessing}
              className="flex-1 btn bg-cream border border-neutral-border text-neutral-text-dark hover:bg-neutral-border"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isProcessing}
              className="flex-1 btn bg-coffee-brown text-cream hover:bg-coffee-dark
                       disabled:bg-neutral-border disabled:cursor-not-allowed"
            >
              {isProcessing ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Saving...
                </span>
              ) : isEditing ? (
                "Save Changes"
              ) : (
                "Add Item"
              )}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
