import { useState, useMemo } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { LockOpen, LockKey, CheckCircle, ClockCounterClockwise, Info } from '@phosphor-icons/react';
import Sidebar from '../components/Sidebar';
import BottomNav from '../components/BottomNav';
import DenominationCounter, { Denominations } from '../components/DenominationCounter';
import { useCashCounterToday, useOpenCashCounter, useCloseCashCounter, useVerifyCashCounter, useCashCounterHistory } from '../hooks/useCashCounter';
import { toast } from '../utils/toast';
import { formatCurrency } from '../utils/formatCurrency';

export default function CashCounterPage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const { data: todayCounter, isLoading } = useCashCounterToday();

  return (
    <div className="min-h-screen bg-neutral-background pb-16 lg:pb-0 lg:pl-60 transition-all duration-300">
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      {/* Header */}
      <header className="bg-off-white border-b border-neutral-border p-4 md:p-6">
        <div className="flex items-center gap-4">
          {/* Hamburger Menu Button */}
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="lg:hidden w-10 h-10 flex items-center justify-center rounded-lg bg-coffee-brown text-cream hover:bg-coffee-dark transition-colors"
            aria-label="Open menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div className="flex-1">
            <h1 className="font-heading heading-section text-neutral-text-dark">
              Cash Counter
            </h1>
            <p className="text-sm text-muted mt-1">
              Daily cash management and verification
            </p>
          </div>
        </div>
      </header>

      <main className="p-4 lg:p-6 max-w-7xl mx-auto">
        {isLoading ? (
          <div className="text-center py-12 text-neutral-text-muted">Loading counter status...</div>
        ) : (
          <div className="flex flex-col lg:flex-row gap-6">
              {/* Middle Column - Main Content */}
              <div className="flex-1 space-y-3 min-w-0">
                {/* Action Forms */}
                {!todayCounter && <OpenCounterForm />}
                {todayCounter?.status === 'open' && <CloseCounterForm counter={todayCounter} />}
                {todayCounter?.status === 'closed_pending_verification' && <VerifyCounterForm counter={todayCounter} />}

                {/* History Section */}
                <CashCounterHistory />
              </div>

              {/* Right Column - Sticky Sidebar (hidden on mobile, shown on desktop) */}
              <div className="hidden lg:block lg:w-80 flex-shrink-0">
                <div className="sticky top-24">
                  <CashCounterSidebar counter={todayCounter} />
                </div>
              </div>
            </div>
        )}
      </main>

      <div className="lg:hidden">
        <BottomNav />
      </div>
    </div>
  );
}

function CashCounterSidebar({ counter }: { counter: any }) {
  if (!counter) {
    return (
      <div className="card p-4 space-y-4">
        <h3 className="text-sm font-semibold text-neutral-text-muted mb-3 flex items-center gap-2">
          <Info size={16} />
          Summary
        </h3>

        {/* Date */}
        <div className="pb-3 border-b border-neutral-border">
          <div className="text-xs text-neutral-text-muted mb-1">Date</div>
          <div className="text-sm font-medium text-neutral-text-dark">
            {new Date().toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </div>
        </div>

        {/* Status */}
        <div className="flex items-center justify-center gap-2 p-3 bg-neutral-background rounded-lg border-2 border-dashed border-neutral-border">
          <LockOpen size={20} className="text-neutral-text-muted" />
          <span className="text-sm font-medium text-neutral-text-muted">Counter Not Open</span>
        </div>

        <div className="text-center py-4 text-neutral-text-muted text-xs">
          <p>Open the counter to see cash summary</p>
        </div>
      </div>
    );
  }

  const openingBalance = parseFloat(counter.opening_balance);
  const cashPaymentsTotal = counter.cash_payments_total || 0;
  const expectedClosing = counter.expected_closing ? parseFloat(counter.expected_closing) : openingBalance + cashPaymentsTotal;
  const closingBalance = counter.closing_balance ? parseFloat(counter.closing_balance) : null;
  const variance = counter.variance !== null ? parseFloat(counter.variance) : null;

  const statusConfig = {
    open: { styles: 'bg-success/10 text-success border-success/30', icon: <LockOpen size={16} />, label: 'Open' },
    closed_pending_verification: { styles: 'bg-warning/10 text-warning border-warning/30', icon: <LockKey size={16} />, label: 'Pending' },
    verified: { styles: 'bg-info/10 text-info border-info/30', icon: <CheckCircle size={16} />, label: 'Verified' },
  };

  const config = statusConfig[counter.status as keyof typeof statusConfig] || {
    styles: 'bg-neutral-border/10 text-neutral-text-muted border-neutral-border',
    icon: <LockOpen size={16} />,
    label: counter.status || 'Unknown'
  };

  return (
    <div className="card p-4 space-y-4">
      {/* Header */}
      <h3 className="text-sm font-semibold text-neutral-text-dark mb-3 flex items-center gap-2">
        <Info size={16} className="text-lily-green" />
        Summary
      </h3>

      {/* Date */}
      <div className="pb-3 border-b border-neutral-border">
        <div className="text-xs text-neutral-text-muted mb-1">Date</div>
        <div className="text-sm font-medium text-neutral-text-dark">
          {new Date(counter.date).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </div>
      </div>

      {/* Status Badge */}
      <div className={`flex items-center justify-center gap-2 px-3 py-2 rounded-lg border ${config.styles}`}>
        {config.icon}
        <span className="text-sm font-medium">{config.label}</span>
      </div>

      {/* Opening Balance */}
      <div className="pb-3 border-b border-neutral-border">
        <div className="text-xs text-neutral-text-muted mb-1">Opening Balance</div>
        <div className="text-2xl font-mono font-bold text-neutral-text-dark">
          ₹{openingBalance.toLocaleString('en-IN')}
        </div>
      </div>

      {/* Cash Sales (if counter is open or closed) */}
      {counter.status !== 'verified' && (
        <div className="pb-3 border-b border-neutral-border">
          <div className="text-xs text-neutral-text-muted mb-1">Cash Sales Today</div>
          <div className="text-xl font-mono font-bold text-lily-green">
            + ₹{cashPaymentsTotal.toLocaleString('en-IN')}
          </div>
        </div>
      )}

      {/* Expected Total (when closing) */}
      {counter.status === 'open' && (
        <div className="p-3 bg-info/10 rounded-lg border border-info/30">
          <div className="text-xs text-info font-medium mb-1">What You Should Have</div>
          <div className="text-2xl font-mono font-bold text-info">
            ₹{expectedClosing.toLocaleString('en-IN')}
          </div>
          <div className="text-xs text-neutral-text-muted mt-2">
            Count this amount when closing
          </div>
        </div>
      )}

      {/* Closing Summary (when closed or verified) */}
      {(counter.status === 'closed_pending_verification' || counter.status === 'verified') && closingBalance !== null && (
        <>
          <div className="pb-3 border-b border-neutral-border">
            <div className="text-xs text-neutral-text-muted mb-1">Expected Amount</div>
            <div className="text-xl font-mono font-bold text-info">
              ₹{expectedClosing.toLocaleString('en-IN')}
            </div>
          </div>

          <div className="pb-3 border-b border-neutral-border">
            <div className="text-xs text-neutral-text-muted mb-1">You Counted</div>
            <div className="text-xl font-mono font-bold text-neutral-text-dark">
              ₹{closingBalance.toLocaleString('en-IN')}
            </div>
          </div>

          {/* Variance Display */}
          {variance !== null && (
            <div className={`p-3 rounded-lg border-2 ${
              variance === 0 ? 'bg-success/10 border-success/30' :
              variance > 0 ? 'bg-warning/10 border-warning/30' :
              'bg-error/10 border-error/30'
            }`}>
              <div className="text-xs font-medium mb-1">
                {variance === 0 ? '✅ Perfect Match!' : variance > 0 ? '⚠️ Extra Cash Found' : '❌ Cash Missing'}
              </div>
              <div className={`text-2xl font-mono font-bold ${
                variance === 0 ? 'text-success' :
                variance > 0 ? 'text-warning' :
                'text-error'
              }`}>
                {variance === 0 ? '₹0' : `₹${Math.abs(variance).toLocaleString('en-IN')}`}
              </div>
            </div>
          )}
        </>
      )}

      {/* Status Badge */}
      <div className="pt-3 border-t border-neutral-border">
        <div className="text-xs text-neutral-text-muted mb-1">Counter Status</div>
        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-sm font-medium ${
          counter.status === 'open' ? 'bg-success/10 text-success' :
          counter.status === 'closed_pending_verification' ? 'bg-warning/10 text-warning' :
          'bg-info/10 text-info'
        }`}>
          {counter.status === 'open' ? '🟢' : counter.status === 'closed_pending_verification' ? '🟡' : '✅'}
          <span className="capitalize">
            {counter.status === 'closed_pending_verification' ? 'Pending' : counter.status}
          </span>
        </div>
      </div>
    </div>
  );
}


function OpenCounterForm() {
  const [denominations, setDenominations] = useState<Denominations>({
    500: 0,
    200: 0,
    100: 0,
    50: 0,
    20: 0,
    10: 0
  });
  const [notes, setNotes] = useState('');
  const openCounter = useOpenCashCounter();

  // Calculate total from denominations
  const total = useMemo(() => {
    return Object.entries(denominations).reduce((sum, [denom, count]) => {
      return sum + (Number(denom) * count);
    }, 0);
  }, [denominations]);

  const handleDenominationChange = (denom: keyof Denominations, count: number) => {
    setDenominations(prev => ({ ...prev, [denom]: count }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (total === 0) return;
    try {
      const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
      await openCounter.mutateAsync({
        date: today,
        opening_500s: denominations[500],
        opening_200s: denominations[200],
        opening_100s: denominations[100],
        opening_50s: denominations[50],
        opening_20s: denominations[20],
        opening_10s: denominations[10],
        notes
      });
      toast.success("Counter opened successfully!", {
        description: `Opening balance: ${formatCurrency(total * 100)}`
      });
    } catch (error) {
      console.error("Failed to open counter", error);
      toast.error("Failed to open counter", {
        description: error instanceof Error ? error.message : "Please try again"
      });
    }
  };

  return (
    <div className="card p-4 animate-fade-in">
      <h3 className="text-base font-heading text-neutral-text-dark mb-3 flex items-center justify-between">
        <span className="flex items-center gap-2">
          <LockOpen size={20} />
          Open Counter
        </span>
        {total > 0 && (
          <span className="text-lily-green font-mono text-lg">
            ₹{total.toLocaleString('en-IN')}
          </span>
        )}
      </h3>

      {/* Help Text */}
      <div className="mb-4 p-3 bg-info/5 border border-info/20 rounded-lg">
        <h4 className="text-sm font-semibold text-info mb-1 flex items-center gap-2">
          <Info size={16} />
          How it works
        </h4>
        <ol className="text-xs text-neutral-text-dark space-y-1 list-decimal list-inside">
          <li>Count and enter opening cash by denomination</li>
          <li>Close counter at end of day with actual cash count</li>
          <li>Owner verifies variance (if any) with password</li>
        </ol>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-neutral-text-muted mb-2">Count Opening Cash by Denomination</label>
          <DenominationCounter
            denominations={denominations}
            onChange={handleDenominationChange}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-neutral-text-muted mb-1">Notes (Optional)</label>
          <textarea
            value={notes}
            onChange={e => setNotes(e.target.value)}
            className="input-field min-h-[80px]"
            placeholder="Any notes about opening condition..."
          />
        </div>
        <button type="submit" className="btn-primary w-full" disabled={openCounter.isPending || total === 0}>
          {openCounter.isPending ? (
            <span className="flex items-center justify-center gap-2">
              <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
              Opening Counter...
            </span>
          ) : total === 0 ? (
            'Enter cash denominations to continue'
          ) : (
            `Open Counter with ₹${total.toLocaleString('en-IN')}`
          )}
        </button>
      </form>
    </div>
  );
}

function CloseCounterForm({ counter }: { counter: any }) {
  const [denominations, setDenominations] = useState<Denominations>({
    500: 0,
    200: 0,
    100: 0,
    50: 0,
    20: 0,
    10: 0
  });
  const [notes, setNotes] = useState('');
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const closeCounter = useCloseCashCounter();

  // Calculate total from denominations
  const total = useMemo(() => {
    return Object.entries(denominations).reduce((sum, [denom, count]) => {
      return sum + (Number(denom) * count);
    }, 0);
  }, [denominations]);

  // Get expected closing balance
  const expectedClosing = counter.expected_closing ? parseFloat(counter.expected_closing) : parseFloat(counter.opening_balance) + (counter.cash_payments_total || 0);
  const difference = total - expectedClosing;

  const handleDenominationChange = (denom: keyof Denominations, count: number) => {
    setDenominations(prev => ({ ...prev, [denom]: count }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (total === 0) return;
    setIsConfirmOpen(true);
  };

  const handleConfirmClose = async () => {
    try {
      const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
      await closeCounter.mutateAsync({
        date: today,
        closing_500s: denominations[500],
        closing_200s: denominations[200],
        closing_100s: denominations[100],
        closing_50s: denominations[50],
        closing_20s: denominations[20],
        closing_10s: denominations[10],
        notes
      });
      setIsConfirmOpen(false);
      toast.success("Counter closed successfully!", {
        description: difference === 0 ? "Perfect match! No variance." : `Variance: ${difference > 0 ? '+' : ''}₹${Math.abs(difference).toLocaleString('en-IN')}`
      });
    } catch (error) {
      console.error("Failed to close counter", error);
      toast.error("Failed to close counter", {
        description: error instanceof Error ? error.message : "Please try again"
      });
    }
  };

  return (
    <>
      <div className="card p-4 animate-fade-in border-l-4 border-warning">
        <h3 className="text-base font-heading text-neutral-text-dark mb-3 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <LockKey size={20} />
            Close Counter
          </span>
          {total > 0 && (
            <span className={`font-mono text-lg ${
              total === expectedClosing ? 'text-success' : 'text-warning'
            }`}>
              ₹{total.toLocaleString('en-IN')}
            </span>
          )}
        </h3>

        {/* Expected vs Actual Balance */}
        <div className="mb-4 p-4 bg-info/10 border border-info/30 rounded-lg">
          {/* Explainer Section */}
          <div className="mb-3 pb-3 border-b border-info/20">
            <div className="flex items-start gap-2 text-xs text-neutral-text-dark">
              <Info size={14} className="text-info mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium mb-1">How Expected Cash is Calculated:</p>
                <p className="text-neutral-text-muted">
                  Opening Balance (₹{parseFloat(counter.opening_balance).toLocaleString('en-IN')}) +
                  Today's Cash Sales (₹{(counter.cash_payments_total || 0).toLocaleString('en-IN')}) =
                  Expected Cash (₹{expectedClosing.toLocaleString('en-IN')})
                </p>
              </div>
            </div>
          </div>

          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium">What You Should Have:</span>
            <span className="text-lg font-mono font-bold text-info">
              ₹{expectedClosing.toLocaleString('en-IN')}
            </span>
          </div>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium">What You Counted:</span>
            <span className={`text-lg font-mono font-bold ${
              total === expectedClosing ? 'text-success' : total === 0 ? 'text-neutral-text-muted' : 'text-warning'
            }`}>
              ₹{total.toLocaleString('en-IN')}
            </span>
          </div>
          {total > 0 && total !== expectedClosing && (
            <div className={`mt-2 pt-2 border-t ${difference > 0 ? 'border-warning/30' : 'border-error/30'}`}>
              <div className="flex justify-between">
                <span className="text-sm font-medium">
                  {difference > 0 ? 'Extra Cash Found:' : 'Cash Missing:'}
                </span>
                <span className={`text-lg font-mono font-bold ${difference > 0 ? 'text-warning' : 'text-error'}`}>
                  ₹{Math.abs(difference).toLocaleString('en-IN')}
                </span>
              </div>
              <p className="text-xs text-neutral-text-muted mt-1">
                {difference > 0 ? 'You counted more cash than expected - please recount' : 'You counted less cash than expected - please recount'}
              </p>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-neutral-text-muted mb-2">Count Closing Cash by Denomination</label>
            <DenominationCounter
              denominations={denominations}
              onChange={handleDenominationChange}
            />
            <p className="text-xs text-neutral-text-muted mt-2">
              Count the actual amount of cash in the drawer by denomination.
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-text-muted mb-1">Notes (Optional)</label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className="input-field min-h-[80px]"
              placeholder="Reason for any discrepancies..."
            />
          </div>
          <button type="submit" className="btn-secondary w-full bg-warning/10 text-warning-dark hover:bg-warning/20 border-warning/20" disabled={closeCounter.isPending || total === 0}>
            {closeCounter.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <div className="animate-spin h-4 w-4 border-2 border-warning-dark border-t-transparent rounded-full" />
                Closing Counter...
              </span>
            ) : total === 0 ? (
              'Enter cash count to continue'
            ) : (
              `Close Counter with ₹${total.toLocaleString('en-IN')}`
            )}
          </button>
        </form>
      </div>

      <ConfirmationModal
        isOpen={isConfirmOpen}
        onClose={() => setIsConfirmOpen(false)}
        onConfirm={handleConfirmClose}
        title="Close Cash Counter?"
        message={`Closing the counter will lock today's cash payments totaling ${formatCurrency((counter.cash_payments_total || 0) * 100)}. This action cannot be undone and no further orders can be added to today's sales.`}
        confirmLabel={closeCounter.isPending ? 'Closing...' : 'Yes, Close Counter'}
        isProcessing={closeCounter.isPending}
      />
    </>
  );
}

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel: string;
  isProcessing?: boolean;
}

function ConfirmationModal({ isOpen, onClose, onConfirm, title, message, confirmLabel, isProcessing }: ConfirmationModalProps) {
  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/60 z-50 backdrop-blur-sm"
        onClick={!isProcessing ? onClose : undefined}
        aria-hidden="true"
      />
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-neutral-background rounded-2xl shadow-2xl z-50 p-6 animate-fade-in"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 rounded-full bg-warning/10 text-warning flex items-center justify-center mb-4">
            <LockKey size={24} weight="duotone" />
          </div>
          <h3 className="text-xl font-heading text-neutral-text-dark mb-2">{title}</h3>
          <p className="text-neutral-text-muted mb-6">
            {message}
          </p>
          
          <div className="flex gap-3 w-full">
            <button
              onClick={onClose}
              disabled={isProcessing}
              className="flex-1 py-2.5 px-4 rounded-xl font-bold bg-neutral-border/50 text-neutral-text-body hover:bg-neutral-border transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              disabled={isProcessing}
              className="flex-1 py-2.5 px-4 rounded-xl font-bold bg-warning text-coffee-dark hover:bg-warning/90 transition-colors disabled:opacity-50 shadow-lg shadow-warning/20"
            >
              {confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

function VerifyCounterForm({ counter }: { counter: any }) {
  const [password, setPassword] = useState('');
  const [notes, setNotes] = useState('');
  const [showReopenModal, setShowReopenModal] = useState(false);
  const verifyCounter = useVerifyCashCounter();

  const variance = counter.variance !== null ? parseFloat(counter.variance) : 0;
  const cashPaymentsTotal = counter.cash_payments_total || 0;
  const openingBalance = parseFloat(counter.opening_balance);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) return;
    try {
      await verifyCounter.mutateAsync({ id: counter.id, data: { owner_password: password, notes } });
      toast.success("Counter verified successfully!", {
        description: variance === 0 ? "Perfect day - no variance!" : `Variance of ₹${Math.abs(variance).toLocaleString('en-IN')} acknowledged`
      });
    } catch (error) {
      console.error("Verification failed", error);
      toast.error("Verification failed", {
        description: "Invalid owner password. Please try again."
      });
    }
  };

  return (
    <>
      <div className="card p-6 animate-fade-in border-l-4 border-info">
        <h3 className="text-lg font-heading text-neutral-text-dark mb-4 flex items-center gap-2">
          <CheckCircle size={24} />
          Owner Verification Required
        </h3>

        {/* Explainer */}
        <div className="mb-4 p-3 bg-info/5 border border-info/20 rounded-lg">
          <div className="flex items-start gap-2 text-xs text-neutral-text-dark">
            <Info size={14} className="text-info mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium mb-1">What does this mean?</p>
              <p className="text-neutral-text-muted">
                The counter is closed. Owner needs to verify the cash count and acknowledge any difference between expected and actual cash.
              </p>
            </div>
          </div>
        </div>

        {/* Calculation Breakdown */}
        <div className="mb-4 p-4 bg-neutral-background rounded-lg">
          <p className="text-xs font-medium text-neutral-text-muted mb-2">How Cash Was Calculated:</p>
          <div className="text-sm text-neutral-text-body space-y-1 mb-3">
            <div className="flex justify-between">
              <span>Cash at Start (Opening Balance):</span>
              <span className="font-mono">₹{openingBalance.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between">
              <span>Cash from Sales Today:</span>
              <span className="font-mono">₹{cashPaymentsTotal.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between font-bold text-info border-t border-neutral-border pt-1 mt-1">
              <span>What You Should Have:</span>
              <span className="font-mono">₹{counter.expected_closing}</span>
            </div>
          </div>
          <div className="text-sm text-neutral-text-body space-y-1 mb-3 pt-2 border-t border-neutral-border">
            <div className="flex justify-between">
              <span>What You Actually Counted:</span>
              <span className="font-mono">₹{counter.closing_balance}</span>
            </div>
          </div>
          <div className={`flex justify-between font-bold text-base ${variance === 0 ? 'text-success' : variance > 0 ? 'text-warning' : 'text-error'} pt-2 border-t-2 ${variance === 0 ? 'border-success/30' : variance > 0 ? 'border-warning/30' : 'border-error/30'}`}>
            <span>{variance === 0 ? 'Perfect Match!' : variance > 0 ? 'Extra Cash Found:' : 'Cash Missing:'}</span>
            <span className="font-mono">{variance === 0 ? '₹0' : `₹${Math.abs(variance).toLocaleString('en-IN')}`}</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-text-muted mb-1">Owner Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="input-field"
              placeholder="Enter owner password"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-text-muted mb-1">Verification Notes (Optional)</label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className="input-field min-h-[80px]"
              placeholder="Explain the reason for any difference..."
            />
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setShowReopenModal(true)}
              className="flex-1 btn-secondary text-warning border-warning/30 hover:bg-warning/10"
            >
              Reopen Counter
            </button>
            <button type="submit" className="flex-1 btn-primary bg-info hover:bg-info-dark border-info" disabled={verifyCounter.isPending || !password}>
              {verifyCounter.isPending ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                  Verifying...
                </span>
              ) : !password ? (
                'Enter Password'
              ) : (
                'Verify & Approve'
              )}
            </button>
          </div>
        </form>
      </div>

      <ReopenCounterModal
        isOpen={showReopenModal}
        onClose={() => setShowReopenModal(false)}
        counter={counter}
      />
    </>
  );
}

interface ReopenCounterModalProps {
  isOpen: boolean;
  onClose: () => void;
  counter: any;
}

function ReopenCounterModal({ isOpen, onClose, counter }: ReopenCounterModalProps) {
  const [password, setPassword] = useState('');
  const [isReopening, setIsReopening] = useState(false);
  const queryClient = useQueryClient();

  const handleReopen = async () => {
    if (!password) return;

    setIsReopening(true);
    try {
      // Call reopen API (we'll create this)
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/cash-counter/reopen/${counter.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ owner_password: password })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to reopen counter');
      }

      await queryClient.invalidateQueries({ queryKey: ['cash-counter'] });

      toast.success("Counter reopened successfully!", {
        description: "You can now modify the cash count"
      });
      onClose();
      setPassword('');
    } catch (error) {
      console.error("Reopen failed", error);
      toast.error("Failed to reopen counter", {
        description: error instanceof Error ? error.message : "Invalid password or server error"
      });
    } finally {
      setIsReopening(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/60 z-50 backdrop-blur-sm"
        onClick={!isReopening ? onClose : undefined}
        aria-hidden="true"
      />
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-neutral-background rounded-2xl shadow-2xl z-50 p-6 animate-fade-in"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex flex-col">
          <div className="w-12 h-12 rounded-full bg-warning/10 text-warning flex items-center justify-center mb-4 mx-auto">
            <LockOpen size={24} weight="duotone" />
          </div>
          <h3 className="text-xl font-heading text-neutral-text-dark mb-2 text-center">Reopen Cash Counter?</h3>
          <p className="text-neutral-text-muted mb-4 text-sm text-center">
            Reopening will allow you to recount the cash. The counter will return to "Open" status and you'll need to close and verify it again.
          </p>

          {/* Warning */}
          <div className="mb-4 p-3 bg-warning/10 border border-warning/30 rounded-lg">
            <div className="flex items-start gap-2 text-xs text-neutral-text-dark">
              <Info size={14} className="text-warning mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium mb-1">⚠️ Important:</p>
                <p className="text-neutral-text-muted">
                  Only reopen if you need to fix a counting mistake. This requires owner password verification.
                </p>
              </div>
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-neutral-text-muted mb-1">Owner Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="input-field"
              placeholder="Enter owner password"
              disabled={isReopening}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && password) {
                  e.preventDefault();
                  handleReopen();
                }
              }}
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={isReopening}
              className="flex-1 py-2.5 px-4 rounded-xl font-bold bg-neutral-border/50 text-neutral-text-body hover:bg-neutral-border transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleReopen}
              disabled={isReopening || !password}
              className="flex-1 py-2.5 px-4 rounded-xl font-bold bg-warning text-coffee-dark hover:bg-warning/90 transition-colors disabled:opacity-50 shadow-lg shadow-warning/20"
            >
              {isReopening ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="animate-spin h-4 w-4 border-2 border-coffee-dark border-t-transparent rounded-full" />
                  Reopening...
                </span>
              ) : (
                'Yes, Reopen Counter'
              )}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

function CashCounterHistory() {
  const { data, isLoading } = useCashCounterHistory({ limit: 10 });

  return (
    <div className="card overflow-hidden mt-8">
      <div className="p-4 border-b border-neutral-border">
        <h3 className="font-heading text-lg text-neutral-text-dark flex items-center gap-2">
          <ClockCounterClockwise size={20} />
          Recent History
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-neutral-background border-b border-neutral-border text-neutral-text-muted text-sm uppercase tracking-wider">
              <th className="p-4 font-medium">Date</th>
              <th className="p-4 font-medium text-right">Opening</th>
              <th className="p-4 font-medium text-right">Closing</th>
              <th className="p-4 font-medium text-right">Variance</th>
              <th className="p-4 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-border">
            {isLoading ? (
              <tr><td colSpan={5} className="p-8 text-center text-neutral-text-muted">Loading history...</td></tr>
            ) : !data?.history || data.history.length === 0 ? (
              <tr><td colSpan={5} className="p-8 text-center text-neutral-text-muted">No history found.</td></tr>
            ) : (
              data.history.map((item) => (
                <tr key={item.id} className="hover:bg-neutral-background/50">
                  <td className="p-4 text-sm text-neutral-text-body">
                    {new Date(item.date).toLocaleDateString()}
                  </td>
                  <td className="p-4 text-right font-mono text-sm">₹{item.opening_balance}</td>
                  <td className="p-4 text-right font-mono text-sm">
                    {item.closing_balance !== null ? `₹${item.closing_balance}` : '-'}
                  </td>
                  <td className={`p-4 text-right font-mono text-sm ${
                    !item.variance ? 'text-neutral-text-muted' :
                    item.variance === 0 ? 'text-success' : 'text-error'
                  }`}>
                    {item.variance !== null ? (item.variance > 0 ? `+₹${item.variance}` : `₹${item.variance}`) : '-'}
                  </td>
                  <td className="p-4">
                    <span className={`badge ${
                      item.status === 'verified' ? 'bg-info/10 text-info' :
                      item.status === 'closed_pending_verification' ? 'bg-warning/10 text-warning-dark' :
                      'bg-success/10 text-success'
                    }`}>
                      {item.status === 'closed_pending_verification' ? 'Pending' : item.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
