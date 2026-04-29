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
        <div
          style={{ background: 'linear-gradient(135deg, #c04e30, #b5462a)' }}
          className="flex items-center gap-3 px-5 py-4"
        >
          <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5" fill="white" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/>
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-white font-heading italic text-base font-bold leading-tight">
              Revenue Breakdown
            </h2>
            <p className="text-white/70 text-xs mt-0.5">
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
            aria-label="Close"
            className="text-white/60 hover:text-white text-xl leading-none ml-auto flex-shrink-0"
          >
            &times;
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Total Revenue */}
          <div className="bg-coffee-brown/10 border border-coffee-light/30 rounded-2xl p-6 text-center">
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
                <div className="w-10 h-10 rounded-full bg-lily-green/10 text-lily-green flex items-center justify-center">
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
                <div className="w-10 h-10 rounded-full bg-info/10 text-info flex items-center justify-center">
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
                <div className="w-10 h-10 rounded-full bg-amber/10 text-amber flex items-center justify-center">
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
