import { useLayoutEffect, useRef, useState } from 'react';
import { Package, Tag, ClockCounterClockwise, ClipboardText, ShoppingCart } from '@phosphor-icons/react';
import { useSidebar } from '../context/SidebarContext';
import { useAuth } from '../hooks/useAuth';
import DailyCountTab from '../components/inventory/DailyCountTab';
import PurchaseSheetTab from '../components/inventory/PurchaseSheetTab';
import InventoryItemsTab from '../components/inventory/InventoryItemsTab';
import InventoryCategoriesTab from '../components/inventory/InventoryCategoriesTab';
import InventoryTransactionsTab from '../components/inventory/InventoryTransactionsTab';

type Tab = 'daily-count' | 'purchases' | 'items' | 'categories' | 'transactions';

const TABS: { id: Tab; label: string; icon: JSX.Element; ownerOnly?: boolean }[] = [
  { id: 'daily-count', label: 'Daily count', icon: <ClipboardText size={20} aria-hidden /> },
  { id: 'purchases', label: 'Purchases', icon: <ShoppingCart size={20} aria-hidden /> },
  { id: 'items', label: 'Items', icon: <Package size={20} aria-hidden />, ownerOnly: true },
  { id: 'categories', label: 'Categories', icon: <Tag size={20} aria-hidden />, ownerOnly: true },
  { id: 'transactions', label: 'Stock log', icon: <ClockCounterClockwise size={20} aria-hidden /> },
];

export default function InventoryPage() {
  const [activeTab, setActiveTab] = useState<Tab>('daily-count');
  const { setMobileOpen } = useSidebar();
  // Items and categories are owner-only master data: admins don't see them.
  const { isOwner } = useAuth();
  const tabs = TABS.filter(tab => isOwner || !tab.ownerOnly);

  // One underline that slides to the selected tab, so the eye follows the
  // switch instead of seeing one line vanish and another appear.
  const tabRefs = useRef(new Map<Tab, HTMLButtonElement>());
  const [indicator, setIndicator] = useState<{ left: number; width: number } | null>(null);
  useLayoutEffect(() => {
    const measure = () => {
      const tab = tabRefs.current.get(activeTab);
      if (tab) setIndicator({ left: tab.offsetLeft, width: tab.offsetWidth });
    };
    measure();
    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, [activeTab, tabs.length]);

  // Tabs behave like tabs for the keyboard: one stop in the tab order, then
  // arrows (and Home/End) move between them.
  const onTabKeyDown = (event: React.KeyboardEvent) => {
    const step = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0;
    let next = -1;
    if (step) next = (tabs.findIndex(tab => tab.id === activeTab) + step + tabs.length) % tabs.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = tabs.length - 1;
    if (next < 0) return;
    event.preventDefault();
    setActiveTab(tabs[next].id);
    tabRefs.current.get(tabs[next].id)?.focus();
  };

  return (
    <div className="flex flex-col min-h-full bg-neutral-background">
      {/* Not sticky: on a phone a pinned title and tab row would eat a fifth of the screen. */}
      <header className="bg-off-white border-b border-neutral-border px-4 pt-4 md:px-6 md:pt-6">
        <div className="flex items-center justify-between gap-3">
          <h1 className="font-heading heading-section text-neutral-text-dark">Inventory</h1>
          <button
            onClick={() => setMobileOpen(true)}
            className="lg:hidden size-12 -mr-2 grid place-items-center text-coffee-brown hover:bg-neutral-border/50 rounded-lg"
          >
            <span className="sr-only">Open menu</span>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>

        <div role="tablist" aria-label="Inventory sections" className="relative flex gap-1 mt-4 -mx-1 overflow-x-auto scrollbar-hide">
          {tabs.map(tab => (
            <button
              key={tab.id}
              role="tab"
              id={`inventory-tab-${tab.id}`}
              aria-selected={activeTab === tab.id}
              aria-controls="inventory-panel"
              tabIndex={activeTab === tab.id ? 0 : -1}
              onKeyDown={onTabKeyDown}
              ref={element => {
                if (element) tabRefs.current.set(tab.id, element);
                else tabRefs.current.delete(tab.id);
              }}
              onClick={event => {
                setActiveTab(tab.id);
                event.currentTarget.scrollIntoView({ block: 'nearest', inline: 'nearest' });
              }}
              className={`shrink-0 min-h-12 flex items-center gap-2 px-3 text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id ? 'text-coffee-brown' : 'text-neutral-text-light hover:text-coffee-brown'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
          {indicator && (
            <span
              aria-hidden
              className="absolute bottom-0 left-0 h-0.5 rounded-full bg-coffee-brown transition-[translate,width] duration-250 ease-(--ease-settle) motion-reduce:transition-none"
              style={{ translate: `${indicator.left}px 0`, width: indicator.width }}
            />
          )}
        </div>
      </header>

      <main
        id="inventory-panel"
        role="tabpanel"
        aria-labelledby={`inventory-tab-${activeTab}`}
        className="p-4 lg:p-6 w-full"
      >
        {activeTab === 'daily-count' && <DailyCountTab />}
        {activeTab === 'purchases' && <PurchaseSheetTab />}
        {isOwner && activeTab === 'items' && <InventoryItemsTab />}
        {isOwner && activeTab === 'categories' && <InventoryCategoriesTab />}
        {activeTab === 'transactions' && <InventoryTransactionsTab />}
      </main>
    </div>
  );
}
