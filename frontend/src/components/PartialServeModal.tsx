// ========================================
// Partial Serve Modal Component
// Allows admin to mark a specific quantity of items as served
// ========================================

import { useState } from "react";
import { CheckCircle } from "@phosphor-icons/react";
import type { OrderItem } from "../types";

interface PartialServeModalProps {
  item: OrderItem;
  orderId: number;
  onServe: (orderId: number, itemId: number, quantityToServe: number) => void;
  onClose: () => void;
}

export default function PartialServeModal({
  item,
  orderId,
  onServe,
  onClose,
}: PartialServeModalProps) {
  const remainingQuantity = item.quantity - item.quantity_served;
  const [quantityToServe, setQuantityToServe] = useState(remainingQuantity);

  const handleServe = () => {
    if (quantityToServe > 0 && quantityToServe <= remainingQuantity) {
      onServe(orderId, item.id, quantityToServe);
      onClose();
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                   w-full max-w-md bg-off-white rounded-2xl shadow-2xl z-60
                   border border-neutral-border overflow-hidden"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{ background: 'linear-gradient(135deg, #3d7a50, #2e6040)' }}
          className="flex items-center gap-3 px-5 py-4"
        >
          <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
            <CheckCircle size={20} weight="duotone" color="white" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-white font-heading italic text-base font-bold leading-tight">
              Serve Items
            </h2>
            <p className="text-white/70 text-xs mt-0.5">{item.menu_item_name}</p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-white/60 hover:text-white text-xl leading-none ml-auto flex-shrink-0"
          >
            &times;
          </button>
        </div>

        {/* Body */}
        <div className="p-5 flex flex-col gap-5">
          {/* Status */}
          <div className="bg-cream border border-neutral-border rounded-xl p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-neutral-text-light text-sm">Already Served</span>
              <span className="font-semibold text-coffee-dark">
                {item.quantity_served} / {item.quantity}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-neutral-text-light text-sm">Remaining</span>
              <span className="font-semibold text-coffee-dark">{remainingQuantity}</span>
            </div>
          </div>

          {/* Slider */}
          <div>
            <label className="block text-sm font-medium text-neutral-text-dark mb-3">
              How many items to serve now?
            </label>

            <div className="text-center mb-4">
              <span className="text-5xl font-bold font-heading text-coffee-brown">
                {quantityToServe}
              </span>
              <span className="text-2xl text-neutral-text-light ml-2">
                / {remainingQuantity}
              </span>
            </div>

            <input
              type="range"
              min="0"
              max={remainingQuantity}
              value={quantityToServe}
              onChange={(e) => setQuantityToServe(parseInt(e.target.value, 10))}
              className="w-full h-3 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right,
                  #c04e30 0%,
                  #c04e30 ${(quantityToServe / remainingQuantity) * 100}%,
                  #e8d0c0 ${(quantityToServe / remainingQuantity) * 100}%,
                  #e8d0c0 100%)`
              }}
            />

            <div className="flex gap-2 mt-4">
              <button
                onClick={() => setQuantityToServe(0)}
                className="flex-1 py-2 px-3 text-sm font-medium text-neutral-text-dark
                           bg-cream border border-neutral-border rounded-lg hover:bg-neutral-border/50
                           transition-colors"
              >
                None
              </button>
              <button
                onClick={() => setQuantityToServe(Math.floor(remainingQuantity / 2))}
                className="flex-1 py-2 px-3 text-sm font-medium text-neutral-text-dark
                           bg-cream border border-neutral-border rounded-lg hover:bg-neutral-border/50
                           transition-colors"
                disabled={remainingQuantity < 2}
              >
                Half
              </button>
              <button
                onClick={() => setQuantityToServe(remainingQuantity)}
                className="flex-1 py-2 px-3 text-sm font-medium text-neutral-text-dark
                           bg-cream border border-neutral-border rounded-lg hover:bg-neutral-border/50
                           transition-colors"
              >
                All
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-neutral-border p-4 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-3 px-4 text-neutral-text-dark font-medium
                       bg-cream border border-neutral-border rounded-xl hover:bg-neutral-border/50
                       transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleServe}
            disabled={quantityToServe === 0}
            className="flex-1 py-3 px-4 text-white font-medium
                       bg-lily-green rounded-xl hover:bg-lily-green-light
                       transition-colors disabled:opacity-50
                       disabled:cursor-not-allowed"
          >
            Serve {quantityToServe > 0 ? quantityToServe : ''}
          </button>
        </div>
      </div>
    </>
  );
}
