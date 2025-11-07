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
  const [showBreakdown, setShowBreakdown] = useState(false);

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

              {/* Price Breakdown Toggle */}
              {order && order.order_items && order.order_items.length > 0 && (
                <div>
                  <button
                    onClick={() => setShowBreakdown(!showBreakdown)}
                    className="w-full text-left text-sm font-medium text-coffee-brown hover:text-coffee-dark flex items-center gap-2 transition-colors"
                  >
                    <svg
                      className={`w-4 h-4 transition-transform ${showBreakdown ? 'rotate-90' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    {showBreakdown ? 'Hide Price Breakdown' : 'View Price Breakdown'}
                  </button>

                  {/* Menu Items Breakdown */}
                  {showBreakdown && (
                    <div className="mt-3 border border-neutral-border rounded-lg overflow-hidden bg-white">
                      <div className="max-h-64 overflow-y-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-neutral-background border-b border-neutral-border sticky top-0">
                            <tr>
                              <th className="text-left p-2 font-semibold text-neutral-text-dark">Item</th>
                              <th className="text-center p-2 font-semibold text-neutral-text-dark">Qty</th>
                              <th className="text-right p-2 font-semibold text-neutral-text-dark">Price</th>
                            </tr>
                          </thead>
                          <tbody>
                            {order.order_items.map((item) => (
                              <tr key={item.id} className="border-b border-neutral-border last:border-0 hover:bg-neutral-background/50 transition-colors">
                                <td className="p-2 text-neutral-text-dark">{item.menu_item_name}</td>
                                <td className="p-2 text-center text-neutral-text-light">{item.quantity}</td>
                                <td className="p-2 text-right text-neutral-text-dark font-medium">
                                  {formatCurrency(item.subtotal)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                          <tfoot className="bg-neutral-background border-t-2 border-neutral-border">
                            <tr>
                              <td colSpan={2} className="p-2 text-left font-semibold text-neutral-text-dark">
                                Subtotal
                              </td>
                              <td className="p-2 text-right font-semibold text-neutral-text-dark">
                                {formatCurrency(order.subtotal)}
                              </td>
                            </tr>
                            <tr>
                              <td colSpan={2} className="p-2 text-left text-neutral-text-light text-xs">
                                GST (5%)
                              </td>
                              <td className="p-2 text-right text-neutral-text-light text-xs">
                                {formatCurrency(order.gst_amount)}
                              </td>
                            </tr>
                            <tr className="border-t border-neutral-border">
                              <td colSpan={2} className="p-2 text-left font-bold text-coffee-brown">
                                Total
                              </td>
                              <td className="p-2 text-right font-bold text-coffee-brown">
                                {formatCurrency(order.total_amount)}
                              </td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}

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
                    {/* Payment Method - Selectable Boxes */}
                    <div>
                      <label className="block text-sm font-medium text-neutral-text-dark mb-3">
                        Payment Method
                      </label>
                      <div className="grid grid-cols-3 gap-3">
                        {/* UPI Option */}
                        <button
                          type="button"
                          onClick={() => setPaymentMethod("upi")}
                          className={`flex flex-col items-center justify-center gap-2 p-4 rounded-lg border-2 transition-all
                            ${paymentMethod === "upi"
                              ? "border-coffee-brown bg-coffee-brown/10 shadow-md"
                              : "border-neutral-border bg-white hover:border-coffee-brown/50 hover:bg-coffee-brown/5"
                            }`}
                        >
                          <PixLogo
                            size={28}
                            weight="duotone"
                            className={paymentMethod === "upi" ? "text-coffee-brown" : "text-neutral-text-light"}
                          />
                          <span className={`text-sm font-medium ${paymentMethod === "upi" ? "text-coffee-brown" : "text-neutral-text-dark"}`}>
                            UPI
                          </span>
                        </button>

                        {/* Cash Option */}
                        <button
                          type="button"
                          onClick={() => setPaymentMethod("cash")}
                          className={`flex flex-col items-center justify-center gap-2 p-4 rounded-lg border-2 transition-all
                            ${paymentMethod === "cash"
                              ? "border-coffee-brown bg-coffee-brown/10 shadow-md"
                              : "border-neutral-border bg-white hover:border-coffee-brown/50 hover:bg-coffee-brown/5"
                            }`}
                        >
                          <Money
                            size={28}
                            weight="duotone"
                            className={paymentMethod === "cash" ? "text-coffee-brown" : "text-neutral-text-light"}
                          />
                          <span className={`text-sm font-medium ${paymentMethod === "cash" ? "text-coffee-brown" : "text-neutral-text-dark"}`}>
                            Cash
                          </span>
                        </button>

                        {/* Card Option */}
                        <button
                          type="button"
                          onClick={() => setPaymentMethod("card")}
                          className={`flex flex-col items-center justify-center gap-2 p-4 rounded-lg border-2 transition-all
                            ${paymentMethod === "card"
                              ? "border-coffee-brown bg-coffee-brown/10 shadow-md"
                              : "border-neutral-border bg-white hover:border-coffee-brown/50 hover:bg-coffee-brown/5"
                            }`}
                        >
                          <CreditCard
                            size={28}
                            weight="duotone"
                            className={paymentMethod === "card" ? "text-coffee-brown" : "text-neutral-text-light"}
                          />
                          <span className={`text-sm font-medium ${paymentMethod === "card" ? "text-coffee-brown" : "text-neutral-text-dark"}`}>
                            Card
                          </span>
                        </button>
                      </div>
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
                            onWheel={(e) => e.currentTarget.blur()}
                            min="0"
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
