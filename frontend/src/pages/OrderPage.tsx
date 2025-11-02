// ========================================
// Order Page Component
// Main waiter interface for taking orders
// ========================================

import { useState, useEffect, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useMenuItems } from "../hooks/useMenu";
import { useActiveOrders, useCreateOrUpdateOrder } from "../hooks/useOrders";
import { useAppConfig } from "../hooks/useConfig";
import MenuList from "../components/MenuList";
import FloatingCartButton from "../components/FloatingCartButton";
import CartDrawer from "../components/CartDrawer";
import BottomNav from "../components/BottomNav";
import type { MenuItem } from "../types";
import { ArrowLeft } from "@phosphor-icons/react";

export default function OrderPage() {
  const { tableNumber: tableNumberParam } = useParams<{
    tableNumber: string;
  }>();
  const navigate = useNavigate();

  const tableNumber = parseInt(tableNumberParam || "0", 10);

  // State
  const [cart, setCart] = useState<Map<number, number>>(new Map());
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [showSuccessToast, setShowSuccessToast] = useState(false);

  // Data fetching
  const {
    data: menuItems,
    isLoading: isLoadingMenu,
    error: menuError,
  } = useMenuItems({ available_only: true });
  const { data: activeOrders, isLoading: isLoadingOrders } =
    useActiveOrders();
  const { data: appConfig } = useAppConfig();
  const { mutate: createOrUpdateOrder, isPending: isSavingOrder } =
    useCreateOrUpdateOrder();

  const items = menuItems || [];
  const orders = activeOrders || [];

  // Find existing order for this table
  const existingOrder = useMemo(() => {
    return orders.find((order) => order.table_number === tableNumber);
  }, [orders, tableNumber]);

  // Calculate cart totals
  const cartItems = useMemo(() => {
    return Array.from(cart.entries())
      .map(([itemId, quantity]) => {
        const menuItem = items.find((item) => item.id === itemId);
        if (!menuItem || quantity === 0) return null;
        return { menuItem, quantity };
      })
      .filter(
        (item): item is { menuItem: MenuItem; quantity: number } =>
          item !== null
      );
  }, [cart, items]);

  const gstRatePercent = appConfig?.gst_rate ?? 18;
  const gstRate = gstRatePercent / 100;
  const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);
  const subtotal = cartItems.reduce(
    (sum, item) => sum + item.menuItem.price * item.quantity,
    0
  );
  const gstAmount = Math.round(subtotal * gstRate);
  const total = subtotal + gstAmount;

  // Handlers
  const handleQuantityChange = (itemId: number, newQuantity: number) => {
    setCart((prev) => {
      const updated = new Map(prev);
      if (newQuantity <= 0) {
        updated.delete(itemId);
      } else {
        updated.set(itemId, newQuantity);
      }
      return updated;
    });
  };

  const handleRemoveItem = (itemId: number) => {
    setCart((prev) => {
      const updated = new Map(prev);
      updated.delete(itemId);
      return updated;
    });
  };

  const handleOpenDrawer = () => {
    setIsDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setIsDrawerOpen(false);
  };

  const handleSaveOrder = () => {
    if (cartItems.length === 0) {
      return;
    }

    const orderData = {
      table_number: tableNumber,
      items: cartItems.map(({ menuItem, quantity }) => ({
        menu_item_id: menuItem.id,
        quantity,
      })),
    };

    createOrUpdateOrder(orderData, {
      onSuccess: () => {
        // Show success toast
        setShowSuccessToast(true);
        setTimeout(() => setShowSuccessToast(false), 3000);

        // Clear cart
        setCart(new Map());

        // Close drawer
        setIsDrawerOpen(false);

        // Navigate back to tables after a short delay
        setTimeout(() => {
          navigate("/tables");
        }, 1500);
      },
      onError: (error) => {
        console.error("Failed to save order:", error);
        alert("Failed to save order. Please try again.");
      },
    });
  };

  // Redirect if invalid table number
  useEffect(() => {
    if (!tableNumber || tableNumber < 1) {
      navigate("/tables");
    }
  }, [tableNumber, navigate]);

  // Loading state
  if (isLoadingMenu || isLoadingOrders) {
    return (
      <div className="min-h-screen bg-neutral-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-coffee-brown border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-neutral-text-light">Loading...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (menuError) {
    return (
      <div className="min-h-screen bg-neutral-background flex items-center justify-center p-4">
        <div className="bg-error/10 border border-error rounded-lg p-6 max-w-md">
          <h2 className="text-lg font-semibold text-error mb-2">
            Error Loading Menu
          </h2>
          <p className="text-neutral-text-dark mb-4">
            {menuError instanceof Error
              ? menuError.message
              : "Failed to load menu items"}
          </p>
          <button
            onClick={() => navigate("/tables")}
            className="btn-primary"
          >
            Back to Tables
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-background pb-16">
      {/* Header */}
      <header className="bg-coffee-brown text-cream p-4 sticky top-0 z-30 shadow-md">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate("/tables")}
            className="flex items-center gap-2 hover:text-cream/80 transition-colors"
            aria-label="Back to tables"
          >
            <ArrowLeft size={22} weight="duotone" />
            <span className="font-medium">Back</span>
          </button>
          <h1 className="text-lg font-semibold">
            Table {tableNumber}
            {existingOrder && (
              <span className="ml-2 text-sm font-normal text-cream/80">
                (Active Order)
              </span>
            )}
          </h1>
          <div className="w-20"></div> {/* Spacer for centering */}
        </div>
      </header>

      {/* Menu List */}
      <main>
        {items.length === 0 ? (
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <p className="text-neutral-text-light mb-4">
                No menu items available
              </p>
              <button
                onClick={() => navigate("/tables")}
                className="btn-primary"
              >
                Back to Tables
              </button>
            </div>
          </div>
        ) : (
          <MenuList
            menuItems={items}
            cart={cart}
            onQuantityChange={handleQuantityChange}
          />
        )}
      </main>

      {/* Floating Cart Button */}
      <FloatingCartButton
        itemCount={totalItems}
        totalAmount={total}
        onClick={handleOpenDrawer}
      />

      {/* Cart Drawer */}
      <CartDrawer
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
        tableNumber={tableNumber}
        cartItems={cartItems}
        onQuantityChange={handleQuantityChange}
        onRemoveItem={handleRemoveItem}
        onSaveOrder={handleSaveOrder}
        isSaving={isSavingOrder}
        gstRatePercent={gstRatePercent}
      />

      {/* Bottom Navigation */}
      <BottomNav />

      {/* Success Toast */}
      {showSuccessToast && (
        <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-[100] animate-slide-down">
          <div className="bg-success text-white px-6 py-3 rounded-lg shadow-xl flex items-center gap-2">
            <span></span>
            <span className="font-medium">
              Order saved for Table {tableNumber}!
            </span>
          </div>
        </div>
      )}

      {/* Custom animations */}
      <style>{`
        @keyframes slide-down {
          from {
            transform: translateX(-50%) translateY(-100%);
            opacity: 0;
          }
          to {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
          }
        }

        .animate-slide-down {
          animation: slide-down 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
      `}</style>
    </div>
  );
}
