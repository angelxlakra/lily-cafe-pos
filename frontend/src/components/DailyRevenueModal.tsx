import { UpiIcon, CashIcon, CardIcon } from "./icons/PaymentIcons";
import { formatCurrency } from "../utils/formatCurrency";

interface DailyRevenueModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: {
    total: number;
    cash: number;
    upi: number;
    card: number;
  };
  date: string;
}

export default function DailyRevenueModal({
  isOpen,
  onClose,
  data,
  date,
}: DailyRevenueModalProps) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 z-[60] backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                   w-full max-w-md bg-neutral-background rounded-3xl shadow-2xl z-[70]
                   flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="p-6 border-b border-neutral-border flex items-center justify-between bg-off-white">
          <div>
            <h2 className="text-xl font-heading font-bold text-coffee-dark">
              Revenue Breakdown
            </h2>
            <p className="text-sm text-neutral-text-light mt-1">
              {new Date(date).toLocaleDateString(undefined, {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-neutral-border transition-colors text-neutral-text-light"
            aria-label="Close"
          >
            <span className="text-2xl">&times;</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Total Revenue */}
          <div className="bg-coffee-light/10 border border-coffee-light rounded-2xl p-6 text-center">
            <p className="text-sm font-medium text-coffee-brown mb-1 uppercase tracking-wide">
              Total Revenue
            </p>
            <p className="text-4xl font-heading font-bold text-coffee-dark">
              {formatCurrency(data.total)}
            </p>
          </div>

          {/* Breakdown Grid */}
          <div className="space-y-3">
            {/* Cash */}
            <div className="flex items-center justify-between p-4 bg-off-white border border-neutral-border rounded-xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-green-100 text-green-700 flex items-center justify-center">
                  <CashIcon size={20} weight="duotone" />
                </div>
                <span className="font-medium text-neutral-text-dark">Cash</span>
              </div>
              <span className="font-bold text-neutral-text-dark text-lg">
                {formatCurrency(data.cash)}
              </span>
            </div>

            {/* UPI */}
            <div className="flex items-center justify-between p-4 bg-off-white border border-neutral-border rounded-xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center">
                  <UpiIcon size={20} weight="duotone" />
                </div>
                <span className="font-medium text-neutral-text-dark">UPI</span>
              </div>
              <span className="font-bold text-neutral-text-dark text-lg">
                {formatCurrency(data.upi)}
              </span>
            </div>

            {/* Card */}
            <div className="flex items-center justify-between p-4 bg-off-white border border-neutral-border rounded-xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center">
                  <CardIcon size={20} weight="duotone" />
                </div>
                <span className="font-medium text-neutral-text-dark">Card</span>
              </div>
              <span className="font-bold text-neutral-text-dark text-lg">
                {formatCurrency(data.card)}
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-neutral-border bg-off-white">
          <button
            onClick={onClose}
            className="w-full py-3 bg-neutral-background border border-neutral-border text-neutral-text-dark font-bold rounded-xl hover:bg-neutral-border transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </>
  );
}
