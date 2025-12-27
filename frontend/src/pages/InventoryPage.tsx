import { useState } from 'react';
import { Package, Tag, ClockCounterClockwise, ClipboardText } from '@phosphor-icons/react';
import BottomNav from '../components/BottomNav';
import Sidebar from '../components/Sidebar';
import ThemeToggle from '../components/ThemeToggle';
import DailyCountTab from '../components/inventory/DailyCountTab';
import InventoryItemsTab from '../components/inventory/InventoryItemsTab';
import InventoryCategoriesTab from '../components/inventory/InventoryCategoriesTab';
import InventoryTransactionsTab from '../components/inventory/InventoryTransactionsTab';

type Tab = 'daily-count' | 'items' | 'categories' | 'transactions';

export default function InventoryPage() {
  const [activeTab, setActiveTab] = useState<Tab>('daily-count');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-neutral-background pb-16 lg:pb-0 lg:pl-60 transition-all duration-300">
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      {/* Header */}
      <header className="bg-gradient-primary text-cream p-6 sticky top-0 z-30 shadow-medium">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-heading heading-sub text-cream">Inventory Management</h1>
            <div className="text-cream/80 text-sm mt-1 font-medium">Track stock, purchases, and usage</div>
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

        {/* Tabs */}
        <div className="flex space-x-1 mt-6 overflow-x-auto pb-1 scrollbar-hide">
          <TabButton
            active={activeTab === 'daily-count'}
            onClick={() => setActiveTab('daily-count')}
            icon={<ClipboardText size={20} />}
            label="Daily Count"
          />
          <TabButton
            active={activeTab === 'items'}
            onClick={() => setActiveTab('items')}
            icon={<Package size={20} />}
            label="Items"
          />
          <TabButton
            active={activeTab === 'categories'}
            onClick={() => setActiveTab('categories')}
            icon={<Tag size={20} />}
            label="Categories"
          />
          <TabButton
            active={activeTab === 'transactions'}
            onClick={() => setActiveTab('transactions')}
            icon={<ClockCounterClockwise size={20} />}
            label="History"
          />
        </div>
      </header>

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

function TabButton({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all
        ${active 
          ? 'bg-cream text-coffee-brown shadow-sm' 
          : 'text-cream/70 hover:bg-white/10 hover:text-cream'
        }
      `}
    >
      {icon}
      {label}
    </button>
  );
}
