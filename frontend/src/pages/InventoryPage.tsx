import { useState } from 'react';
import { Package, Tag, ClockCounterClockwise, ClipboardText } from '@phosphor-icons/react';
import PageHeader from '../components/PageHeader';
import BottomNav from '../components/BottomNav';
import DailyCountTab from '../components/inventory/DailyCountTab';
import InventoryItemsTab from '../components/inventory/InventoryItemsTab';
import InventoryCategoriesTab from '../components/inventory/InventoryCategoriesTab';
import InventoryTransactionsTab from '../components/inventory/InventoryTransactionsTab';

type Tab = 'daily-count' | 'items' | 'categories' | 'transactions';

const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'daily-count', label: 'Daily Count', icon: <ClipboardText size={20} /> },
  { id: 'items', label: 'Items', icon: <Package size={20} /> },
  { id: 'categories', label: 'Categories', icon: <Tag size={20} /> },
  { id: 'transactions', label: 'History', icon: <ClockCounterClockwise size={20} /> },
];

export default function InventoryPage() {
  const [activeTab, setActiveTab] = useState<Tab>('daily-count');

  return (
    <div className="flex flex-col h-full bg-neutral-background">

      <PageHeader title="Inventory" />

      {/* Tab bar */}
      <div className="flex border-b border-neutral-border px-4 bg-off-white relative z-10">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-3 text-sm font-semibold transition-colors border-b-2 -mb-[2px] whitespace-nowrap flex items-center gap-2 ${
              activeTab === tab.id
                ? 'border-coffee-brown text-coffee-brown'
                : 'border-transparent text-neutral-text-light hover:text-coffee-dark'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      <main className="p-4 lg:p-6 max-w-7xl mx-auto">
        {activeTab === 'daily-count' && <DailyCountTab />}
        {activeTab === 'items' && <InventoryItemsTab />}
        {activeTab === 'categories' && <InventoryCategoriesTab />}
        {activeTab === 'transactions' && <InventoryTransactionsTab />}
      </main>

      <div className="lg:hidden">
        <BottomNav />
      </div>
    </div>
  );
}
