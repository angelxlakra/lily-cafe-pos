// ========================================
// Payment Modal Component
// Split payment support with receipt printing
// ========================================

import { useState } from "react";
import { PixLogo, Money, CreditCard } from "@phosphor-icons/react";
import { useOrder, useAddPayments, usePrintReceipt } from "../hooks/useOrders";
import { formatCurrency } from "../utils/formatCurrency";
import type {
  Payment,
  PaymentMethod,
  PaymentCreateRequest,
} from "../types";

interface PaymentModalProps {
  orderId: number;
  onClose: () => void;
}

export default function PaymentModal({ orderId, onClose }: PaymentModalProps) {
  const { data: order, isLoading: isLoadingOrder } = useOrder(orderId);
  const addPaymentsMutation = useAddPayments();
  const printReceiptMutation = usePrintReceipt();

  const paymentIcons: Record<PaymentMethod, JSX.Element> = {
    upi: <PixLogo size={20} weight="duotone" />,
    cash: <Money size={20} weight="duotone" />,
    card: <CreditCard size={20} weight="duotone" />,
  };

  const [payments, setPayments] = useState<PaymentCreateRequest[]>([]);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("upi");
  const [paymentAmount, setPaymentAmount] = useState("");
  const [error, setError] = useState("");

  const totalAmount = order?.total_amount || 0;
  const existingPayments = order?.payments ?? [];
  const alreadyPaid = existingPayments.reduce((sum, payment) => sum + payment.amount, 0);
  const pendingTotal = payments.reduce((sum, p) => sum + p.amount, 0);
  const totalPaid = alreadyPaid + pendingTotal;
  const remaining = Math.max(totalAmount - totalPaid, 0);

  const handleAddPayment = () => {
    setError("");

    const amount = parseInt(paymentAmount, 10) * 100;

    if (!paymentAmount || isNaN(amount) || amount <= 0) {
      setError("Please enter a valid amount");
      return;
    }

    if (amount > remaining) {
      setError(
        `Amount exceeds remaining balance (${formatCurrency(remaining)})`
      );
      return;
    }

    setPayments([...payments, { payment_method: paymentMethod, amount }]);
    setPaymentAmount("");
  };

  const handleRemovePayment = (index: number) => {
    setPayments(payments.filter((_, i) => i !== index));
  };

  const handlePrintReceipt = async () => {
    if (remaining !== 0) {
      setError("Please add payments to cover the full amount");
      return;
    }

    setError("");

    try {
      // Submit the payments only if new payments were added
      if (payments.length > 0) {
        await addPaymentsMutation.mutateAsync({
          orderId,
          data: { payments },
        });
      }

      // Then, print the receipt
      await printReceiptMutation.mutateAsync(orderId);

      // Close modal on success
      onClose();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to process payment"
      );
    }
  };

  const isProcessing =
    addPaymentsMutation.isPending || printReceiptMutation.isPending;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-60"
        onClick={!isProcessing ? onClose : undefined}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                   w-full max-w-lg bg-off-white rounded-2xl shadow-2xl z-70
                   flex flex-col max-h-[90vh]"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-border">
          <h2 className="text-xl font-bold text-neutral-text-dark">
            Payment for Table {order?.table_number}
          </h2>
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-neutral-border transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <span className="text-xl text-neutral-text-light">&times;</span>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoadingOrder ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-coffee-brown border-t-transparent rounded-full"></div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Total Amount */}
              <div className="bg-cream rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <span className="text-neutral-text-light">Total Amount:</span>
                  <span className="text-2xl font-bold font-heading text-coffee-brown">
                    {formatCurrency(totalAmount)}
                  </span>
                </div>
              </div>

              {/* Existing Payments */}
              {existingPayments.length > 0 && (
                <div>
                  <h3 className="font-semibold text-neutral-text-dark mb-3">
                    Recorded Payments:
                  </h3>
                  <div className="space-y-2">
                    {existingPayments.map((payment: Payment) => (
                      <div
                        key={payment.id}
                        className="flex items-center justify-between bg-cream rounded-lg p-3"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-lg">
                            {paymentIcons[payment.payment_method]}
                          </span>
                          <span className="font-medium text-neutral-text-dark capitalize">
                            {payment.payment_method}
                          </span>
                        </div>
                        <span className="font-semibold text-coffee-brown">
                          {formatCurrency(payment.amount)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Payments Added */}
              {payments.length > 0 && (
                <div>
                  <h3 className="font-semibold text-neutral-text-dark mb-3">
                    Payments Added:
                  </h3>
                  <div className="space-y-2">
                    {payments.map((payment, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between bg-cream rounded-lg p-3"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-lg">
                            {paymentIcons[payment.payment_method]}
                          </span>
                          <span className="font-medium text-neutral-text-dark capitalize">
                            {payment.payment_method}
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="font-semibold text-coffee-brown">
                            {formatCurrency(payment.amount)}
                          </span>
                          <button
                            onClick={() => handleRemovePayment(index)}
                            className="text-error hover:text-[#D32F2F] transition-colors"
                            aria-label="Remove payment"
                          >
                            &times;
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Amount Remaining */}
              <div className="bg-lily-green/10 border border-lily-green rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-neutral-text-dark">
                    Amount Remaining:
                  </span>
                  <span
                    className={`text-xl font-bold ${
                      remaining === 0 ? "text-success" : "text-coffee-brown"
                    }`}
                  >
                    {formatCurrency(remaining)}
                  </span>
                </div>
              </div>

              {/* Add Payment Section */}
              {remaining > 0 && (
                <div className="border border-neutral-border rounded-lg p-4">
                  <h3 className="font-semibold text-neutral-text-dark mb-4">
                    Add Payment
                  </h3>

                  <div className="space-y-4">
                    {/* Payment Method */}
                    <div>
                      <label className="block text-sm font-medium text-neutral-text-dark mb-2">
                        Payment Method
                      </label>
                      <select
                        value={paymentMethod}
                        onChange={(e) =>
                          setPaymentMethod(e.target.value as PaymentMethod)
                        }
                        className="w-full px-4 py-3 border border-neutral-border rounded-lg
                                 focus:outline-none focus:ring-2 focus:ring-coffee-brown"
                      >
                        <option value="upi">UPI (PhonePe, GPay, etc.)</option>
                        <option value="cash">Cash</option>
                        <option value="card">Card</option>
                      </select>
                    </div>

                    {/* Amount */}
                    <div>
                      <label className="block text-sm font-medium text-neutral-text-dark mb-2">
                        Amount
                      </label>
                      <div className="flex gap-2">
                        <div className="flex-1 relative">
                          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-text-light">
                            ₹
                          </span>
                          <input
                            type="number"
                            value={paymentAmount}
                            onChange={(e) => setPaymentAmount(e.target.value)}
                            placeholder="0"
                            className="w-full pl-8 pr-4 py-3 border border-neutral-border rounded-lg
                                     focus:outline-none focus:ring-2 focus:ring-coffee-brown"
                          />
                        </div>
                        <button
                          onClick={() =>
                            setPaymentAmount((remaining / 100).toString())
                          }
                          className="btn-secondary whitespace-nowrap"
                        >
                          Full Amount
                        </button>
                      </div>
                    </div>

                    {/* Add Button */}
                    <button
                      onClick={handleAddPayment}
                      className="btn-success w-full"
                    >
                      + Add Payment
                    </button>
                  </div>
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div className="bg-error/10 border border-error rounded-lg p-3">
                  <p className="text-sm text-error font-medium">{error}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-neutral-border">
          <button
            onClick={handlePrintReceipt}
            disabled={remaining !== 0 || isProcessing}
            className="btn-primary w-full h-12 text-base"
          >
            {isProcessing ? (
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
                Processing...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 17v-2a2 2 0 012-2h2a2 2 0 012 2v2m4 0V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10m16 0a2 2 0 01-2 2H5a2 2 0 01-2-2"
                  />
                </svg>
                Print Receipt
              </span>
            )}
          </button>
        </div>
      </div>
    </>
  );
}
