// ========================================
// Edit Payments Modal Component
// Edit payment methods for completed orders
// ========================================

import { useState } from "react";
import { Trash } from "@phosphor-icons/react";
import { UpiIcon, CashIcon, CardIcon } from "./icons/PaymentIcons";
import { formatCurrency } from "../utils/formatCurrency";
import type {
  PaymentMethod,
  PaymentCreateRequest,
  Order,
} from "../types";

interface EditPaymentsModalProps {
  order: Order;
  onSave: (orderId: number, payments: PaymentCreateRequest[]) => void;
  onClose: () => void;
  isSaving?: boolean;
  onCancelOrder?: () => void;
}

export default function EditPaymentsModal({
  order,
  onSave,
  onClose,
  isSaving = false,
  onCancelOrder,
}: EditPaymentsModalProps) {
  const paymentIcons: Record<PaymentMethod, JSX.Element> = {
    upi: <UpiIcon size={32} weight="duotone" />,
    cash: <CashIcon size={32} weight="duotone" />,
    card: <CardIcon size={32} weight="duotone" />,
  };

  // Initialize with existing payments
  const [payments, setPayments] = useState<PaymentCreateRequest[]>(
    order.payments.map((p) => ({
      payment_method: p.payment_method,
      amount: p.amount,
    }))
  );

  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("upi");
  const [paymentAmount, setPaymentAmount] = useState("");
  const [error, setError] = useState("");

  const totalAmount = order.total_amount;
  const paymentsTotal = payments.reduce((sum, p) => sum + p.amount, 0);
  const remaining = totalAmount - paymentsTotal;
  const isValid = remaining === 0;

  const handleAddPayment = () => {
    setError("");

    const amount = parseInt(paymentAmount, 10) * 100;

    if (!paymentAmount || isNaN(amount) || amount <= 0) {
      setError("Please enter a valid amount");
      return;
    }

    if (amount > remaining && remaining > 0) {
      setError(
        `Amount exceeds remaining balance (${formatCurrency(remaining)})`
      );
      return;
    }

    if (remaining < 0 && amount > 0) {
      setError("Total already exceeds order amount. Remove payments first.");
      return;
    }

    setPayments([...payments, { payment_method: paymentMethod, amount }]);
    setPaymentAmount("");
  };

  const handleRemovePayment = (index: number) => {
    setPayments(payments.filter((_, i) => i !== index));
    setError("");
  };

  const handleSave = () => {
    if (!isValid) {
      setError("Payment total must match order total");
      return;
    }

    setError("");
    onSave(order.id, payments);
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
                   w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white rounded-2xl shadow-2xl z-60 p-6"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex flex-col gap-6">
          {/* Header */}
          <div>
            <h2 className="text-2xl font-heading font-bold text-coffee-dark mb-2">
              Edit Payment Methods
            </h2>
            <p className="text-neutral-text-light text-sm">
              Order #{order.order_number} - Table {order.table_number}
            </p>
          </div>

          {/* Order Total */}
          <div className="bg-neutral-background rounded-xl p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-neutral-text-light">Order Total</span>
              <span className="text-2xl font-bold font-heading text-coffee-dark">
                {formatCurrency(totalAmount)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-neutral-text-light">Payment Total</span>
              <span
                className={`text-lg font-semibold ${
                  isValid
                    ? "text-green-700"
                    : remaining > 0
                    ? "text-orange-700"
                    : "text-red-700"
                }`}
              >
                {formatCurrency(paymentsTotal)}
              </span>
            </div>
            {!isValid && (
              <div className="mt-2 text-sm">
                <span className="text-neutral-text-light">Difference: </span>
                <span
                  className={`font-medium ${
                    remaining > 0 ? "text-orange-700" : "text-red-700"
                  }`}
                >
                  {remaining > 0 ? "+" : ""}
                  {formatCurrency(Math.abs(remaining))}
                </span>
              </div>
            )}
          </div>

          {/* Current Payments */}
          {payments.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-neutral-text-dark mb-3">
                Payment Methods
              </h3>
              <div className="space-y-2">
                {payments.map((payment, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-neutral-background rounded-lg p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="text-coffee-brown">
                        {paymentIcons[payment.payment_method]}
                      </div>
                      <div>
                        <p className="font-medium text-neutral-text-dark capitalize">
                          {payment.payment_method}
                        </p>
                        <p className="text-sm text-neutral-text-light">
                          {formatCurrency(payment.amount)}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemovePayment(index)}
                      className="text-red-600 hover:text-red-700 text-sm font-medium
                                 px-3 py-1 hover:bg-red-50 rounded transition-colors"
                      disabled={isSaving}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Add Payment */}
          <div>
            <h3 className="text-sm font-semibold text-neutral-text-dark mb-3">
              Add Payment
            </h3>

            {/* Payment Method Selection */}
            <div className="grid grid-cols-3 gap-3 mb-4">
              {(["upi", "cash", "card"] as PaymentMethod[]).map((method) => (
                <button
                  key={method}
                  onClick={() => setPaymentMethod(method)}
                  className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all
                    ${
                      paymentMethod === method
                        ? "border-coffee-brown bg-coffee-brown/10"
                        : "border-neutral-border bg-white hover:border-coffee-brown/50"
                    }`}
                  disabled={isSaving}
                >
                  <div
                    className={
                      paymentMethod === method
                        ? "text-coffee-brown"
                        : "text-neutral-text-light"
                    }
                  >
                    {paymentIcons[method]}
                  </div>
                  <span className="text-sm font-medium capitalize">
                    {method}
                  </span>
                </button>
              ))}
            </div>

            {/* Amount Input */}
            <div className="flex gap-2">
              <div className="flex-1">
                <input
                  type="number"
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddPayment()}
                  placeholder="Amount in ₹"
                  className="w-full px-4 py-3 border border-neutral-border rounded-lg
                           focus:outline-none focus:ring-2 focus:ring-coffee-brown"
                  disabled={isSaving}
                />
              </div>
              {remaining > 0 && (
                <button
                  onClick={() => {
                    setPayments([...payments, { payment_method: paymentMethod, amount: remaining }]);
                    setPaymentAmount("");
                    setError("");
                  }}
                  className="px-4 py-3 bg-coffee-brown/10 border-2 border-coffee-brown text-coffee-brown font-semibold rounded-lg
                           hover:bg-coffee-brown hover:text-white transition-all disabled:opacity-50
                           whitespace-nowrap text-sm shadow-sm hover:shadow-md"
                  disabled={isSaving}
                  title={`Add full remaining amount (${formatCurrency(remaining)})`}
                >
                  Full Amount
                </button>
              )}
              <button
                onClick={handleAddPayment}
                className="px-6 py-3 bg-coffee-brown text-white font-semibold rounded-lg
                         hover:bg-coffee-dark shadow-sm hover:shadow-md
                         transition-all disabled:opacity-50"
                disabled={isSaving}
              >
                Add
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col gap-3">
            <div className="flex gap-3 items-center">
              {onCancelOrder && order.status !== 'canceled' && (
                <button
                  onClick={() => {
                    onCancelOrder();
                    onClose();
                  }}
                  disabled={isSaving}
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
                disabled={isSaving}
                className="py-3.5 px-6 text-neutral-text-dark font-semibold text-base
                         bg-white border-2 border-neutral-border rounded-xl
                         hover:bg-neutral-background hover:border-coffee-brown/30
                         shadow-sm hover:shadow-md
                         transition-all disabled:opacity-50"
              >
                Close
              </button>
              <button
                onClick={handleSave}
                disabled={!isValid || isSaving}
                className="py-3.5 px-6 text-white font-semibold text-base
                         bg-coffee-brown rounded-xl hover:bg-coffee-dark
                         shadow-md hover:shadow-lg
                         transition-all disabled:opacity-50
                         disabled:cursor-not-allowed"
              >
                {isSaving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
