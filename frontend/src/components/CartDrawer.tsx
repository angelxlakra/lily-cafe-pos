// ========================================
// Cart Drawer Component
// Slide-up drawer for cart review and checkout
// ========================================

import { useEffect, useState } from 'react';
import type { MenuItem } from '../types';
import { formatCurrency } from '../utils/formatCurrency';

interface CartItem {
  menuItem: MenuItem;
  quantity: number;
  is_parcel: boolean;
}

interface CartDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  tableNumber: number;
  cartItems: CartItem[];
  onQuantityChange: (itemId: number, newQuantity: number) => void;
  onParcelChange: (itemId: number, isParcel: boolean) => void;
  onRemoveItem: (itemId: number) => void;
  onSaveOrder: () => void;
  isSaving?: boolean;
  gstRatePercent?: number;
  /** Instruction for the kitchen/bar, printed in the NOTES section of the chit */
  notes?: string;
  onNotesChange?: (notes: string) => void;
  /** Items already sent for this table's active order (shown for context on review) */
  alreadySentCount?: number;
}

export default function CartDrawer({
  isOpen,
  onClose,
  tableNumber,
  cartItems,
  onQuantityChange,
  onParcelChange,
  onRemoveItem,
  onSaveOrder,
  isSaving = false,
  gstRatePercent = 5,
  notes = '',
  onNotesChange,
  alreadySentCount = 0,
}: CartDrawerProps) {
  // Two steps: edit the cart, then review the full order before it goes to the kitchen
  const [step, setStep] = useState<'cart' | 'review'>('cart');
  const isReview = step === 'review';

  // Always reopen on the cart, and fall back to it if the cart empties
  useEffect(() => {
    if (!isOpen || cartItems.length === 0) setStep('cart');
  }, [isOpen, cartItems.length]);

  // Back from review goes to the cart; from the cart, closes the drawer
  const handleDismiss = () => {
    if (isSaving) return;
    if (isReview) setStep('cart');
    else onClose();
  };
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
        handleDismiss();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  });

  if (!isOpen) {
    return null;
  }

  if (isReview) {
    // Group like the printed chits: kitchen items and bar items go on separate chits
    const groups = [
      { label: 'Kitchen', items: cartItems.filter((i) => !i.menuItem.is_beverage) },
      { label: 'Bar', items: cartItems.filter((i) => i.menuItem.is_beverage) },
    ].filter((g) => g.items.length > 0);
    const itemCount = cartItems.reduce((sum, i) => sum + i.quantity, 0);

    return (
      <div
        className="fixed inset-0 z-[70] h-[100dvh] bg-off-white flex flex-col animate-fade-in"
        role="dialog"
        aria-modal="true"
        aria-labelledby="review-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-neutral-border bg-white">
          <div>
            <h2 id="review-title" className="text-xl font-semibold text-neutral-text-dark">
              Review Table {tableNumber}
            </h2>
            <p className="text-sm text-neutral-text-light">
              {itemCount} {itemCount === 1 ? 'item' : 'items'} to send
              {alreadySentCount > 0 && ` · ${alreadySentCount} already sent earlier`}
            </p>
          </div>
        </div>

        {/* Full order - scrollable */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          {groups.map((group) => (
            <section key={group.label}>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-text-light mb-2">
                {group.label}
              </h3>
              <ul className="bg-white border border-neutral-border rounded-lg divide-y divide-neutral-border">
                {group.items.map(({ menuItem, quantity, is_parcel }) => (
                  <li key={menuItem.id} className="flex items-center gap-3 px-3 py-3">
                    <span className="min-w-[2.5rem] text-center text-xl font-bold text-coffee-brown">
                      {quantity}×
                    </span>
                    <span className="flex-1 text-base font-medium text-neutral-text-dark">
                      {menuItem.name}
                      {is_parcel && (
                        <span className="ml-2 inline-block rounded bg-coffee-brown/10 px-1.5 py-0.5 text-xs font-semibold text-coffee-brown">
                          PARCEL
                        </span>
                      )}
                    </span>
                    <span className="text-sm text-neutral-text-light">
                      {formatCurrency(menuItem.price * quantity)}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ))}

          {/* Kitchen Notes (Optional) — printed on the order chit */}
          <div>
            <label htmlFor="order-notes" className="block text-sm font-medium text-neutral-text-dark mb-2">
              Notes for kitchen <span className="text-neutral-text-light">(optional)</span>
            </label>
            <textarea
              id="order-notes"
              value={notes}
              onChange={(e) => onNotesChange?.(e.target.value)}
              placeholder="e.g. no onion, extra spicy, less sugar..."
              rows={2}
              maxLength={500}
              className="w-full px-4 py-2.5 border border-neutral-border rounded-lg
                       focus:outline-none focus:ring-2 focus:ring-coffee-brown
                       text-base text-neutral-text-dark placeholder:text-neutral-text-light
                       resize-none"
              disabled={isSaving}
            />
            <p className="mt-1 text-xs text-neutral-text-light">
              Printed on the kitchen/bar chit for these items.
            </p>
          </div>

          {/* Totals */}
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-neutral-text-light">Subtotal</span>
              <span className="text-neutral-text-dark">{formatCurrency(subtotal)}</span>
            </div>
            {gstRatePercent > 0 && (
              <>
                <div className="flex justify-between">
                  <span className="text-neutral-text-light">SGST ({gstRateLabel}%)</span>
                  <span className="text-neutral-text-dark">{formatCurrency(sgstAmount)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-text-light">CGST ({gstRateLabel}%)</span>
                  <span className="text-neutral-text-dark">{formatCurrency(cgstAmount)}</span>
                </div>
              </>
            )}
            <div className="flex justify-between pt-2 border-t border-neutral-border text-lg">
              <span className="font-semibold text-neutral-text-dark">Total</span>
              <span className="font-bold font-heading text-coffee-brown">{formatCurrency(total)}</span>
            </div>
          </div>
        </div>

        {/* Actions - pinned */}
        <div className="flex gap-3 border-t border-neutral-border bg-white p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
          <button
            onClick={() => setStep('cart')}
            disabled={isSaving}
            className="btn-secondary h-12 px-5 disabled:opacity-50"
          >
            Edit
          </button>
          <button
            onClick={onSaveOrder}
            disabled={isSaving}
            className="btn-primary flex-1 h-12"
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
                  Sending...
                </span>
              ) : (
                'Send to Kitchen'
              )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-[60] animate-fade-in"
        onClick={handleDismiss}
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
            cartItems.map(({ menuItem, quantity, is_parcel }) => (
              <div
                key={menuItem.id}
                className="bg-cream border border-neutral-border rounded-lg p-3"
              >
                {/* Item Name */}
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-base font-medium text-neutral-text-dark flex-1">
                    {menuItem.name}
                    {is_parcel && (
                      <span className="ml-2 text-sm text-coffee-brown">(Parcel)</span>
                    )}
                  </h3>
                  <button
                    onClick={() => onRemoveItem(menuItem.id)}
                    className="ml-2 text-error hover:text-error/80 transition-colors"
                    aria-label={`Remove ${menuItem.name}`}
                  >
                    <span className="text-xl" aria-hidden="true">&times;</span>
                  </button>
                </div>

                {/* Parcel Checkbox */}
                <div className="flex items-center gap-2 mb-3 p-2 bg-white border border-neutral-border rounded-lg">
                  <input
                    id={`parcel-${menuItem.id}`}
                    type="checkbox"
                    checked={is_parcel}
                    onChange={(e) => onParcelChange(menuItem.id, e.target.checked)}
                    disabled={isSaving}
                    className="w-4 h-4 text-coffee-brown border-neutral-border rounded
                             focus:ring-2 focus:ring-coffee-brown cursor-pointer
                             disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                  <label
                    htmlFor={`parcel-${menuItem.id}`}
                    className="flex-1 text-sm font-medium text-neutral-text-dark cursor-pointer select-none"
                  >
                    Mark as Parcel
                  </label>
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

        {/* Footer - Total and Review */}
        {cartItems.length > 0 && (
          <div className="border-t border-neutral-border bg-white p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
            <button
              onClick={() => setStep('review')}
              className="btn-primary w-full h-12 flex items-center justify-between px-5"
            >
              <span>Review Order</span>
              <span className="font-bold">{formatCurrency(total)}</span>
            </button>
          </div>
        )}
      </div>
    </>
  );
}
