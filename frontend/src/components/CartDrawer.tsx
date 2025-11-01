// ========================================
// Cart Drawer Component
// Slide-up drawer for cart review and checkout
// ========================================

import { useEffect } from 'react';
import type { MenuItem } from '../types';
import { formatCurrency } from '../utils/formatCurrency';

interface CartItem {
  menuItem: MenuItem;
  quantity: number;
}

interface CartDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  tableNumber: number;
  cartItems: CartItem[];
  onQuantityChange: (itemId: number, newQuantity: number) => void;
  onRemoveItem: (itemId: number) => void;
  onSaveOrder: () => void;
  isSaving?: boolean;
  gstRatePercent?: number;
}

export default function CartDrawer({
  isOpen,
  onClose,
  tableNumber,
  cartItems,
  onQuantityChange,
  onRemoveItem,
  onSaveOrder,
  isSaving = false,
  gstRatePercent = 18,
}: CartDrawerProps) {
  // Calculate totals
  const subtotal = cartItems.reduce(
    (sum, item) => sum + item.menuItem.price * item.quantity,
    0
  );
  const gstRate = gstRatePercent / 100;
  const gstAmount = Math.round(subtotal * gstRate);
  // Split GST into SGST and CGST (50/50)
  const sgstAmount = Math.round(gstAmount / 2);
  const cgstAmount = gstAmount - sgstAmount; // Ensure they add up exactly
  const total = subtotal + gstAmount;
  const halfGstRate = gstRatePercent / 2;
  const gstRateLabel = Number.isInteger(halfGstRate)
    ? halfGstRate
    : halfGstRate.toFixed(2);

  // Lock body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-[60] animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        className={`
          fixed bottom-0 left-0 right-0
          bg-off-white
          rounded-t-3xl shadow-2xl
          z-[70]
          max-h-[80vh]
          flex flex-col
          ${isOpen ? 'animate-slide-up' : ''}
        `}
        role="dialog"
        aria-modal="true"
        aria-labelledby="cart-drawer-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-neutral-border">
          <h2 id="cart-drawer-title" className="text-lg font-semibold text-neutral-text-dark">
            Table {tableNumber} Order
          </h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-neutral-border transition-colors"
            aria-label="Close cart"
          >
            <span className="text-xl text-neutral-text-light" aria-hidden="true">&times;</span>
          </button>
        </div>

        {/* Cart Items - Scrollable */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {cartItems.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-neutral-text-light">Your cart is empty</p>
            </div>
          ) : (
            cartItems.map(({ menuItem, quantity }) => (
              <div
                key={menuItem.id}
                className="bg-cream border border-neutral-border rounded-lg p-3"
              >
                {/* Item Name */}
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-base font-medium text-neutral-text-dark flex-1">
                    {menuItem.name}
                  </h3>
                  <button
                    onClick={() => onRemoveItem(menuItem.id)}
                    className="ml-2 text-error hover:text-error/80 transition-colors"
                    aria-label={`Remove ${menuItem.name}`}
                  >
                    <span className="text-xl" aria-hidden="true">&times;</span>
                  </button>
                </div>

                {/* Quantity Controls and Subtotal */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {/* Decrement */}
                    <button
                      onClick={() => onQuantityChange(menuItem.id, quantity - 1)}
                      disabled={quantity <= 1}
                      className="
                        w-8 h-8 rounded-full
                        flex items-center justify-center
                        bg-white border border-coffee-light
                        text-coffee-brown text-2xl font-bold
                        transition-colors
                        hover:bg-coffee-light hover:text-white
                        disabled:opacity-30 disabled:cursor-not-allowed
                      "
                      aria-label="Decrease quantity"
                    >
                      &minus;
                    </button>

                    {/* Quantity */}
                    <span className="text-base font-semibold text-neutral-text-dark w-6 text-center">
                      {quantity}
                    </span>

                    {/* Increment */}
                    <button
                      onClick={() => onQuantityChange(menuItem.id, quantity + 1)}
                      className="
                        w-8 h-8 rounded-full
                        flex items-center justify-center
                        bg-coffee-brown border border-coffee-brown
                        text-cream font-bold
                        transition-colors
                        hover:bg-coffee-dark
                      "
                      aria-label="Increase quantity"
                    >
                      +
                    </button>
                  </div>

                  {/* Item Subtotal */}
                  <span className="text-base font-semibold text-coffee-brown">
                    {formatCurrency(menuItem.price * quantity)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer - Totals and Save Button */}
        {cartItems.length > 0 && (
          <div className="border-t border-neutral-border bg-white p-4 space-y-3">
            {/* Subtotal */}
            <div className="flex justify-between text-sm">
              <span className="text-neutral-text-light">Subtotal:</span>
              <span className="font-semibold text-neutral-text-dark">
                {formatCurrency(subtotal)}
              </span>
            </div>

            {/* SGST */}
            <div className="flex justify-between text-sm">
              <span className="text-neutral-text-light">SGST ({gstRateLabel}%):</span>
              <span className="font-semibold text-neutral-text-dark">
                {formatCurrency(sgstAmount)}
              </span>
            </div>

            {/* CGST */}
            <div className="flex justify-between text-sm">
              <span className="text-neutral-text-light">CGST ({gstRateLabel}%):</span>
              <span className="font-semibold text-neutral-text-dark">
                {formatCurrency(cgstAmount)}
              </span>
            </div>

            {/* Divider */}
            <div className="border-t border-neutral-border"></div>

            {/* Total */}
            <div className="flex justify-between text-lg">
              <span className="font-semibold text-neutral-text-dark">Total:</span>
              <span className="font-bold text-coffee-brown">{formatCurrency(total)}</span>
            </div>

            {/* Save Order Button */}
            <button
              onClick={onSaveOrder}
              disabled={isSaving}
              className="
                btn w-full h-12
                bg-coffee-brown text-cream
                rounded-lg font-semibold
                hover:bg-coffee-dark
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-all duration-200
                active:scale-95
              "
            >
              {isSaving ? (
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
              ) : (
                'Save Order'
              )}
            </button>
          </div>
        )}
      </div>

      {/* Custom animations */}
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes slide-up {
          from {
            transform: translateY(100%);
          }
          to {
            transform: translateY(0);
          }
        }

        .animate-fade-in {
          animation: fade-in 0.2s ease-out;
        }

        .animate-slide-up {
          animation: slide-up 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
      `}</style>
    </>
  );
}
