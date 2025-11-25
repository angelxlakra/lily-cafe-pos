// ========================================
// Payment Modal Component
// Split payment support with receipt printing
// ========================================

import { useState } from "react";
import { UpiIcon, CashIcon, CardIcon } from "./icons/PaymentIcons";
import { useOrder, useAddPayments, usePrintReceipt } from "../hooks/useOrders";
import { formatCurrency } from "../utils/formatCurrency";
import type {
  PaymentMethod,
  PaymentCreateRequest,
} from "../types";

interface PaymentModalProps {
  orderId: number;
  onClose: () => void;
}

export default function PaymentModal({ orderId, onClose }: PaymentModalProps) {
  const { data: order } = useOrder(orderId);
  const addPaymentsMutation = useAddPayments();
  const printReceiptMutation = usePrintReceipt();

  const paymentIcons: Record<PaymentMethod, JSX.Element> = {
    upi: <UpiIcon size={32} weight="duotone" />,
    cash: <CashIcon size={32} weight="duotone" />,
    card: <CardIcon size={32} weight="duotone" />,
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
        className="fixed inset-0 bg-black/60 z-60 backdrop-blur-sm"
        onClick={!isProcessing ? onClose : undefined}
        aria-hidden="true"
      />

      {/* Modal - Wider for two-column layout */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                   w-full max-w-5xl max-h-[90vh] overflow-y-auto bg-neutral-background rounded-3xl shadow-2xl z-70
                   flex flex-col lg:flex-row overflow-hidden"
        role="dialog"
        aria-modal="true"
      >
        {/* LEFT COLUMN - Order Summary */}
        <div className="w-full lg:w-5/12 bg-off-white p-8 flex flex-col border-r border-neutral-border">
          <div className="mb-8">
            <h2 className="text-3xl font-heading font-bold text-coffee-dark mb-6">
              Payment for Table {order?.table_number}
            </h2>

            {/* Summary Tiles Grid */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              {/* Total Amount Box */}
              <div className="bg-cream rounded-xl p-4 flex flex-col justify-center">
                <span className="text-neutral-text-light text-sm font-medium mb-1">Total Amount</span>
                <span className="text-2xl font-bold font-heading text-coffee-dark">
                  {formatCurrency(totalAmount)}
                </span>
              </div>

              {/* Amount Remaining Box */}
              <div className={`rounded-xl p-4 flex flex-col justify-center border ${
                remaining === 0 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-orange-50 border-orange-200'
              }`}>
                <span className={`text-sm font-medium mb-1 ${
                  remaining === 0 ? 'text-green-700' : 'text-orange-700'
                }`}>Remaining</span>
                <span className={`text-2xl font-bold font-heading ${
                  remaining === 0 ? 'text-green-800' : 'text-orange-800'
                }`}>
                  {formatCurrency(remaining)}
                </span>
              </div>
            </div>

            {/* Price Breakdown */}
            <div className="space-y-4">
              <button
                onClick={() => setShowBreakdown(!showBreakdown)}
                className="text-neutral-text-light font-medium flex items-center gap-2 hover:text-coffee-dark transition-colors"
              >
                <svg
                  className={`w-4 h-4 transition-transform ${showBreakdown ? 'rotate-90' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                {showBreakdown ? 'Hide Price Breakdown' : 'Show Price Breakdown'}
              </button>

              <div className={`transition-all duration-300 ease-in-out overflow-hidden ${showBreakdown ? 'opacity-100 max-h-96' : 'opacity-0 max-h-0'}`}>
                <div className="bg-neutral-background rounded-xl border border-neutral-border overflow-hidden mt-2">
                   <table className="w-full text-sm">
                      <thead className="bg-off-white border-b border-neutral-border">
                        <tr>
                          <th className="text-left p-3 font-semibold text-coffee-dark">Item</th>
                          <th className="text-center p-3 font-semibold text-coffee-dark">Qty</th>
                          <th className="text-right p-3 font-semibold text-coffee-dark">Price</th>
                        </tr>
                      </thead>
                      <tbody>
                        {order?.order_items.map((item) => (
                          <tr key={item.id} className="border-b border-neutral-border last:border-0">
                            <td className="p-3 text-coffee-dark font-medium">{item.menu_item_name}</td>
                            <td className="p-3 text-center text-neutral-text-light">{item.quantity}</td>
                            <td className="p-3 text-right text-coffee-dark font-bold">
                              {formatCurrency(item.subtotal)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot className="bg-off-white border-t border-neutral-border">
                         <tr>
                            <td colSpan={2} className="p-3 text-left text-neutral-text-light">GST (5%)</td>
                            <td className="p-3 text-right text-neutral-text-light">{formatCurrency(order?.gst_amount || 0)}</td>
                         </tr>
                         <tr>
                            <td colSpan={2} className="p-3 text-left font-bold text-coffee-dark text-base">Total</td>
                            <td className="p-3 text-right font-bold text-coffee-dark text-base">{formatCurrency(order?.total_amount || 0)}</td>
                         </tr>
                      </tfoot>
                   </table>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN - Payment Controls */}
        <div className="w-full lg:w-7/12 bg-neutral-background p-8 flex flex-col relative">
           {/* Close Button */}
           <button
            onClick={onClose}
            disabled={isProcessing}
            className="absolute top-6 right-6 w-8 h-8 flex items-center justify-center rounded-full hover:bg-cream transition-colors text-neutral-text-light z-50"
            aria-label="Close"
          >
            <span className="text-2xl">&times;</span>
          </button>

          <div className="flex-1 flex flex-col min-h-0">
            {/* Payments Added Section - Scrollable if too many items */}
            <div className="flex-shrink min-h-0 overflow-y-auto mb-4 pr-2">
              <div className="flex justify-between items-center mb-4 sticky top-0 bg-neutral-background z-10 py-2">
                 <h3 className="text-xl font-bold text-coffee-dark">Payments Added</h3>
              </div>

              {payments.length === 0 && existingPayments.length === 0 ? (
                <div className="text-neutral-text-muted italic text-sm py-2">No payments added yet.</div>
              ) : (
                <div className="grid grid-cols-1 gap-2">
                   {existingPayments.map((payment) => (
                      <div key={payment.id} className="flex items-center justify-between bg-off-white border border-neutral-border rounded-lg px-3 py-2">
                         <div className="flex items-center gap-2">
                            <span className="text-coffee-dark scale-75">{paymentIcons[payment.payment_method]}</span>
                            <span className="font-medium text-coffee-dark capitalize text-sm">{payment.payment_method}</span>
                         </div>
                         <span className="font-bold text-coffee-dark text-sm">{formatCurrency(payment.amount)}</span>
                      </div>
                   ))}
                   {payments.map((payment, index) => (
                      <div key={`new-${index}`} className="flex items-center justify-between bg-neutral-background border border-neutral-border rounded-lg px-3 py-2 shadow-sm relative group">
                         <div className="flex items-center gap-2">
                            <span className="text-coffee-dark scale-75">{paymentIcons[payment.payment_method]}</span>
                            <span className="font-medium text-coffee-dark capitalize text-sm">{payment.payment_method}</span>
                         </div>
                         <div className="flex items-center gap-3">
                            <span className="font-bold text-coffee-dark text-sm">{formatCurrency(payment.amount)}</span>
                            <button
                               onClick={() => handleRemovePayment(index)}
                               className="text-red-600 hover:bg-red-50 rounded-full p-1 transition-colors"
                            >
                               &times;
                            </button>
                         </div>
                      </div>
                   ))}
                </div>
              )}
            </div>

            {/* Add Payment Section - Fixed at bottom of content area */}
            <div className="flex-shrink-0 pt-4 border-t border-dashed border-neutral-border">
               <h3 className="text-lg font-bold text-coffee-dark mb-3">Add Payment</h3>
               
               {/* Payment Methods - Compact Grid */}
               <div className="grid grid-cols-3 gap-3 mb-4">
                  {(['upi', 'cash', 'card'] as PaymentMethod[]).map((method) => (
                     <button
                        key={method}
                        onClick={() => setPaymentMethod(method)}
                        className={`
                           relative flex flex-col items-center justify-center gap-2 p-3 rounded-xl border-2 transition-all duration-200
                           ${paymentMethod === method
                              ? 'border-coffee-brown bg-off-white shadow-md transform -translate-y-0.5'
                              : 'border-neutral-border bg-neutral-background hover:border-coffee-light hover:bg-off-white'
                           }
                        `}
                     >
                        <div className={`
                           w-8 h-8 rounded-full flex items-center justify-center text-lg
                           ${paymentMethod !== method ? 'bg-coffee-brown text-cream' : 'bg-cream text-coffee-brown'}
                        `}>
                           {paymentIcons[method]}
                        </div>
                        <span className={`text-xs font-bold ${paymentMethod === method ? 'text-coffee-brown' : 'text-neutral-text-light'}`}>
                           {method.toUpperCase()}
                        </span>
                        {paymentMethod === method && (
                           <div className="absolute top-1 right-1 text-coffee-brown">
                              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                 <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                           </div>
                        )}
                     </button>
                  ))}
               </div>

               <div className="mb-4">
                  <div className="flex gap-3">
                     <div className="relative flex-1">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-text-light font-bold text-lg">₹</span>
                        <input
                           type="number"
                           value={paymentAmount}
                           onChange={(e) => setPaymentAmount(e.target.value)}
                           className="w-full pl-10 pr-4 py-3 border-2 border-neutral-border rounded-xl text-xl font-bold text-coffee-dark bg-neutral-background focus:border-coffee-brown focus:outline-none transition-colors"
                           placeholder="0"
                        />
                     </div>
                     <button
                        onClick={() => setPaymentAmount((remaining / 100).toString())}
                        className="px-4 py-2 bg-cream text-coffee-brown font-bold rounded-xl hover:bg-neutral-border transition-colors border-2 border-neutral-border whitespace-nowrap"
                     >
                        Full Amount
                     </button>
                  </div>
               </div>

               {error && (
                  <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-xl flex items-center gap-2 text-sm">
                     <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                     </svg>
                     {error}
                  </div>
               )}

               <button
                  onClick={handleAddPayment}
                  disabled={!paymentAmount || parseFloat(paymentAmount) <= 0}
                  className="w-full py-3 bg-coffee-dark text-cream font-bold text-lg rounded-xl hover:bg-coffee-brown disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
               >
                  Add Payment
               </button>
            </div>
          </div>

          {/* Footer Action */}
          <div className="mt-auto pt-6 border-t border-neutral-border">
             <button
                onClick={handlePrintReceipt}
                disabled={remaining > 0 || isProcessing}
                className={`
                   w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all shadow-lg
                   ${remaining === 0
                      ? 'bg-coffee-brown text-white hover:bg-coffee-dark transform hover:-translate-y-0.5'
                      : 'bg-neutral-border text-neutral-text-muted cursor-not-allowed'
                   }
                `}
             >
                {isProcessing ? (
                   <>
                      <svg className="animate-spin h-6 w-6" viewBox="0 0 24 24">
                         <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                         <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Processing...
                   </>
                ) : (
                   <>
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                         <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                      </svg>
                      {remaining === 0 ? 'Complete Order & Print Receipt' : `Remaining: ${formatCurrency(remaining)}`}
                   </>
                )}
             </button>
          </div>
        </div>
      </div>
    </>
  );
}
