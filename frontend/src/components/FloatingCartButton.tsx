// ========================================
// Floating Cart Button Component
// Fixed button showing cart count and total
// ========================================

import { formatCurrency } from "../utils/formatCurrency";
import { ShoppingCartSimple } from "@phosphor-icons/react";

interface FloatingCartButtonProps {
  itemCount: number;
  totalAmount: number;
  onClick: () => void;
}

export default function FloatingCartButton({
  itemCount,
  totalAmount,
  onClick,
}: FloatingCartButtonProps) {
  // Don't render if cart is empty
  if (itemCount === 0) {
    return null;
  }

  return (
    <button
      onClick={onClick}
      className="
        fixed bottom-20 right-5
        min-w-[120px] h-[60px]
        bg-coffee-brown text-cream
        rounded-2xl shadow-2xl
        px-4 py-2
        flex flex-col items-center justify-center
        transition-all duration-200
        hover:bg-coffee-dark hover:scale-105
        active:scale-100
        z-50
        cursor-pointer
      "
      aria-label={`View cart: ${itemCount} items, total ${formatCurrency(
        totalAmount
      )}`}
    >
      <div className="flex items-center gap-2 text-sm font-semibold">
        <ShoppingCartSimple size={20} weight="duotone" />
        <span>
          {itemCount} {itemCount === 1 ? "item" : "items"}
        </span>
      </div>
      <div className="text-sm font-bold mt-0.5">
        {formatCurrency(totalAmount)}
      </div>
    </button>
  );
}
