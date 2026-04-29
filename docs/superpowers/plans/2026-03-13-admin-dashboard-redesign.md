# Admin Dashboard & Waiter View Redesign — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign all 6 admin pages and 3 waiter pages with a consistent branded aesthetic (cream backgrounds, Quesha italic titles, linen texture, amber accent) and add UX improvements including master-detail Active Orders, skeleton loading, keyboard nav, inline availability toggle, and clickable rows.

**Architecture:** Introduce 3 new shared components (`LinenTexture`, `PageHeader`, `AdminStatsBar`) and 1 new CSS token (`amber`). All admin pages share `PageHeader`; `LinenTexture` is mounted once in `AdminLayout`. Waiter pages each get `LinenTexture` individually. All existing functional sub-components (modals, denomination counter, charts, menu list) are untouched.

**Tech Stack:** React 18, TypeScript 5, Tailwind CSS v4 (config in `index.css`), Phosphor Icons, React Query, sonner toasts. No test framework — TypeScript build + ESLint serve as the quality gate.

---

## Chunk 1: Foundation — CSS Tokens, Shared Components, AdminLayout

### Task 1: Add `amber` colour token to `index.css`

> **Note:** The spec's "Design Direction" overview says "No new colours are introduced." This is superseded by the spec's own "Colour Palette Addition" section, which explicitly defines and requires the `amber` token. Implement amber as specified in the Colour Palette Addition section.

**Files:**
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Add amber to `@theme {}` block**

  Open `frontend/src/index.css`. Find the `@theme {` block (around line 15). After the existing colour token entries, add:

  ```css
  --color-amber: #C27A2A;
  ```

- [ ] **Step 2: Add amber dark mode override to `.dark {}` block**

  Find the `.dark {` block (around line 50). After the existing dark colour overrides, add:

  ```css
  --color-amber: #D4943F;
  ```

- [ ] **Step 3: Verify build**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build
  ```
  Expected: build succeeds with no type errors.

- [ ] **Step 4: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/index.css && git commit -m "feat(design): add amber colour token to CSS theme"
  ```

---

### Task 2: Create `LinenTexture` component

**Files:**
- Create: `frontend/src/components/LinenTexture.tsx`

The linen texture is a fixed SVG crosshatch overlay — fine horizontal + vertical lines — that sits behind all page content. Opacity differs between light and dark mode.

- [ ] **Step 1: Create the file**

  ```tsx
  // frontend/src/components/LinenTexture.tsx
  import { useTheme } from '../contexts/ThemeContext';

  export default function LinenTexture() {
    const { theme } = useTheme();
    const isDark = theme === 'dark';

    return (
      <div
        className="fixed inset-0 pointer-events-none z-0"
        style={{ opacity: isDark ? 0.05 : 0.08 }}
        aria-hidden="true"
      >
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern
              id="linen-pattern"
              x="0"
              y="0"
              width="4"
              height="4"
              patternUnits="userSpaceOnUse"
            >
              {/* Horizontal thread */}
              <line
                x1="0" y1="0" x2="4" y2="0"
                stroke="var(--color-coffee-light)"
                strokeWidth="0.5"
              />
              {/* Vertical thread */}
              <line
                x1="0" y1="0" x2="0" y2="4"
                stroke="var(--color-coffee-light)"
                strokeWidth="0.5"
              />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#linen-pattern)" />
        </svg>
      </div>
    );
  }
  ```

- [ ] **Step 2: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```
  Expected: clean build, zero lint warnings.

- [ ] **Step 3: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/components/LinenTexture.tsx && git commit -m "feat(design): add LinenTexture background component"
  ```

---

### Task 3: Create `PageHeader` component

**Files:**
- Create: `frontend/src/components/PageHeader.tsx`

Used on all 6 admin pages. Replaces the duplicated hamburger + header pattern. The eyebrow (`LILY CAFE · ADMIN`) renders in lily-green above the italic title. The `action` slot right-aligns on desktop; on mobile (`< lg`) it wraps below the title block as a full-width second row.

- [ ] **Step 1: Create the file**

  ```tsx
  // frontend/src/components/PageHeader.tsx
  import type { ReactNode } from 'react';
  import { useSidebar } from '../context/SidebarContext';
  import { List } from '@phosphor-icons/react';

  interface PageHeaderProps {
    title: string;
    subtitle?: string;
    action?: ReactNode;
  }

  export default function PageHeader({ title, subtitle, action }: PageHeaderProps) {
    const { setMobileOpen } = useSidebar();

    return (
      <header className="bg-off-white border-b-2 border-coffee-brown px-4 py-4 md:px-6 md:py-5 relative z-10">
        <div className="flex items-start gap-4">
          {/* Hamburger — mobile only */}
          <button
            onClick={() => setMobileOpen(true)}
            className="lg:hidden flex-shrink-0 mt-1 w-9 h-9 flex items-center justify-center rounded-lg text-coffee-brown hover:bg-cream/60 transition-colors"
            aria-label="Open menu"
          >
            <List size={22} weight="bold" />
          </button>

          {/* Title block */}
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold tracking-widest uppercase text-lily-green mb-0.5">
              Lily Cafe · Admin
            </p>
            <h1 className="font-heading italic text-2xl md:text-3xl text-coffee-dark leading-tight">
              {title}
            </h1>
            {subtitle && (
              <p className="text-sm text-neutral-text-light mt-0.5">{subtitle}</p>
            )}
          </div>

          {/* Action slot — desktop: right-aligned in same row */}
          {action && (
            <div className="hidden lg:flex flex-shrink-0 items-center">
              {action}
            </div>
          )}
        </div>

        {/* Action slot — mobile: full-width second row */}
        {action && (
          <div className="lg:hidden mt-3">
            {action}
          </div>
        )}
      </header>
    );
  }
  ```

- [ ] **Step 2: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```

- [ ] **Step 3: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/components/PageHeader.tsx && git commit -m "feat(design): add PageHeader shared component"
  ```

---

### Task 4: Create `AdminStatsBar` component

**Files:**
- Create: `frontend/src/components/AdminStatsBar.tsx`

Horizontal stat strip with equal-width cells separated by `neutral-border` dividers. Supports optional `clickable`, `onClick`, and `hint` per cell (used by Order History revenue breakdown).

- [ ] **Step 1: Create the file**

  ```tsx
  // frontend/src/components/AdminStatsBar.tsx
  interface StatItem {
    label: string;
    value: string;
    clickable?: boolean;
    onClick?: () => void;
    hint?: string;
  }

  interface AdminStatsBarProps {
    stats: StatItem[];
  }

  export default function AdminStatsBar({ stats }: AdminStatsBarProps) {
    return (
      <div className="flex border-b border-neutral-border bg-off-white relative z-10">
        {stats.map((stat, index) => {
          const isLast = index === stats.length - 1;
          const cellClass = `
            flex-1 px-4 py-3 text-left
            ${!isLast ? 'border-r border-neutral-border' : ''}
            ${stat.clickable ? 'cursor-pointer hover:bg-cream/50 transition-colors' : ''}
          `;

          // Use explicit conditional rendering to avoid TypeScript polymorphic-tag issues
          const content = (
            <>
              <p className="text-lg font-bold text-coffee-brown leading-tight">
                {stat.value}
              </p>
              <p className="text-xs font-semibold uppercase tracking-wide text-neutral-text-light mt-0.5">
                {stat.label}
              </p>
              {stat.hint && (
                <p className="text-xs text-coffee-light mt-0.5">{stat.hint}</p>
              )}
            </>
          );

          return stat.clickable ? (
            <button key={stat.label} className={cellClass} onClick={stat.onClick}>
              {content}
            </button>
          ) : (
            <div key={stat.label} className={cellClass}>
              {content}
            </div>
          );
        })}
      </div>
    );
  }
  ```

- [ ] **Step 2: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```

- [ ] **Step 3: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/components/AdminStatsBar.tsx && git commit -m "feat(design): add AdminStatsBar shared component"
  ```

---

### Task 5: Update `AdminLayout` — add `LinenTexture`

**Files:**
- Modify: `frontend/src/components/AdminLayout.tsx`

Mount `<LinenTexture />` once in the layout so it applies to all 6 admin pages automatically. Add `relative` and `overflow-hidden` to contain the fixed overlay within the admin shell (the sidebar already fills the full height so this keeps the pattern from bleeding).

- [ ] **Step 1: Modify `AdminLayout.tsx`**

  Replace the entire file with:

  ```tsx
  import { Outlet } from "react-router-dom";
  import Sidebar from "./Sidebar";
  import LinenTexture from "./LinenTexture";
  import { useSidebar } from "../context/SidebarContext";

  export default function AdminLayout() {
    const { isCollapsed } = useSidebar();

    return (
      <div className="flex min-h-screen bg-off-white relative">
        <LinenTexture />
        <Sidebar />
        <main
          className={`
            flex-1 transition-all duration-300 ease-in-out relative z-10
            ${isCollapsed ? "lg:ml-20" : "lg:ml-60"}
          `}
        >
          <Outlet />
        </main>
      </div>
    );
  }
  ```

  Note: `bg-neutral-background` → `bg-off-white` (matches the cream page background from the design spec). `relative z-10` on `<main>` keeps page content above the fixed `LinenTexture` overlay.

- [ ] **Step 2: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```

- [ ] **Step 3: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/components/AdminLayout.tsx && git commit -m "feat(design): add LinenTexture to AdminLayout and switch to off-white background"
  ```

---

## Chunk 2: Admin Active Orders — Full Rewrite

### Task 6: Rewrite `AdminActiveOrdersPage`

**Files:**
- Modify: `frontend/src/pages/AdminActiveOrdersPage.tsx`

This is the largest single change. The current card-grid layout is replaced with a two-panel master-detail layout. Key behaviours to preserve: all modals (Payment, Edit, Cancel Confirm, Partial Serve, EditServedQuantity), serve/edit-served-quantity handlers, all mutations. Key additions: auto-select, keyboard shortcuts with `useMemo`, age warnings, stats bar, skeleton loading, ghost cancel button.

**Layout structure:**
```
PageHeader + AdminStatsBar
┌───────────────────┬─────────────────────────────────┐
│  Order List       │  Detail Panel                   │
│  (240px, lg+)     │  (flex-1, hidden on < lg)       │
│  scrollable       │                                 │
└───────────────────┴─────────────────────────────────┘
```

- [ ] **Step 1: Write the new page**

  Replace `frontend/src/pages/AdminActiveOrdersPage.tsx` in full. The complete implementation follows. Read this carefully before writing it.

  ```tsx
  // frontend/src/pages/AdminActiveOrdersPage.tsx
  import { useState, useEffect, useMemo } from 'react';
  import { toast } from 'sonner';
  import { ClipboardText } from '@phosphor-icons/react';
  import { useSidebar } from '../context/SidebarContext';
  import {
    useActiveOrders,
    useCancelOrder,
    useUpdateItemServedStatus,
    useSetItemServedQuantity
  } from '../hooks/useOrders';
  import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcut';
  import PageHeader from '../components/PageHeader';
  import AdminStatsBar from '../components/AdminStatsBar';
  import EmptyState from '../components/EmptyState';
  import EditOrderModal from '../components/EditOrderModal';
  import PaymentModal from '../components/PaymentModal';
  import ConfirmDialog from '../components/ConfirmDialog';
  import PartialServeModal from '../components/PartialServeModal';
  import EditServedQuantityModal from '../components/EditServedQuantityModal';
  import KeyboardShortcutsHelp from '../components/KeyboardShortcutsHelp';
  import { formatCurrency } from '../utils/formatCurrency';
  import type { Order, OrderItem } from '../types';

  // ── helpers ──────────────────────────────────────────────────────────────────

  function getOrderAgeMinutes(createdAt: string): number {
    return Math.floor((Date.now() - new Date(createdAt).getTime()) / 60_000);
  }

  function ageClass(minutes: number) {
    if (minutes >= 60) return 'border-error bg-[rgba(244,67,54,0.04)]';
    if (minutes >= 30) return 'border-amber bg-[rgba(194,122,42,0.04)]';
    return 'border-lily-green';
  }

  function AgeBadge({ minutes }: { minutes: number }) {
    if (minutes >= 60)
      return (
        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-error/10 text-error">
          ⚠ {minutes}m
        </span>
      );
    if (minutes >= 30)
      return (
        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-amber/10 text-amber">
          ⚑ {minutes}m
        </span>
      );
    return (
      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-lily-green/10 text-lily-green">
        {minutes}m
      </span>
    );
  }

  // ── skeleton ──────────────────────────────────────────────────────────────────

  function Skeleton() {
    return (
      <div className="flex flex-1 overflow-hidden">
        {/* List skeleton */}
        <div className="w-60 flex-shrink-0 border-r border-neutral-border flex flex-col gap-0">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="p-3 border-b border-neutral-border animate-pulse">
              <div className="h-3 w-24 bg-neutral-border/50 rounded mb-2" />
              <div className="h-2.5 w-16 bg-neutral-border/50 rounded" />
            </div>
          ))}
        </div>
        {/* Detail skeleton — hidden on mobile */}
        <div className="hidden lg:flex flex-1 flex-col gap-3 p-6 animate-pulse">
          <div className="h-5 w-32 bg-neutral-border/50 rounded" />
          <div className="h-3 w-48 bg-neutral-border/50 rounded" />
          <div className="h-40 w-full bg-neutral-border/50 rounded mt-4" />
        </div>
      </div>
    );
  }

  // ── order list row ────────────────────────────────────────────────────────────

  interface OrderRowProps {
    order: Order;
    isSelected: boolean;
    onClick: () => void;
  }

  function OrderRow({ order, isSelected, onClick }: OrderRowProps) {
    const age = getOrderAgeMinutes(order.created_at);
    const items = order.order_items || [];
    const servedCount = items.filter(i => i.is_served).length;
    const pendingCount = items.length - servedCount;

    return (
      <button
        onClick={onClick}
        className={`
          w-full text-left px-3 py-3 border-b border-neutral-border/60
          border-l-[3px] transition-colors
          ${isSelected
            ? 'bg-white border-l-coffee-brown'
            : `bg-off-white hover:bg-cream/40 ${ageClass(age)}`
          }
        `}
      >
        <div className="flex items-start justify-between gap-1">
          <div className="min-w-0">
            <p className="text-sm font-bold text-coffee-dark truncate">
              Table {order.table_number}
              {order.customer_name && (
                <span className="font-normal text-neutral-text-light"> — {order.customer_name}</span>
              )}
            </p>
            <p className="text-xs text-neutral-text-light mt-0.5">
              {items.length} item{items.length !== 1 ? 's' : ''}
            </p>
          </div>
          <AgeBadge minutes={age} />
        </div>
        <div className="flex gap-1.5 mt-1.5 flex-wrap">
          {servedCount > 0 && (
            <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-lily-green/10 text-lily-green">
              {servedCount} served
            </span>
          )}
          {pendingCount > 0 && (
            <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-amber/10 text-amber">
              {pendingCount} pending
            </span>
          )}
        </div>
      </button>
    );
  }

  // ── detail panel ──────────────────────────────────────────────────────────────

  interface DetailPanelProps {
    order: Order;
    onGenerateBill: () => void;
    onEdit: () => void;
    onCancel: () => void;
    onOpenServeModal: (item: OrderItem) => void;
    onOpenEditModal: (item: OrderItem) => void;
  }

  function DetailPanel({
    order,
    onGenerateBill,
    onEdit,
    onCancel,
    onOpenServeModal,
    onOpenEditModal,
  }: DetailPanelProps) {
    const age = getOrderAgeMinutes(order.created_at);
    const items = order.order_items || [];
    const dineInItems = items.filter(i => !i.is_parcel);
    const parcelItems = items.filter(i => i.is_parcel);

    const ItemRow = ({ item }: { item: OrderItem }) => (
      <tr className="border-b border-[#F5E6D3] last:border-0">
        <td className="py-2 px-3 text-sm text-coffee-dark">{item.menu_item_name}</td>
        <td className="py-2 px-3 text-sm text-center text-neutral-text-light">{item.quantity}</td>
        <td className="py-2 px-3 text-center">
          {item.is_served ? (
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-lily-green/10 text-lily-green">
              ✓ Served
            </span>
          ) : (
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-amber/10 text-amber">
              Pending
            </span>
          )}
        </td>
        <td className="py-2 px-3 text-right">
          {!item.is_served && (
            <button
              onClick={() => onOpenServeModal(item)}
              className="text-xs font-semibold text-lily-green hover:text-lily-green/80 transition-colors"
            >
              Serve
            </button>
          )}
          {item.is_served && (
            <button
              onClick={() => onOpenEditModal(item)}
              className="text-xs text-neutral-text-light hover:text-coffee-brown transition-colors"
            >
              Edit
            </button>
          )}
        </td>
      </tr>
    );

    return (
      <div className="flex flex-col h-full">
        {/* Detail header */}
        <div className="px-5 py-4 border-b border-neutral-border bg-off-white/80">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="font-heading italic text-xl text-coffee-dark">
                Table {order.table_number}
              </h2>
              <p className="text-xs text-neutral-text-light mt-0.5">
                {order.order_number}
                {order.customer_name && ` · ${order.customer_name}`}
                {' · '}
                <AgeBadge minutes={age} />
              </p>
            </div>
            <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
              parcelItems.length > 0
                ? 'bg-amber/10 text-amber border border-amber/20'
                : 'bg-lily-green/10 text-lily-green border border-lily-green/20'
            }`}>
              {parcelItems.length > 0 ? 'Dine-in + Parcel' : 'Dine-in'}
            </span>
          </div>
        </div>

        {/* Items */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
          {/* Dine-in section */}
          {dineInItems.length > 0 && (
            <div>
              {parcelItems.length > 0 && (
                <p className="text-xs font-bold uppercase tracking-widest text-neutral-text-light mb-2">
                  Dine-in
                </p>
              )}
              <table className="w-full">
                <thead>
                  <tr className="border-b border-neutral-border">
                    <th className="pb-1 px-3 text-left text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Item</th>
                    <th className="pb-1 px-3 text-center text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Qty</th>
                    <th className="pb-1 px-3 text-center text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Status</th>
                    <th className="pb-1 px-3 text-right text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {dineInItems.map(item => <ItemRow key={item.id} item={item} />)}
                </tbody>
              </table>
            </div>
          )}

          {/* Parcel section */}
          {parcelItems.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-1 h-4 bg-amber rounded-full" />
                <p className="text-xs font-bold uppercase tracking-widest text-amber">
                  Parcel
                </p>
              </div>
              <table className="w-full">
                <thead>
                  <tr className="border-b border-neutral-border">
                    <th className="pb-1 px-3 text-left text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Item</th>
                    <th className="pb-1 px-3 text-center text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Qty</th>
                    <th className="pb-1 px-3 text-center text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">Status</th>
                    <th className="pb-1 px-3" />
                  </tr>
                </thead>
                <tbody>
                  {parcelItems.map(item => <ItemRow key={item.id} item={item} />)}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-neutral-border bg-off-white/80">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-neutral-text-light">Total</span>
            <span className="font-heading italic text-xl text-coffee-dark">
              {formatCurrency(order.total_amount)}
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onGenerateBill}
              className="flex-1 bg-coffee-brown text-cream text-sm font-semibold py-2 rounded-lg hover:bg-coffee-dark transition-colors"
            >
              Generate Bill
            </button>
            <button
              onClick={onEdit}
              className="px-4 bg-cream border border-neutral-border text-coffee-dark text-sm font-semibold py-2 rounded-lg hover:bg-neutral-border/30 transition-colors"
            >
              Edit
            </button>
          </div>
          <div className="mt-2 text-center">
            <button
              onClick={onCancel}
              className="text-xs text-neutral-text-light underline hover:text-error transition-colors"
            >
              cancel order
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── empty detail state ────────────────────────────────────────────────────────

  function EmptyDetailPanel() {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-off-white/60 gap-3">
        <div className="w-12 h-12 rounded-full bg-coffee-brown/8 flex items-center justify-center">
          <ClipboardText size={24} weight="duotone" className="text-coffee-brown" />
        </div>
        <p className="text-sm font-semibold text-coffee-dark">Select an order</p>
        <p className="text-xs text-neutral-text-light text-center max-w-[180px]">
          Click any table on the left to view its details here
        </p>
      </div>
    );
  }

  // ── page ──────────────────────────────────────────────────────────────────────

  export default function AdminActiveOrdersPage() {
    const { data: activeOrders, isLoading, error } = useActiveOrders();
    const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);
    const [paymentOrderId, setPaymentOrderId] = useState<number | null>(null);
    const [editOrder, setEditOrder] = useState<Order | null>(null);
    const [cancelOrderId, setCancelOrderId] = useState<number | null>(null);
    const [serveModalData, setServeModalData] = useState<{ item: OrderItem; orderId: number } | null>(null);
    const [editModalData, setEditModalData] = useState<{ item: OrderItem; orderId: number } | null>(null);

    const cancelMutation = useCancelOrder();
    const updateServedMutation = useUpdateItemServedStatus();
    const setServedQuantityMutation = useSetItemServedQuantity();

    const orders = activeOrders || [];
    const selectedOrder = orders.find(o => o.id === selectedOrderId) ?? null;

    // Auto-select first order when none selected
    useEffect(() => {
      if (selectedOrderId === null && orders.length > 0) {
        setSelectedOrderId(orders[0].id);
      }
    }, [orders, selectedOrderId]);

    // Stats
    const liveTotal = orders.reduce((sum, o) => sum + o.total_amount, 0);
    const pendingServe = orders.filter(o =>
      (o.order_items || []).some(i => !i.is_served)
    ).length;
    const readyToBill = orders.filter(o =>
      (o.order_items || []).length > 0 &&
      (o.order_items || []).every(i => i.is_served)
    ).length;

    const stats = [
      { label: 'Active', value: String(orders.length) },
      { label: 'Live Total', value: formatCurrency(liveTotal) },
      { label: 'Pending Serve', value: String(pendingServe) },
      { label: 'Ready to Bill', value: String(readyToBill) },
    ];

    // Modal guards
    const isAnyModalOpen =
      paymentOrderId !== null ||
      editOrder !== null ||
      cancelOrderId !== null ||
      serveModalData !== null ||
      editModalData !== null;

    // Keyboard shortcuts
    const shortcuts = useMemo(() => ({
      ArrowUp: {
        handler: () => {
          if (orders.length === 0) return;
          const idx = orders.findIndex(o => o.id === selectedOrderId);
          const prev = orders[Math.max(0, idx - 1)];
          setSelectedOrderId(prev.id);
        },
        enabled: !isAnyModalOpen,
      },
      ArrowDown: {
        handler: () => {
          if (orders.length === 0) return;
          const idx = orders.findIndex(o => o.id === selectedOrderId);
          const next = orders[Math.min(orders.length - 1, idx + 1)];
          setSelectedOrderId(next.id);
        },
        enabled: !isAnyModalOpen,
      },
      b: {
        handler: () => {
          if (selectedOrderId !== null) setPaymentOrderId(selectedOrderId);
        },
        enabled: !isAnyModalOpen && selectedOrderId !== null,
      },
      e: {
        handler: () => {
          if (selectedOrder) setEditOrder(selectedOrder);
        },
        enabled: !isAnyModalOpen && selectedOrderId !== null,
      },
    }), [selectedOrderId, orders, isAnyModalOpen, selectedOrder]);

    useKeyboardShortcuts(shortcuts);

    // Handlers
    const handleServeItem = (orderId: number, itemId: number, quantityToServe: number) => {
      updateServedMutation.mutate(
        { orderId, itemId, quantityToServe },
        {
          onError: (error) => {
            toast.error('Failed to update served quantity', {
              description: error instanceof Error ? error.message : 'Please try again.',
            });
          },
          onSuccess: () => toast.success('Served quantity updated successfully'),
        }
      );
    };

    const handleEditServedQuantity = (orderId: number, itemId: number, quantityServed: number) => {
      setServedQuantityMutation.mutate(
        { orderId, itemId, quantityServed },
        {
          onError: (error) => {
            toast.error('Failed to update served quantity', {
              description: error instanceof Error ? error.message : 'Please try again.',
            });
          },
          onSuccess: () => toast.success('Served quantity updated successfully'),
        }
      );
    };

    const handleCancelOrder = () => {
      if (!cancelOrderId) return;
      cancelMutation.mutate(cancelOrderId, {
        onSuccess: () => {
          toast.success('Order cancelled successfully');
          setCancelOrderId(null);
          setSelectedOrderId(null); // triggers auto-select via useEffect
        },
        onError: (error) => {
          toast.error('Failed to cancel order', {
            description: error instanceof Error ? error.message : 'Please try again.',
          });
        },
      });
    };

    return (
      <div className="flex flex-col h-screen overflow-hidden">
        <PageHeader
          title="Active Orders"
          subtitle="Manage ongoing orders, generate bills, and process payments"
        />

        <AdminStatsBar stats={stats} />

        {/* Loading */}
        {isLoading && <Skeleton />}

        {/* Error */}
        {!isLoading && error && (
          <div className="p-6">
            <div className="bg-error/10 border border-error rounded-lg p-4">
              <p className="text-error font-medium">
                {error instanceof Error ? error.message : 'Failed to load active orders'}
              </p>
            </div>
          </div>
        )}

        {/* Empty */}
        {!isLoading && !error && orders.length === 0 && (
          <div className="flex-1 flex items-center justify-center">
            <EmptyState
              icon={<ClipboardText size={32} weight="duotone" />}
              title="No active orders"
              description="Once tables send orders, you'll see them listed here ready for billing."
            />
          </div>
        )}

        {/* Master–detail */}
        {!isLoading && orders.length > 0 && (
          <div className="flex flex-1 overflow-hidden">
            {/* Order list — left panel */}
            <div className="w-full lg:w-60 flex-shrink-0 border-r border-neutral-border overflow-y-auto">
              {orders.map(order => (
                <OrderRow
                  key={order.id}
                  order={order}
                  isSelected={order.id === selectedOrderId}
                  onClick={() => setSelectedOrderId(order.id)}
                />
              ))}
            </div>

            {/* Detail panel — right panel, hidden on mobile */}
            <div className="hidden lg:flex flex-1 overflow-hidden">
              {selectedOrder ? (
                <DetailPanel
                  order={selectedOrder}
                  onGenerateBill={() => setPaymentOrderId(selectedOrder.id)}
                  onEdit={() => setEditOrder(selectedOrder)}
                  onCancel={() => setCancelOrderId(selectedOrder.id)}
                  onOpenServeModal={(item) => setServeModalData({ item, orderId: selectedOrder.id })}
                  onOpenEditModal={(item) => setEditModalData({ item, orderId: selectedOrder.id })}
                />
              ) : (
                <EmptyDetailPanel />
              )}
            </div>
          </div>
        )}

        {/* Modals */}
        {editOrder && (
          <EditOrderModal order={editOrder} onClose={() => setEditOrder(null)} />
        )}
        {paymentOrderId && (
          <PaymentModal orderId={paymentOrderId} onClose={() => setPaymentOrderId(null)} />
        )}
        {cancelOrderId && (
          <ConfirmDialog
            isOpen
            onClose={() => setCancelOrderId(null)}
            onConfirm={handleCancelOrder}
            title="Cancel Order?"
            message={`Are you sure you want to cancel Table ${orders.find(o => o.id === cancelOrderId)?.table_number}'s order? This action cannot be undone.`}
            confirmText="Yes, Cancel Order"
            cancelText="No, Keep It"
            variant="danger"
            isLoading={cancelMutation.isPending}
          />
        )}
        {serveModalData && (
          <PartialServeModal
            item={serveModalData.item}
            orderId={serveModalData.orderId}
            onClose={() => setServeModalData(null)}
            onServe={handleServeItem}
          />
        )}
        {editModalData && (
          <EditServedQuantityModal
            item={editModalData.item}
            orderId={editModalData.orderId}
            onClose={() => setEditModalData(null)}
            onSave={handleEditServedQuantity}
          />
        )}

        <KeyboardShortcutsHelp />
      </div>
    );
  }
  ```

- [ ] **Step 2: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```
  Expected: clean build. If TypeScript errors appear, fix them before continuing. Common issues: `PartialServeModal` and `EditServedQuantityModal` props — check their type definitions at `frontend/src/components/`.

- [ ] **Step 3: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/pages/AdminActiveOrdersPage.tsx && git commit -m "feat(admin): rewrite Active Orders with master-detail layout, keyboard nav, age warnings"
  ```

---

## Chunk 3: Remaining Admin Pages

### Task 7: Order History page

**Files:**
- Modify: `frontend/src/pages/OrderHistoryPage.tsx`

Changes: replace header with `<PageHeader>` + `<AdminStatsBar>`; add revenue breakdown expand; toolbar in one row (date picker + search + filter chips); make rows clickable; `line-through` for cancelled. Functional sub-components (date logic, search, filter, sort, print, modal) all stay.

- [ ] **Step 1: Read the current file first**

  Read `frontend/src/pages/OrderHistoryPage.tsx` entirely to understand the current state structure and component boundaries before editing.

- [ ] **Step 2: Replace the header section**

  Locate the `<header>` element (or the equivalent header `div`) at the top of the returned JSX. Replace it with:

  ```tsx
  <PageHeader
    title="Order History"
    subtitle="Review and manage completed orders"
  />
  <AdminStatsBar
    stats={[
      { label: 'Total Orders', value: String(filteredOrders.length) },
      {
        label: 'Revenue',
        value: formatCurrency(totalRevenue),
        clickable: true,
        onClick: () => setIsBreakdownOpen(prev => !prev),
        hint: '↗ tap for breakdown',
      },
      { label: 'Avg Order', value: formatCurrency(avgOrder) },
    ]}
  />
  ```

  Add `isBreakdownOpen` state: `const [isBreakdownOpen, setIsBreakdownOpen] = useState(false);`

  Below `<AdminStatsBar>`, add the conditional breakdown row (uses whatever `paymentBreakdown` variable currently exists in the file — if none exists yet, compute it from `filteredOrders`):

  ```tsx
  {isBreakdownOpen && (
    <div className="flex gap-3 px-4 py-3 border-b border-neutral-border bg-cream/40">
      {paymentBreakdown.map(b => (
        <div key={b.method} className="flex-1 bg-off-white border border-neutral-border rounded-lg px-3 py-2">
          <p className="text-[10px] font-bold uppercase tracking-wide text-neutral-text-light">{b.method}</p>
          <p className="text-sm font-bold text-coffee-brown">{formatCurrency(b.amount)}</p>
          <p className="text-[10px] text-neutral-text-light">{b.pct}%</p>
        </div>
      ))}
    </div>
  )}
  ```

  The `paymentBreakdown` array shape: `{ method: string; amount: number; pct: number }[]`. Compute it from filtered orders if it doesn't already exist, using whatever payment method data is available on each order.

- [ ] **Step 3: Consolidate toolbar to one row**

  Find the toolbar area (date picker, search input, filter chips). Wrap them in a single `div` with `flex flex-wrap gap-2 items-center px-4 py-3 border-b border-neutral-border bg-off-white`. Keep all existing filter logic unchanged.

- [ ] **Step 4: Make table rows clickable**

  On the desktop `<table>` view: add `onClick={handleViewDetails(order)}` (or equivalent) to each `<tr>`, add `cursor-pointer hover:bg-cream/40` to the `<tr>` className, and remove the standalone "View Details" button cell.

  On the mobile card view: add `onClick={handleViewDetails(order)}` and `cursor-pointer` to each card wrapper `div`.

  Both keep any existing Print / Edit action buttons — add `e.stopPropagation()` to their `onClick` handlers to prevent triggering the row click.

- [ ] **Step 5: Style cancelled row amounts**

  In the amount cell for cancelled orders, add `line-through text-neutral-text-light` to the amount text.

- [ ] **Step 6: Add skeleton loading**

  Replace the existing spinner (if present) with a shimmer skeleton shown when `isLoading === true`:

  ```tsx
  {isLoading && (
    <div className="p-6 space-y-2 animate-pulse">
      {/* Stat cells skeleton */}
      <div className="flex gap-0 border border-neutral-border rounded-lg overflow-hidden mb-4">
        {[1,2,3].map(i => (
          <div key={i} className="flex-1 h-14 bg-neutral-border/50" />
        ))}
      </div>
      {/* Table rows skeleton */}
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="h-10 w-full bg-neutral-border/50 rounded" />
      ))}
    </div>
  )}
  ```

- [ ] **Step 7: Add required imports**

  Add to imports:
  ```tsx
  import PageHeader from '../components/PageHeader';
  import AdminStatsBar from '../components/AdminStatsBar';
  ```

- [ ] **Step 8: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```

- [ ] **Step 9: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/pages/OrderHistoryPage.tsx && git commit -m "feat(admin): redesign Order History page with PageHeader, revenue breakdown, clickable rows"
  ```

---

### Task 8: Cash Counter page

**Files:**
- Modify: `frontend/src/pages/CashCounterPage.tsx`

Light-touch Direction C polish only. `DenominationCounter` and all form/modal logic untouched.

- [ ] **Step 1: Read the current file first**

  Read `frontend/src/pages/CashCounterPage.tsx` to understand the current header and card structure.

- [ ] **Step 2: Replace the header**

  Remove the existing header element and replace with `<PageHeader title="Cash Counter" />`. Remove the import of `useSidebar` if it was only used for the hamburger (it's now in `PageHeader`).

- [ ] **Step 3: Update card accent colours**

  Find the card wrapper(s) (the 2-column layout cards). Add a `border-l-4` left accent that reflects the counter state:
  - Counter open: `border-l-4 border-lily-green`
  - Counter pending verification: `border-l-4 border-amber`
  - Counter verified/closed: `border-l-4 border-blue-500` (or equivalent — check existing state constants in the file)

  This is a className addition only — the conditional logic is based on existing state already present in the file.

- [ ] **Step 4: Add skeleton loading**

  Replace any existing full-page spinner with:

  ```tsx
  {isLoading && (
    <div className="p-6 animate-pulse">
      <div className="h-48 w-full bg-neutral-border/50 rounded-xl" />
    </div>
  )}
  ```

- [ ] **Step 5: Add required imports**

  ```tsx
  import PageHeader from '../components/PageHeader';
  ```

- [ ] **Step 6: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```

- [ ] **Step 7: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/pages/CashCounterPage.tsx && git commit -m "feat(admin): apply Direction C polish to Cash Counter page"
  ```

---

### Task 9: Analytics page

**Files:**
- Modify: `frontend/src/pages/AnalyticsPage.tsx`

Light-touch only. All chart components, `AnalyticsDashboard`, `AskQuestionsView`, settings modal untouched.

- [ ] **Step 1: Read the current file first**

  Read `frontend/src/pages/AnalyticsPage.tsx` to understand the current header and view-toggle structure.

- [ ] **Step 2: Replace the header**

  Replace the existing header with `<PageHeader title="Analytics" />`.

- [ ] **Step 3: Restyle the view toggle**

  Find the Dashboard / Ask Questions toggle (currently a border-box style toggle). Replace with a pill toggle:

  ```tsx
  <div className="flex p-1 bg-cream border border-neutral-border rounded-full mx-4 mt-3 mb-0 w-fit">
    <button
      onClick={() => setView('dashboard')}
      className={`px-4 py-1.5 text-sm font-semibold rounded-full transition-colors ${
        view === 'dashboard'
          ? 'bg-coffee-brown text-cream shadow-sm'
          : 'text-neutral-text-light hover:text-coffee-dark'
      }`}
    >
      Dashboard
    </button>
    <button
      onClick={() => setView('ask')}
      className={`px-4 py-1.5 text-sm font-semibold rounded-full transition-colors ${
        view === 'ask'
          ? 'bg-coffee-brown text-cream shadow-sm'
          : 'text-neutral-text-light hover:text-coffee-dark'
      }`}
    >
      Ask Questions
    </button>
  </div>
  ```

  Adapt the state variable name (`view`, `activeView`, etc.) and string values to match what the existing file uses.

- [ ] **Step 4: Add skeleton loading**

  ```tsx
  {isLoading && (
    <div className="p-6 animate-pulse space-y-4">
      <div className="flex gap-2">
        {[1,2,3,4].map(i => <div key={i} className="flex-1 h-20 bg-neutral-border/50 rounded-xl" />)}
      </div>
      <div className="h-60 w-full bg-neutral-border/50 rounded-xl" />
    </div>
  )}
  ```

- [ ] **Step 5: Add required imports**

  ```tsx
  import PageHeader from '../components/PageHeader';
  ```

- [ ] **Step 6: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```

- [ ] **Step 7: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/pages/AnalyticsPage.tsx && git commit -m "feat(admin): apply Direction C polish to Analytics page"
  ```

---

### Task 10: Inventory page

**Files:**
- Modify: `frontend/src/pages/InventoryPage.tsx`

Light-touch only. Tab content components untouched.

- [ ] **Step 1: Read the current file first**

  Read `frontend/src/pages/InventoryPage.tsx` to understand the header and tab structure.

- [ ] **Step 2: Replace the header**

  Replace with `<PageHeader title="Inventory" />`.

- [ ] **Step 3: Restyle the tab bar**

  Find the tab bar (buttons for Daily Count, Items, Categories, Transactions). Restyle to underline-style with a `coffee-brown` indicator replacing the current button-style tabs:

  ```tsx
  <div className="flex border-b border-neutral-border px-4 bg-off-white">
    {tabs.map(tab => (
      <button
        key={tab.id}
        onClick={() => setActiveTab(tab.id)}
        className={`px-4 py-3 text-sm font-semibold transition-colors border-b-2 -mb-[2px] ${
          activeTab === tab.id
            ? 'border-coffee-brown text-coffee-brown'
            : 'border-transparent text-neutral-text-light hover:text-coffee-dark'
        }`}
      >
        {tab.label}
      </button>
    ))}
  </div>
  ```

  Adapt tab IDs, labels, and active state variable to match the existing file.

- [ ] **Step 4: Add skeleton loading**

  ```tsx
  {isLoading && (
    <div className="p-6 animate-pulse space-y-2">
      <div className="flex gap-4 mb-4">
        {[1,2,3,4].map(i => <div key={i} className="h-8 w-24 bg-neutral-border/50 rounded" />)}
      </div>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="h-10 w-full bg-neutral-border/50 rounded" />
      ))}
    </div>
  )}
  ```

- [ ] **Step 5: Add required imports**

  ```tsx
  import PageHeader from '../components/PageHeader';
  ```

- [ ] **Step 6: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```

- [ ] **Step 7: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/pages/InventoryPage.tsx && git commit -m "feat(admin): apply Direction C polish to Inventory page"
  ```

---

### Task 11: Menu Management page

**Files:**
- Modify: `frontend/src/pages/MenuManagementPage.tsx`

Changes: `PageHeader` with `+ Add Item` action slot; horizontal-scrolling category filter chips toolbar; table row hover + dividers; inline availability toggle (no modal). `MenuItemForm` modal untouched.

- [ ] **Step 1: Read the current file first**

  Read `frontend/src/pages/MenuManagementPage.tsx` entirely.

- [ ] **Step 2: Replace the header with action slot**

  ```tsx
  <PageHeader
    title="Menu Management"
    action={
      <button
        onClick={() => setIsAddModalOpen(true)} // use existing handler/state
        className="flex items-center gap-1.5 bg-coffee-brown text-cream text-sm font-semibold px-4 py-2 rounded-lg hover:bg-coffee-dark transition-colors w-full justify-center lg:w-auto"
      >
        <span className="text-lg leading-none">+</span>
        Add Item
      </button>
    }
  />
  ```

- [ ] **Step 3: Consolidate toolbar**

  Place the search input and category filter chips in one row:

  ```tsx
  <div className="px-4 py-3 border-b border-neutral-border bg-off-white space-y-2">
    {/* Search */}
    <div className="relative">
      {/* existing search input */}
    </div>
    {/* Category chips — horizontal scroll */}
    <div className="flex gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
      <button
        onClick={() => setSelectedCategory(null)}
        className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
          selectedCategory === null
            ? 'bg-coffee-brown text-cream'
            : 'bg-cream border border-neutral-border text-coffee-dark hover:border-coffee-brown'
        }`}
      >
        All
      </button>
      {categories?.map(cat => (
        <button
          key={cat.id}
          onClick={() => setSelectedCategory(cat.id)}
          className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
            selectedCategory === cat.id
              ? 'bg-coffee-brown text-cream'
              : 'bg-cream border border-neutral-border text-coffee-dark hover:border-coffee-brown'
          }`}
        >
          {cat.name}
        </button>
      ))}
    </div>
  </div>
  ```

  Adapt state variable names to match existing code.

- [ ] **Step 4: Add inline availability toggle**

  In the table, find the "Available" column. Replace the current status dot with a toggle switch.

  Add a `useUpdateMenuItem` hook instantiation and a local optimistic-state map near the top of the component (after existing hooks):
  ```tsx
  const updateMenuItemMutation = useUpdateMenuItem();
  // Optimistic toggle map: { [itemId]: optimistic is_available }
  const [optimisticAvail, setOptimisticAvail] = useState<Record<number, boolean>>({});
  ```

  The effective availability for display is `optimisticAvail[item.id] ?? item.is_available`.

  Add handler:
  ```tsx
  const handleToggleAvailability = (item: MenuItem) => {
    const newValue = !( optimisticAvail[item.id] ?? item.is_available );
    // Flip optimistically
    setOptimisticAvail(prev => ({ ...prev, [item.id]: newValue }));
    updateMenuItemMutation.mutate(
      { id: item.id, data: { ...item, is_available: newValue } },
      {
        onSuccess: () => {
          // Clear optimistic entry — query invalidation will show real value
          setOptimisticAvail(prev => { const n = { ...prev }; delete n[item.id]; return n; });
        },
        onError: () => {
          // Revert optimistic entry
          setOptimisticAvail(prev => { const n = { ...prev }; delete n[item.id]; return n; });
          toast.error('Failed to update availability');
        },
      }
    );
  };

  // Toggle cell JSX — use the effective availability for display
  // effectiveAvail = optimisticAvail[item.id] ?? item.is_available
  <td className="py-3 px-4">
    <label className="flex items-center gap-1.5 cursor-pointer w-fit">
      <button
        role="switch"
        aria-checked={effectiveAvail}
        onClick={() => handleToggleAvailability(item)}
        className={`relative inline-flex w-8 h-5 rounded-full transition-colors ${
          effectiveAvail ? 'bg-lily-green' : 'bg-neutral-border'
        }`}
      >
        <span className={`inline-block w-3.5 h-3.5 rounded-full bg-white shadow transition-transform absolute top-[3px] ${
          effectiveAvail ? 'translate-x-[14px]' : 'translate-x-[3px]'
        }`} />
      </button>
      <span className={`text-xs font-semibold ${
        effectiveAvail ? 'text-lily-green' : 'text-neutral-text-light'
      }`}>
        {effectiveAvail ? 'On' : 'Off'}
      </span>
    </label>
  </td>
  ```

  Derive `effectiveAvail` per-row inside the `.map()` callback:
  ```tsx
  const effectiveAvail = optimisticAvail[item.id] ?? item.is_available;
  ```

  For unavailable items (where `!effectiveAvail`), add `text-neutral-text-light` to the item name and price cells.

- [ ] **Step 5: Add row hover + dividers**

  On each `<tr>`: add `hover:bg-cream/40 transition-colors`. For `<td>` borders use `border-b border-[#F5E6D3]`.

- [ ] **Step 6: Add skeleton loading**

  ```tsx
  {isLoading && (
    <div className="p-6 animate-pulse space-y-2">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="h-10 w-full bg-neutral-border/50 rounded" />
      ))}
    </div>
  )}
  ```

- [ ] **Step 7: Add required imports**

  ```tsx
  import { useState } from 'react'; // if not already imported
  import PageHeader from '../components/PageHeader';
  import { useUpdateMenuItem } from '../hooks/useMenu';
  import { toast } from 'sonner';
  ```

- [ ] **Step 8: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```

- [ ] **Step 9: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/pages/MenuManagementPage.tsx && git commit -m "feat(admin): redesign Menu Management with inline availability toggle and toolbar"
  ```

---

## Chunk 4: Waiter View

### Task 12: Polish `BottomNav`

**Files:**
- Modify: `frontend/src/components/BottomNav.tsx`

Change: remove `bg-gradient-primary text-cream` from active tab; replace with `text-coffee-brown` + 2px `coffee-brown` top border indicator.

- [ ] **Step 1: Update active tab styles**

  In `BottomNav.tsx`, find the `isActive` className block on the `<Link>` element:

  Current active: `bg-gradient-primary text-cream`
  New active: `text-coffee-brown`

  Current inactive: `text-neutral-text-light hover:text-coffee-brown hover:bg-cream/60`
  Inactive: unchanged.

  Current indicator (inside Link): `<div className="absolute top-0 left-0 right-0 h-1 bg-cream rounded-b-full">`
  New indicator: `<div className="absolute top-0 left-0 right-0 h-[2px] bg-coffee-brown">`

  The `<Link>` className should become:
  ```tsx
  className={`
    flex-1 flex flex-col items-center justify-center gap-1.5
    smooth-transition min-h-touch cursor-pointer relative
    ${isActive
      ? 'text-coffee-brown'
      : 'text-neutral-text-light hover:text-coffee-brown hover:bg-cream/60'
    }
  `}
  ```

  The existing `<span className={`text-2xl ${isActive ? 'scale-110' : ''} smooth-transition`}>` wrapper around the icon is **unchanged** — leave it as-is.

- [ ] **Step 2: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```

- [ ] **Step 3: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/components/BottomNav.tsx && git commit -m "feat(waiter): restyle BottomNav active tab from gradient to coffee-brown indicator"
  ```

---

### Task 13: Update `TablesPage`

**Files:**
- Modify: `frontend/src/pages/TablesPage.tsx`

Changes: swap `<BackgroundPattern>` → `<LinenTexture>`; add eyebrow line to header.

- [ ] **Step 1: Replace BackgroundPattern import and usage**

  Remove: `import BackgroundPattern from '../components/BackgroundPattern';`
  Add: `import LinenTexture from '../components/LinenTexture';`

  In the JSX, replace `<BackgroundPattern opacity={0.04} density="light" />` with `<LinenTexture />`.

- [ ] **Step 2: Add eyebrow to header**

  Inside `<header>`, above the `<h1>`:

  ```tsx
  <p className="text-xs font-semibold tracking-widest uppercase text-lily-green/80 text-center mb-0.5">
    Lily Cafe
  </p>
  ```

- [ ] **Step 3: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```

- [ ] **Step 4: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/pages/TablesPage.tsx && git commit -m "feat(waiter): add LinenTexture and header eyebrow to TablesPage"
  ```

---

### Task 14: Update waiter `OrderPage`

**Files:**
- Modify: `frontend/src/pages/OrderPage.tsx`

Change: swap `<BackgroundPattern>` → `<LinenTexture>`. No other changes.

- [ ] **Step 1: Replace BackgroundPattern**

  Remove: `import BackgroundPattern from '../components/BackgroundPattern';`
  Add: `import LinenTexture from '../components/LinenTexture';`

  Replace `<BackgroundPattern opacity={0.04} density="light" />` with `<LinenTexture />`.

- [ ] **Step 2: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```

- [ ] **Step 3: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/pages/OrderPage.tsx && git commit -m "feat(waiter): swap BackgroundPattern for LinenTexture in OrderPage"
  ```

---

### Task 15: Restyle waiter `ActiveOrdersPage`

**Files:**
- Modify: `frontend/src/pages/ActiveOrdersPage.tsx`

Changes: switch header to `bg-gradient-primary`; add eyebrow; add `<LinenTexture>`; restyle cards (cream bg, left accent, clickable, serve-status strip); inline name edit preserved with `e.stopPropagation()`; add served/unserved status in details modal.

- [ ] **Step 1: Add LinenTexture and update header**

  Add `import LinenTexture from '../components/LinenTexture';`.

  Replace the existing `<header className="bg-coffee-brown text-cream...">` with:

  ```tsx
  <header className="bg-gradient-primary text-cream p-4 sticky top-0 z-30 shadow-md">
    <p className="text-[10px] font-semibold tracking-widest uppercase text-lily-green/80 text-center mb-0.5">
      Lily Cafe · Orders
    </p>
    <h1 className="font-heading heading-sub text-center">Active Orders</h1>
  </header>
  ```

  Add `<LinenTexture />` as the first child inside the outer `<div>`.

- [ ] **Step 2: Restyle `OrderCard`**

  In the `OrderCard` component, update the card `<div>` className:

  ```tsx
  // Old
  className="bg-off-white border border-neutral-border rounded-lg p-4 shadow-sm"

  // New
  className={`
    bg-cream border border-neutral-border rounded-lg p-4 shadow-sm
    border-l-4 border-l-coffee-brown
    cursor-pointer hover:shadow-md transition-shadow
  `}
  onClick={!isEditingName ? onViewDetails : undefined}
  ```

  After the item count / date row, add a serve-status strip:
  ```tsx
  {/* Serve status strip */}
  <div className="flex gap-1.5 mt-1 mb-3">
    {(() => {
      const items = order.order_items || [];
      const served = items.filter(i => i.is_served).length;
      const pending = items.length - served;
      return (
        <>
          {served > 0 && (
            <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-lily-green/10 text-lily-green">
              {served} served
            </span>
          )}
          {pending > 0 && (
            <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-amber/10 text-amber">
              {pending} pending
            </span>
          )}
        </>
      );
    })()}
  </div>
  ```

  Remove the "View Details" `<button>` at the bottom of the card (the card itself is now the click target).

- [ ] **Step 3: Add `e.stopPropagation()` to inline edit elements**

  In the `isEditingName` edit-mode JSX, add propagation guards:

  - **Pencil button**: change `onClick` to `onClick={(e) => { e.stopPropagation(); setIsEditingName(true); }}`
  - **Name `<input>`**: add both `onClick={(e) => e.stopPropagation()}` AND change `onChange` to `onChange={(e) => { e.stopPropagation(); setCustomerName(e.target.value); }}` — the `onChange` guard is critical: without it, every keystroke in the input bubbles to the card's `onViewDetails` and reopens the order detail modal
  - **Save `<button>`**: add `onClick={(e) => { e.stopPropagation(); handleSaveName(); }}`
  - **Cancel `<button>`**: add `onClick={(e) => { e.stopPropagation(); handleCancelEdit(); }}`

- [ ] **Step 4: Add served/pending status in details modal**

  In `OrderDetailsModal`, in the items list section, next to each item add a status indicator:

  ```tsx
  {order.order_items.map((item: any, index: number) => (
    <div key={index} className="flex justify-between items-start bg-cream rounded-lg p-3">
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <p className="font-medium text-neutral-text-dark">{item.menu_item_name}</p>
          {item.is_parcel && (
            <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-amber/10 text-amber border border-amber/20">
              Parcel
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          <p className="text-sm text-neutral-text-light">
            Qty: {item.quantity} × {formatCurrency(item.unit_price)}
          </p>
          {item.is_served !== undefined && (
            <span className={`text-[9px] font-semibold ${
              item.is_served ? 'text-lily-green' : 'text-amber'
            }`}>
              {item.is_served ? '✓ Served' : 'Pending'}
            </span>
          )}
        </div>
      </div>
      <p className="font-semibold text-coffee-brown">{formatCurrency(item.subtotal)}</p>
    </div>
  ))}
  ```

- [ ] **Step 5: Verify build + lint**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```

- [ ] **Step 6: Commit**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos && git add frontend/src/pages/ActiveOrdersPage.tsx && git commit -m "feat(waiter): restyle ActiveOrdersPage with gradient header, clickable cards, serve status"
  ```

---

## Final Verification

- [ ] **Full build + lint pass**

  ```bash
  cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run build && npm run lint
  ```
  Expected: zero errors, zero warnings.

- [ ] **Visual check — admin**

  Start the dev server: `cd /Users/angelxlakra/dev/lily-cafe-pos/frontend && npm run dev`

  Verify in browser:
  - Admin pages all show `PageHeader` with eyebrow, italic title, 2px coffee-brown bottom rule
  - Linen texture visible (subtle crosshatch in background of all admin pages)
  - Active Orders: master-detail layout, age badges, keyboard nav (↑↓ to navigate, `b` for bill, `e` for edit)
  - Menu Management: inline availability toggle works (no modal)
  - Order History: revenue breakdown expands when clicked

- [ ] **Visual check — waiter**

  Navigate to `/tables`, `/order/:n`, `/active-orders`:
  - Linen texture visible on all waiter pages
  - BottomNav: active tab shows `coffee-brown` indicator (not gradient fill)
  - Waiter active orders: cards are cream with left accent, entire card is clickable
  - **Inline edit conflict test**: tap the pencil icon on a waiter ActiveOrders card → input should open without triggering the order detail modal. Type in the input → modal should NOT reopen on each keystroke. Tap save/cancel → edit closes without reopening the modal.
