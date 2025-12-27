import { useState } from 'react';
import { CurrencyInr, LockOpen, LockKey, CheckCircle, ClockCounterClockwise } from '@phosphor-icons/react';
import Sidebar from '../components/Sidebar';
import BottomNav from '../components/BottomNav';
import { useCashCounterToday, useOpenCashCounter, useCloseCashCounter, useVerifyCashCounter, useCashCounterHistory } from '../hooks/useCashCounter';

export default function CashCounterPage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const { data: todayCounter, isLoading } = useCashCounterToday();

  return (
    <div className="min-h-screen bg-neutral-background pb-16 lg:pb-0 lg:pl-60 transition-all duration-300">
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      {/* Header */}
      <header className="bg-gradient-primary text-cream p-6 sticky top-0 z-30 shadow-medium">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-heading heading-sub text-cream">Cash Counter</h1>
            <div className="text-cream/80 text-sm mt-1 font-medium">Daily cash management and verification</div>
          </div>
          <div className="lg:hidden">
            <button 
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 text-cream hover:bg-white/10 rounded-lg"
            >
              <span className="sr-only">Open Menu</span>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <main className="p-4 lg:p-6 max-w-4xl mx-auto space-y-6">
        {isLoading ? (
          <div className="text-center py-12 text-neutral-text-muted">Loading counter status...</div>
        ) : (
          <>
            {/* Current Status Card */}
            <CurrentStatusCard counter={todayCounter} />

            {/* Action Forms */}
            {!todayCounter && <OpenCounterForm />}
            {todayCounter?.status === 'open' && <CloseCounterForm counter={todayCounter} />}
            {todayCounter?.status === 'closed_pending_verification' && <VerifyCounterForm counter={todayCounter} />}

            {/* History Section */}
            <CashCounterHistory />
          </>
        )}
      </main>

      <div className="lg:hidden">
        <BottomNav />
      </div>
    </div>
  );
}

function CurrentStatusCard({ counter }: { counter: any }) {
  if (!counter) {
    return (
      <div className="card p-6 bg-neutral-background border-2 border-dashed border-neutral-border text-center">
        <div className="w-16 h-16 rounded-full bg-neutral-border/50 flex items-center justify-center mx-auto mb-4 text-neutral-text-muted">
          <LockOpen size={32} />
        </div>
        <h3 className="text-lg font-heading text-neutral-text-dark mb-2">Counter Not Open</h3>
        <p className="text-neutral-text-muted">No cash counter has been opened for today yet.</p>
      </div>
    );
  }

  const statusConfig = {
    open: { color: 'bg-success', icon: <LockOpen size={24} />, label: 'Open' },
    closed_pending_verification: { color: 'bg-warning', icon: <LockKey size={24} />, label: 'Pending Verification' },
    verified: { color: 'bg-info', icon: <CheckCircle size={24} />, label: 'Verified' },
  };

  const config = statusConfig[counter.status as keyof typeof statusConfig] || { 
    color: 'bg-neutral-border', 
    icon: <LockOpen size={24} />, 
    label: counter.status || 'Unknown' 
  };

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-xl font-heading text-coffee-brown dark:text-cream mb-1">Today's Counter</h2>
          <p className="text-sm text-neutral-text-muted">{new Date(counter.date).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
        <div className={`badge ${config.color}/10 text-${config.color.replace('bg-', '')} flex items-center gap-2 px-3 py-1.5`}>
          {config.icon}
          <span className="font-medium">{config.label}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-4 rounded-xl bg-neutral-background border border-neutral-border">
          <div className="text-sm text-neutral-text-muted mb-1">Opening Balance</div>
          <div className="text-2xl font-mono font-bold text-neutral-text-dark">₹{counter.opening_balance}</div>
          <div className="text-xs text-neutral-text-muted mt-2">By {counter.opened_by} at {new Date(counter.opened_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
        </div>

        {counter.closing_balance !== null && (
          <div className="p-4 rounded-xl bg-neutral-background border border-neutral-border">
            <div className="text-sm text-neutral-text-muted mb-1">Closing Balance</div>
            <div className="text-2xl font-mono font-bold text-neutral-text-dark">₹{counter.closing_balance}</div>
            <div className="text-xs text-neutral-text-muted mt-2">By {counter.closed_by}</div>
          </div>
        )}

        {counter.variance !== null && (
          <div className={`p-4 rounded-xl border ${counter.variance === 0 ? 'bg-success/5 border-success/20' : 'bg-error/5 border-error/20'}`}>
            <div className="text-sm text-neutral-text-muted mb-1">Variance</div>
            <div className={`text-2xl font-mono font-bold ${counter.variance === 0 ? 'text-success' : 'text-error'}`}>
              {counter.variance > 0 ? '+' : ''}₹{counter.variance}
            </div>
            <div className="text-xs text-neutral-text-muted mt-2">Expected: ₹{counter.expected_closing}</div>
          </div>
        )}
      </div>
    </div>
  );
}

function OpenCounterForm() {
  const [amount, setAmount] = useState('');
  const [notes, setNotes] = useState('');
  const openCounter = useOpenCashCounter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount) return;
    try {
      const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
      await openCounter.mutateAsync({
        date: today,
        opening_balance: Number(amount),
        notes
      });
    } catch (error) {
      console.error("Failed to open counter", error);
    }
  };

  return (
    <div className="card p-6 animate-fade-in">
      <h3 className="text-lg font-heading text-coffee-brown dark:text-cream mb-4 flex items-center gap-2">
        <LockOpen size={24} />
        Open Counter
      </h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-neutral-text-muted mb-1">Opening Cash Balance</label>
          <div className="relative">
            <CurrencyInr className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-text-muted" size={18} />
            <input
              type="number"
              min="0"
              step="0.01"
              required
              value={amount}
              onChange={e => setAmount(e.target.value)}
              className="input-field pl-10"
              placeholder="0.00"
            />
          </div>
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
        <button type="submit" className="btn-primary w-full" disabled={openCounter.isPending}>
          {openCounter.isPending ? 'Opening...' : 'Open Counter'}
        </button>
      </form>
    </div>
  );
}

function CloseCounterForm({ counter: _counter }: { counter: any }) {
  const [amount, setAmount] = useState('');
  const [notes, setNotes] = useState('');
  const closeCounter = useCloseCashCounter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount) return;
    if (window.confirm('Are you sure you want to close the counter? This cannot be undone.')) {
      try {
        const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
        await closeCounter.mutateAsync({
          date: today,
          closing_balance: Number(amount),
          notes
        });
      } catch (error) {
        console.error("Failed to close counter", error);
      }
    }
  };

  return (
    <div className="card p-6 animate-fade-in border-l-4 border-warning">
      <h3 className="text-lg font-heading text-coffee-brown dark:text-cream mb-4 flex items-center gap-2">
        <LockKey size={24} />
        Close Counter
      </h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-neutral-text-muted mb-1">Closing Cash Balance (Physical Count)</label>
          <div className="relative">
            <CurrencyInr className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-text-muted" size={18} />
            <input
              type="number"
              min="0"
              step="0.01"
              required
              value={amount}
              onChange={e => setAmount(e.target.value)}
              className="input-field pl-10"
              placeholder="0.00"
            />
          </div>
          <p className="text-xs text-neutral-text-muted mt-2">
            Enter the actual amount of cash counted in the drawer.
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
        <button type="submit" className="btn-secondary w-full bg-warning/10 text-warning-dark hover:bg-warning/20 border-warning/20" disabled={closeCounter.isPending}>
          {closeCounter.isPending ? 'Closing...' : 'Close Counter'}
        </button>
      </form>
    </div>
  );
}

function VerifyCounterForm({ counter }: { counter: any }) {
  const [password, setPassword] = useState('');
  const [notes, setNotes] = useState('');
  const verifyCounter = useVerifyCashCounter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) return;
    try {
      await verifyCounter.mutateAsync({ id: counter.id, data: { owner_password: password, notes } });
    } catch (error) {
      alert("Verification failed. Invalid password.");
    }
  };

  return (
    <div className="card p-6 animate-fade-in border-l-4 border-info">
      <h3 className="text-lg font-heading text-coffee-brown dark:text-cream mb-4 flex items-center gap-2">
        <CheckCircle size={24} />
        Owner Verification
      </h3>
      <div className="mb-4 p-3 bg-neutral-background rounded-lg text-sm text-neutral-text-body">
        <div className="flex justify-between mb-1">
          <span>Expected Closing:</span>
          <span className="font-mono">₹{counter.expected_closing}</span>
        </div>
        <div className="flex justify-between mb-1">
          <span>Actual Closing:</span>
          <span className="font-mono">₹{counter.closing_balance}</span>
        </div>
        <div className={`flex justify-between font-bold ${counter.variance === 0 ? 'text-success' : 'text-error'}`}>
          <span>Variance:</span>
          <span className="font-mono">{counter.variance > 0 ? '+' : ''}₹{counter.variance}</span>
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
            placeholder="Notes regarding variance..."
          />
        </div>
        <button type="submit" className="btn-primary w-full bg-info hover:bg-info-dark border-info" disabled={verifyCounter.isPending}>
          {verifyCounter.isPending ? 'Verifying...' : 'Verify & Close Day'}
        </button>
      </form>
    </div>
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
