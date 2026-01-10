// ========================================
// Edit Order Modal Component
// Admin can edit order items and change table number
// ========================================

import { useState, useEffect } from 'react';
import { X, Plus, Minus, Trash, MagnifyingGlass } from '@phosphor-icons/react';
import { useUpdateOrder } from '../hooks/useOrders';
import { useMenu } from '../hooks/useMenu';
import { useAppConfig } from '../hooks/useConfig';
import { formatCurrency } from '../utils/formatCurrency';
import type { Order, MenuItem as MenuItemType } from '../types';

interface EditOrderModalProps {
  order: Order;
  onClose: () => void;
  onCancelOrder?: () => void;
}

interface EditOrderItem {
  menu_item_id: number;
  menu_item_name: string;
  quantity: number;
  unit_price: number;
  is_parcel: boolean;
}

export default function EditOrderModal({ order, onClose, onCancelOrder }: EditOrderModalProps) {
  const menu = useMenu();
  const { data: config } = useAppConfig();
  const updateOrder = useUpdateOrder();

  const [items, setItems] = useState<EditOrderItem[]>([]);
  const [tableNumber, setTableNumber] = useState(order.table_number);
  const [customerName, setCustomerName] = useState(order.customer_name || '');
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Initialize items from existing order
  useEffect(() => {
    const initialItems = order.order_items.map(item => ({
      menu_item_id: item.menu_item_id,
      menu_item_name: item.menu_item_name,
      quantity: item.quantity,
      unit_price: item.unit_price,
      is_parcel: item.is_parcel || false,
    }));
    setItems(initialItems);
  }, [order]);

  const max_tables = config?.max_tables || 50;

  // Calculate totals
  const subtotal = items.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0);
  const gstRate = config?.gst_rate || 18;
  const gstAmount = Math.floor(subtotal * gstRate / 100);
  const total = subtotal + gstAmount;

  const handleQuantityChange = (index: number, delta: number) => {
    setItems(prev => {
      const newItems = [...prev];
      const newQuantity = newItems[index].quantity + delta;

      if (newQuantity <= 0) {
        // Remove item if quantity becomes 0
        return newItems.filter((_, i) => i !== index);
      }

      newItems[index] = { ...newItems[index], quantity: newQuantity };
      return newItems;
    });
  };

  const handleRemoveItem = (index: number) => {
    setItems(prev => prev.filter((_, i) => i !== index));
  };

  const handleAddMenuItem = (menuItem: MenuItemType) => {
    setItems(prev => {
      // Check if item already exists
      const existingIndex = prev.findIndex(item => item.menu_item_id === menuItem.id);

      if (existingIndex >= 0) {
        // Increment quantity if exists
        const newItems = [...prev];
        newItems[existingIndex] = {
          ...newItems[existingIndex],
          quantity: newItems[existingIndex].quantity + 1,
        };
        return newItems;
      }

      // Add new item
      return [...prev, {
        menu_item_id: menuItem.id,
        menu_item_name: menuItem.name,
        quantity: 1,
        unit_price: menuItem.price,
        is_parcel: false,
      }];
    });
  };

  const handleSubmit = async () => {
    if (items.length === 0) {
      setError('Order must have at least one item');
      return;
    }

    setError(null);

    try {
      await updateOrder.mutateAsync({
        id: order.id,
        data: {
          items: items.map(item => ({
            menu_item_id: item.menu_item_id,
            quantity: item.quantity,
            is_parcel: item.is_parcel,
          })),
          customer_name: customerName || null,
          table_number: tableNumber !== order.table_number ? tableNumber : undefined,
        },
      });

      onClose();
    } catch (err: any) {
      // Handle API errors
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to update order';
      setError(errorMessage);
    }
  };

  const availableMenuItems = (menu.items.data || []).filter((item: MenuItemType) => item.is_available);

  const filteredMenuItems = availableMenuItems.filter((item: MenuItemType) => 
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-[60]"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                   w-full max-w-2xl max-h-[90vh] bg-off-white rounded-2xl shadow-2xl z-[70] overflow-hidden flex flex-col"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-border">
          <div>
            <h2 className="text-2xl font-bold text-neutral-text-dark">
              Edit Order #{order.order_number}
            </h2>
            <p className="text-sm text-muted mt-1">
              Modify items, customer name, or table number
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-neutral-background transition-colors"
            aria-label="Close"
          >
            <X size={24} weight="bold" className="text-neutral-text-light" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Error Message */}
          {error && (
            <div className="bg-error/10 border border-error rounded-lg p-4">
              <p className="text-error font-medium text-sm">{error}</p>
            </div>
          )}

          {/* Table Number Selection */}
          <div>
            <label className="block text-sm font-semibold text-neutral-text-dark mb-2">
              Table Number
            </label>
            <select
              value={tableNumber}
              onChange={(e) => setTableNumber(Number(e.target.value))}
              className="w-full px-4 py-3 bg-white border border-neutral-border rounded-lg
                       focus:outline-none focus:ring-2 focus:ring-coffee-brown text-neutral-text-dark"
            >
              {Array.from({ length: max_tables }, (_, i) => i + 1).map(num => (
                <option key={num} value={num}>
                  Table {num}
                </option>
              ))}
            </select>
            {tableNumber !== order.table_number && (
              <p className="text-xs text-muted mt-1">
                ⚠️ Moving from Table {order.table_number} to Table {tableNumber}
              </p>
            )}
          </div>

          {/* Customer Name */}
          <div>
            <label className="block text-sm font-semibold text-neutral-text-dark mb-2">
              Customer Name (Optional)
            </label>
            <input
              type="text"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              placeholder="Enter customer name"
              className="w-full px-4 py-3 bg-white border border-neutral-border rounded-lg
                       focus:outline-none focus:ring-2 focus:ring-coffee-brown text-neutral-text-dark placeholder:text-muted"
            />
          </div>

          {/* Current Items */}
          <div>
            <h3 className="text-sm font-semibold text-neutral-text-dark mb-3">
              Order Items
            </h3>
            {items.length === 0 ? (
              <div className="text-center py-8 text-muted">
                No items in order. Add items from the menu below.
              </div>
            ) : (
              <div className="space-y-2">
                {items.map((item, index) => (
                  <div
                    key={index}
                    className={`flex flex-col bg-white border rounded-lg p-4 ${
                      item.is_parcel ? 'border-coffee-brown/30' : 'border-neutral-border'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex-1">
                        <p className="font-medium text-neutral-text-dark">
                          {item.menu_item_name}
                          {item.is_parcel && (
                            <span className="ml-2 text-sm text-coffee-brown">(Parcel)</span>
                          )}
                        </p>
                        <p className="text-sm text-muted">{formatCurrency(item.unit_price)} each</p>
                      </div>
                    </div>

                    {/* Parcel Checkbox */}
                    <div className="flex items-center gap-2 mb-3 p-2 bg-cream border border-neutral-border rounded-lg">
                      <input
                        id={`edit-parcel-${index}`}
                        type="checkbox"
                        checked={item.is_parcel}
                        onChange={(e) => {
                          const newItems = [...items];
                          newItems[index] = { ...newItems[index], is_parcel: e.target.checked };
                          setItems(newItems);
                        }}
                        className="w-4 h-4 text-coffee-brown border-neutral-border rounded
                                 focus:ring-2 focus:ring-coffee-brown cursor-pointer"
                      />
                      <label
                        htmlFor={`edit-parcel-${index}`}
                        className="flex-1 text-sm font-medium text-neutral-text-dark cursor-pointer select-none"
                      >
                        Mark as Parcel
                      </label>
                    </div>

                    <div className="flex items-center gap-3">
                      {/* Quantity Controls */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleQuantityChange(index, -1)}
                          className="w-8 h-8 flex items-center justify-center rounded-lg
                                   bg-neutral-background hover:bg-coffee-brown hover:text-cream transition-colors"
                        >
                          <Minus size={16} weight="bold" />
                        </button>
                        <span className="w-8 text-center font-semibold text-neutral-text-dark">
                          {item.quantity}
                        </span>
                        <button
                          onClick={() => handleQuantityChange(index, 1)}
                          className="w-8 h-8 flex items-center justify-center rounded-lg
                                   bg-neutral-background hover:bg-coffee-brown hover:text-cream transition-colors"
                        >
                          <Plus size={16} weight="bold" />
                        </button>
                      </div>

                      {/* Subtotal */}
                      <div className="w-24 text-right font-semibold text-neutral-text-dark">
                        {formatCurrency(item.unit_price * item.quantity)}
                      </div>

                      {/* Remove Button */}
                      <button
                        onClick={() => handleRemoveItem(index)}
                        className="w-8 h-8 flex items-center justify-center rounded-lg
                                 hover:bg-error/10 hover:text-error transition-colors"
                        aria-label="Remove item"
                      >
                        <Trash size={18} weight="bold" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Add Items from Menu */}
          <div>
            <h3 className="text-sm font-semibold text-neutral-text-dark mb-3">
              Add Items from Menu
            </h3>

            {/* Search Box */}
            <div className="relative mb-3">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlass size={16} className="text-neutral-text-light" />
              </div>
              <input
                type="text"
                placeholder="Search menu items..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white border border-neutral-border rounded-lg
                         focus:outline-none focus:ring-2 focus:ring-coffee-brown text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto p-1">
              {filteredMenuItems.map((menuItem: MenuItemType) => (
                <button
                  key={menuItem.id}
                  onClick={() => handleAddMenuItem(menuItem)}
                  className="text-left p-3 bg-white border border-neutral-border rounded-lg
                           hover:border-coffee-brown hover:bg-coffee-brown/5 transition-all"
                >
                  <p className="font-medium text-sm text-neutral-text-dark truncate">
                    {menuItem.name}
                  </p>
                  <p className="text-xs text-coffee-brown font-semibold mt-1">
                    {formatCurrency(menuItem.price)}
                  </p>
                </button>
              ))}
              {filteredMenuItems.length === 0 && (
                <div className="col-span-2 text-center py-4 text-sm text-muted">
                  No items found matching "{searchQuery}"
                </div>
              )}
            </div>
          </div>

          {/* Price Summary */}
          <div className="border-t border-neutral-border pt-4 space-y-2">
            <div className="flex justify-between text-neutral-text-light">
              <span>Subtotal:</span>
              <span className="font-semibold">{formatCurrency(subtotal)}</span>
            </div>
            <div className="flex justify-between text-neutral-text-light">
              <span>GST ({gstRate}%):</span>
              <span className="font-semibold">{formatCurrency(gstAmount)}</span>
            </div>
            <div className="flex justify-between text-xl font-bold text-coffee-brown border-t border-neutral-border pt-2">
              <span>Total:</span>
              <span>{formatCurrency(total)}</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t border-neutral-border bg-neutral-background/50 items-center">
          {onCancelOrder && order.status !== 'canceled' && (
            <button
              onClick={() => {
                onCancelOrder();
                onClose();
              }}
              disabled={updateOrder.isPending}
              className="py-2 px-3 text-xs text-error font-medium
                       bg-transparent border border-error/30 rounded-lg
                       hover:bg-error/10 hover:border-error
                       transition-all disabled:opacity-50
                       flex items-center gap-1.5"
            >
              <Trash size={14} weight="bold" />
              Cancel Order
            </button>
          )}
          <div className="flex-1"></div>
          <button
            onClick={onClose}
            disabled={updateOrder.isPending}
            className="py-3.5 px-6 text-neutral-text-dark font-semibold text-base
                     bg-white border-2 border-neutral-border rounded-xl
                     hover:bg-neutral-background hover:border-coffee-brown/30
                     shadow-sm hover:shadow-md
                     transition-all disabled:opacity-50"
          >
            Close
          </button>
          <button
            onClick={handleSubmit}
            disabled={updateOrder.isPending || items.length === 0}
            className="py-3.5 px-6 text-white font-semibold text-base
                     bg-coffee-brown rounded-xl hover:bg-coffee-dark
                     shadow-md hover:shadow-lg
                     transition-all disabled:opacity-50
                     disabled:cursor-not-allowed"
          >
            {updateOrder.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </>
  );
}
