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
      const categoryName = item.category?.name || "Other";

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
                    card p-4 fade-in
                    ${!isAvailable ? "opacity-50" : ""}
                  `}
                  >
                    {/* Item Header: Name, Veg/Non-veg Indicator, and Price */}
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-start gap-2 flex-1">
                        {/* Veg/Non-veg Indicator */}
                        <div className={`mt-1 w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                          item.is_vegetarian
                            ? "border-green-600"
                            : "border-red-600"
                        }`}>
                          <div className={`w-2 h-2 rounded-full ${
                            item.is_vegetarian
                              ? "bg-green-600"
                              : "bg-red-600"
                          }`}></div>
                        </div>
                        <h3 className="text-base font-semibold text-neutral-text-dark">
                          {item.name}
                        </h3>
                      </div>
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
                        <span className="badge px-4 py-2 bg-error/15 text-error border border-error/30">
                          Out of Stock
                        </span>
                      ) : (
                        <div className="flex items-center gap-3">
                          {/* Decrement Button */}
                          <button
                            onClick={() => handleDecrement(item.id)}
                            disabled={quantity === 0}
                            className="
                            w-11 h-11 rounded-full
                            flex items-center justify-center
                            bg-gradient-soft border-2 border-coffee-light/40
                            text-coffee-brown font-bold text-xl
                            shadow-soft
                            smooth-transition
                            hover:bg-coffee-light hover:text-white hover:border-coffee-light hover:shadow-medium
                            disabled:opacity-30 disabled:cursor-not-allowed disabled:shadow-none
                            active:scale-90
                          "
                            aria-label="Decrease quantity"
                          >
                            &minus;
                          </button>

                          {/* Quantity Display */}
                          <div className="min-w-[40px] h-11 flex items-center justify-center">
                            <span className="text-xl font-bold text-coffee-brown">
                              {quantity}
                            </span>
                          </div>

                          {/* Increment Button */}
                          <button
                            onClick={() => handleIncrement(item.id)}
                            className="
                            w-11 h-11 rounded-full
                            flex items-center justify-center
                            bg-gradient-primary border-2 border-coffee-brown
                            text-cream font-bold text-xl
                            shadow-medium
                            smooth-transition
                            hover:shadow-strong hover:scale-105
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
