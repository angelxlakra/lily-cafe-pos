import { useState } from 'react';
import { Plus, Minus, ArrowsLeftRight, ClockCounterClockwise } from '@phosphor-icons/react';
import { useInventoryTransactions, useInventoryItems, useRecordPurchase, useRecordUsage, useRecordAdjustment } from '../../hooks/useInventory';
import type { TransactionType } from '../../types/inventory';

export default function InventoryTransactionsTab() {
  const [activeAction, setActiveAction] = useState<'PURCHASE' | 'USAGE' | 'ADJUSTMENT' | null>(null);
  
  return (
    <div className="space-y-6">
      {/* Action Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ActionButton
          icon={<Plus size={24} />}
          title="Record Purchase"
          description="Add stock from suppliers"
          color="bg-success"
          onClick={() => setActiveAction('PURCHASE')}
        />
        <ActionButton
          icon={<Minus size={24} />}
          title="Record Usage"
          description="Log daily ingredient usage"
          color="bg-warning"
          onClick={() => setActiveAction('USAGE')}
        />
        <ActionButton
          icon={<ArrowsLeftRight size={24} />}
          title="Stock Adjustment"
          description="Correct physical counts"
          color="bg-info"
          onClick={() => setActiveAction('ADJUSTMENT')}
        />
      </div>

      {/* Transaction Form Modal */}
      {activeAction && (
        <TransactionFormModal
          type={activeAction}
          onClose={() => setActiveAction(null)}
        />
      )}

      {/* Transactions History */}
      <TransactionsHistory />
    </div>
  );
}

function ActionButton({ icon, title, description, color, onClick }: { icon: React.ReactNode, title: string, description: string, color: string, onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="card p-6 text-left hover:shadow-strong transition-all group border-l-4 border-transparent hover:border-coffee-brown"
    >
      <div className={`w-12 h-12 rounded-full ${color}/10 text-${color.replace('bg-', '')} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
        {icon}
      </div>
      <h3 className="font-heading text-lg text-neutral-text-dark mb-1">{title}</h3>
      <p className="text-sm text-neutral-text-muted">{description}</p>
    </button>
  );
}

function TransactionsHistory() {
  const [filterType, setFilterType] = useState<TransactionType | ''>('');
  const { data, isLoading } = useInventoryTransactions({
    transaction_type: filterType || undefined,
    limit: 20
  });

  return (
    <div className="card overflow-hidden">
      <div className="p-4 border-b border-neutral-border flex justify-between items-center">
        <h3 className="font-heading text-lg text-neutral-text-dark flex items-center gap-2">
          <ClockCounterClockwise size={20} />
          Recent Activity
        </h3>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value as TransactionType | '')}
          className="input-field py-1 px-3 text-sm w-auto"
        >
          <option value="">All Types</option>
          <option value="PURCHASE">Purchases</option>
          <option value="USAGE">Usage</option>
          <option value="ADJUSTMENT">Adjustments</option>
        </select>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-neutral-background border-b border-neutral-border text-neutral-text-muted text-sm uppercase tracking-wider">
              <th className="p-4 font-medium">Date</th>
              <th className="p-4 font-medium">Item</th>
              <th className="p-4 font-medium">Type</th>
              <th className="p-4 font-medium text-right">Quantity</th>
              <th className="p-4 font-medium">By</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-border">
            {isLoading ? (
              <tr><td colSpan={5} className="p-8 text-center text-neutral-text-muted">Loading history...</td></tr>
            ) : !data?.transactions || data.transactions.length === 0 ? (
              <tr><td colSpan={5} className="p-8 text-center text-neutral-text-muted">No transactions found.</td></tr>
            ) : (
              data.transactions.map((tx) => (
                <tr key={tx.id} className="hover:bg-neutral-background/50">
                  <td className="p-4 text-sm text-neutral-text-body">
                    {new Date(tx.created_at).toLocaleDateString()} {new Date(tx.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </td>
                  <td className="p-4 font-medium text-neutral-text-dark">{tx.item_name}</td>
                  <td className="p-4">
                    <span className={`badge ${
                      tx.transaction_type === 'PURCHASE' ? 'bg-success/10 text-success' :
                      tx.transaction_type === 'USAGE' ? 'bg-warning/10 text-warning-dark' :
                      'bg-info/10 text-info'
                    }`}>
                      {tx.transaction_type}
                    </span>
                  </td>
                  <td className="p-4 text-right font-mono">
                    {tx.quantity > 0 ? '+' : ''}{tx.quantity}
                  </td>
                  <td className="p-4 text-sm text-neutral-text-muted">{tx.recorded_by}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TransactionFormModal({ type, onClose }: { type: 'PURCHASE' | 'USAGE' | 'ADJUSTMENT', onClose: () => void }) {
  const [itemId, setItemId] = useState<number | ''>('');
  const [quantity, setQuantity] = useState<number | ''>('');
  const [notes, setNotes] = useState('');
  
  // For search
  const { data: itemsData } = useInventoryItems({ is_active: true });

  const recordPurchase = useRecordPurchase();
  const recordUsage = useRecordUsage();
  const recordAdjustment = useRecordAdjustment();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!itemId || !quantity) return;

    try {
      if (type === 'PURCHASE') {
        await recordPurchase.mutateAsync({
          items: [{ item_id: Number(itemId), quantity: Number(quantity), notes }]
        });
      } else if (type === 'USAGE') {
        await recordUsage.mutateAsync({
          items: [{ item_id: Number(itemId), quantity: Number(quantity), notes }],
          recorded_by: 'Staff' // TODO: Get from auth context
        });
      } else {
        await recordAdjustment.mutateAsync({
          item_id: Number(itemId),
          new_quantity: Number(quantity), // For adjustment, this is the NEW physical count
          notes
        });
      }
      onClose();
    } catch (error) {
      console.error("Failed to record transaction", error);
    }
  };

  const selectedItem = itemsData?.items.find(i => i.id === Number(itemId));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="card w-full max-w-md p-6 shadow-strong animate-scale-in" onClick={e => e.stopPropagation()}>
        <h3 className="text-xl font-heading text-coffee-brown dark:text-cream mb-6">
          {type === 'PURCHASE' ? 'Record Purchase' : type === 'USAGE' ? 'Record Usage' : 'Stock Adjustment'}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Item Selection */}
          <div>
            <label className="block text-sm font-medium text-neutral-text-muted mb-1">Select Item</label>
            <select
              value={itemId}
              onChange={e => setItemId(Number(e.target.value))}
              className="input-field"
              required
            >
              <option value="">Select an item...</option>
              {itemsData?.items.map(item => (
                <option key={item.id} value={item.id}>
                  {item.name} ({item.current_quantity} {item.unit})
                </option>
              ))}
            </select>
          </div>

          {/* Quantity Input */}
          <div>
            <label className="block text-sm font-medium text-neutral-text-muted mb-1">
              {type === 'ADJUSTMENT' ? 'New Physical Count' : 'Quantity'}
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                step="0.01"
                min="0"
                value={quantity}
                onChange={e => setQuantity(Number(e.target.value))}
                className="input-field"
                required
              />
              {selectedItem && <span className="text-neutral-text-muted font-medium">{selectedItem.unit}</span>}
            </div>
            {type === 'ADJUSTMENT' && selectedItem && (
              <p className="text-xs text-neutral-text-muted mt-1">
                Current system stock: {selectedItem.current_quantity} {selectedItem.unit}
              </p>
            )}
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-neutral-text-muted mb-1">Notes (Optional)</label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className="input-field min-h-[80px]"
              placeholder="Supplier name, reason for adjustment, etc."
            />
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button type="button" onClick={onClose} className="btn-ghost">Cancel</button>
            <button type="submit" className="btn-primary">
              Save Record
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
