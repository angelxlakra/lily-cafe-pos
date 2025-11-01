// ========================================
// Menu List Component
// Displays menu items grouped by category
// ========================================

import { useMemo } from "react";
import type { MenuItem } from "../types";
import { formatCurrency } from "../utils/formatCurrency";

interface MenuListProps {
  menuItems: MenuItem[] | undefined;
  cart: Map<number, number>; // Map of menu_item_id to quantity
  onQuantityChange: (itemId: number, newQuantity: number) => void;
  isLoading?: boolean;
}

export default function MenuList({
  menuItems,
  cart,
  onQuantityChange,
  isLoading = false,
}: MenuListProps) {
  if (!menuItems) {
    return null;
  }

  // Group menu items by category
  const itemsByCategory = useMemo(() => {
    const grouped = new Map<string, MenuItem[]>();

    menuItems.forEach((item) => {
      // Ensure category is always a string
      let categoryName: string;
      if (typeof item.category === "string") {
        categoryName = item.category || "Other";
      } else if (
        item.category &&
        typeof item.category === "object" &&
        "name" in item.category
      ) {
        // Handle case where category is an object with a name property
        categoryName = String(
          (item.category as { name: string }).name || "Other"
        );
      } else {
        categoryName = "Other";
      }

      // Ensure categoryName is always a string (safety check)
      categoryName = String(categoryName);

      if (!grouped.has(categoryName)) {
        grouped.set(categoryName, []);
      }
      grouped.get(categoryName)!.push(item);
    });

    return grouped;
  }, [menuItems]);

  const handleIncrement = (itemId: number) => {
    const currentQty = cart.get(itemId) || 0;
    onQuantityChange(itemId, currentQty + 1);
  };

  const handleDecrement = (itemId: number) => {
    const currentQty = cart.get(itemId) || 0;
    if (currentQty > 0) {
      onQuantityChange(itemId, currentQty - 1);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-coffee-brown border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-neutral-text-light">Loading menu...</p>
        </div>
      </div>
    );
  }

  if (menuItems.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <p className="text-neutral-text-light">No menu items available</p>
      </div>
    );
  }

  return (
    <div className="p-4 pb-32 space-y-6">
      {Array.from(itemsByCategory.entries()).map(
        ([category, items], categoryIndex) => (
          <div
            key={`category-${categoryIndex}-${category}`}
            className="space-y-3"
          >
            {/* Category Header */}
            <h2 className="text-lg font-semibold text-coffee-brown sticky top-0 bg-neutral-background py-2 z-10">
              {category}
            </h2>

            {/* Category Items */}
            <div className="space-y-3">
              {items.map((item) => {
                const quantity = cart.get(item.id) || 0;
                const isAvailable = item.is_available;

                return (
                  <div
                    key={item.id}
                    className={`
                    bg-off-white border border-neutral-border rounded-lg p-4
                    transition-all duration-200
                    ${!isAvailable ? "opacity-50" : "hover:shadow-sm"}
                  `}
                  >
                    {/* Item Header: Name and Price */}
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-base font-semibold text-neutral-text-dark flex-1">
                        {item.name}
                      </h3>
                      <span className="text-base font-semibold text-coffee-brown ml-4">
                        {formatCurrency(item.price)}
                      </span>
                    </div>

                    {/* Description */}
                    {item.description && (
                      <p className="text-sm text-neutral-text-light mb-3">
                        {item.description}
                      </p>
                    )}

                    {/* Out of Stock Badge or Quantity Controls */}
                    <div className="flex items-center justify-end mt-3">
                      {!isAvailable ? (
                        <span className="inline-flex items-center px-3 py-1 rounded-full bg-error/10 text-error text-sm font-medium">
                          Out of Stock
                        </span>
                      ) : (
                        <div className="flex items-center gap-3">
                          {/* Decrement Button */}
                          <button
                            onClick={() => handleDecrement(item.id)}
                            disabled={quantity === 0}
                            className="
                            w-10 h-10 rounded-full
                            flex items-center justify-center
                            bg-cream border-2 border-coffee-light
                            text-coffee-brown font-bold text-lg
                            transition-all duration-200
                            hover:bg-coffee-light hover:text-white
                            disabled:opacity-30 disabled:cursor-not-allowed
                            active:scale-95
                          "
                            aria-label="Decrease quantity"
                          >
                            &minus;
                          </button>

                          {/* Quantity Display */}
                          <span className="text-lg font-semibold text-neutral-text-dark w-8 text-center">
                            {quantity}
                          </span>

                          {/* Increment Button */}
                          <button
                            onClick={() => handleIncrement(item.id)}
                            className="
                            w-10 h-10 rounded-full
                            flex items-center justify-center
                            bg-coffee-brown border-2 border-coffee-brown
                            text-cream font-bold text-lg
                            transition-all duration-200
                            hover:bg-coffee-dark hover:border-coffee-dark
                            active:scale-95
                          "
                            aria-label="Increase quantity"
                          >
                            +
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )
      )}
    </div>
  );
}
