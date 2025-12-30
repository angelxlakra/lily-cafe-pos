// ========================================
// Edit Served Quantity Modal Component
// Allows admin to edit the absolute number of items served
// ========================================

import { useState } from "react";
import { OrderItem } from "../types";

interface EditServedQuantityModalProps {
  item: OrderItem;
  orderId: number;
  onEdit: (orderId: number, itemId: number, quantityServed: number) => void;
  onClose: () => void;
}

export default function EditServedQuantityModal({
  item,
  orderId,
  onEdit,
  onClose,
}: EditServedQuantityModalProps) {
  const [quantityServed, setQuantityServed] = useState(item.quantity_served);

  const handleEdit = () => {
    if (quantityServed >= 0 && quantityServed <= item.quantity) {
      onEdit(orderId, item.id, quantityServed);
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
                   w-full max-w-md bg-white rounded-2xl shadow-2xl z-60 p-6"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex flex-col gap-6">
          {/* Header */}
          <div>
            <h2 className="text-2xl font-heading font-bold text-coffee-dark mb-2">
              Edit Served Quantity
            </h2>
            <p className="text-neutral-text-light text-sm">
              {item.menu_item_name}
            </p>
          </div>

          {/* Status */}
          <div className="bg-neutral-background rounded-xl p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-neutral-text-light text-sm">Total Ordered</span>
              <span className="font-semibold text-coffee-dark">
                {item.quantity}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-neutral-text-light text-sm">Current Served</span>
              <span className="font-semibold text-coffee-dark">
                {item.quantity_served}
              </span>
            </div>
          </div>

          {/* Slider */}
          <div>
            <label className="block text-sm font-medium text-neutral-text-dark mb-3">
              Set total number of items served
            </label>

            {/* Quantity Display */}
            <div className="text-center mb-4">
              <span className="text-5xl font-bold font-heading text-coffee-brown">
                {quantityServed}
              </span>
              <span className="text-2xl text-neutral-text-light ml-2">
                / {item.quantity}
              </span>
            </div>

            {/* Slider Input */}
            <input
              type="range"
              min="0"
              max={item.quantity}
              value={quantityServed}
              onChange={(e) => setQuantityServed(parseInt(e.target.value, 10))}
              className="w-full h-3 bg-neutral-border rounded-lg appearance-none cursor-pointer
                         slider-thumb:appearance-none slider-thumb:w-6 slider-thumb:h-6
                         slider-thumb:rounded-full slider-thumb:bg-coffee-brown
                         slider-thumb:cursor-pointer slider-thumb:border-4 slider-thumb:border-white
                         slider-thumb:shadow-md"
              style={{
                background: `linear-gradient(to right,
                  rgb(139, 98, 72) 0%,
                  rgb(139, 98, 72) ${(quantityServed / item.quantity) * 100}%,
                  rgb(229, 231, 235) ${(quantityServed / item.quantity) * 100}%,
                  rgb(229, 231, 235) 100%)`
              }}
            />

            {/* Quick Selection Buttons */}
            <div className="flex gap-2 mt-4">
              <button
                onClick={() => setQuantityServed(0)}
                className="flex-1 py-2 px-3 text-sm font-medium text-neutral-text-dark
                           bg-neutral-background rounded-lg hover:bg-neutral-border
                           transition-colors"
              >
                None
              </button>
              <button
                onClick={() => setQuantityServed(Math.floor(item.quantity / 2))}
                className="flex-1 py-2 px-3 text-sm font-medium text-neutral-text-dark
                           bg-neutral-background rounded-lg hover:bg-neutral-border
                           transition-colors"
                disabled={item.quantity < 2}
              >
                Half
              </button>
              <button
                onClick={() => setQuantityServed(item.quantity)}
                className="flex-1 py-2 px-3 text-sm font-medium text-neutral-text-dark
                           bg-neutral-background rounded-lg hover:bg-neutral-border
                           transition-colors"
              >
                All
              </button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 py-3 px-4 text-neutral-text-dark font-medium
                         bg-neutral-background rounded-xl hover:bg-neutral-border
                         transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleEdit}
              className="flex-1 py-3 px-4 text-white font-medium
                         bg-coffee-brown rounded-xl hover:bg-coffee-dark
                         transition-colors"
            >
              Update
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
