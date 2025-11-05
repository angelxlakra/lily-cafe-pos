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
        min-w-[140px] h-[68px]
        bg-gradient-primary text-cream
        rounded-2xl shadow-strong
        px-5 py-3
        flex flex-col items-center justify-center
        smooth-transition
        hover:shadow-[0_12px_28px_rgba(111,78,55,0.4)]
        hover:scale-105
        active:scale-100
        z-50
        cursor-pointer
        border-2 border-coffee-light/30
        animate-pulse-subtle
      "
      aria-label={`View cart: ${itemCount} items, total ${formatCurrency(
        totalAmount
      )}`}
    >
      {/* Badge for item count */}
      <div className="absolute -top-2 -right-2 bg-lily-green text-white rounded-full w-8 h-8 flex items-center justify-center text-xs font-bold shadow-medium border-2 border-cream">
        {itemCount}
      </div>

      <div className="flex items-center gap-2 text-sm font-semibold">
        <ShoppingCartSimple size={22} weight="duotone" />
        <span className="font-heading">View Cart</span>
      </div>
      <div className="text-base font-bold mt-1">
        {formatCurrency(totalAmount)}
      </div>
    </button>
  );
}
