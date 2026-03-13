# Admin Dashboard Redesign — Design Spec

**Date:** 2026-03-13
**Scope:** All 6 admin pages + shared component layer
**Status:** Approved for implementation

---

## Overview

A holistic redesign of the Lily Cafe admin portal. The goal is to give every admin page a distinctive, branded identity that matches the café's warm character, improve information hierarchy, and fix specific UX friction points — particularly on Active Orders.

The redesign does **not** change any backend APIs, existing functional sub-components (DenominationCounter, payment icons, chart components), or the waiter-facing front-of-house pages.

---

## Design Direction

**C — Branded & Editorial**

- Cream (`#FAF8F5`) backgrounds throughout — no dark/gradient page headers
- Italic Quesha font for all page titles — e.g. *Active Orders*
- 2px `coffee-brown` (`#6F4E37`) bottom rule on every page header — the single consistent accent
- Eyebrow text above every title: `LILY CAFE · ADMIN` in lily-green, uppercase, wide tracking
- Stats shown in horizontal bar directly below header where applicable — cells separated by `neutral-border` dividers

The existing Tailwind colour palette is unchanged. No new colours are introduced.

---

## Shared Components

### `PageHeader`

New shared component used on all 6 admin pages. Replaces the duplicated hamburger + header code currently copy-pasted across every page.

**Props:**
- `title: string` — page title (rendered italic in Quesha)
- `subtitle?: string` — muted description line
- `action?: ReactNode` — optional right-side slot (e.g. "+ Add Item" button)

**Structure:**
```
[hamburger (mobile only)] [eyebrow: LILY CAFE · ADMIN] [italic title] [subtitle]  [action slot]
─────────────────────────────────────────────────── (2px coffee-brown border)
```

The hamburger button calls `setMobileOpen(true)` from `useSidebar()` — same as current pages.

**`action` slot mobile behaviour:** On small screens (`< lg`), the action slot wraps to a second row below the title/subtitle block, full-width (`w-full`). On `lg+` it stays right-aligned in the same flex row.

**Dark mode:** The 2px bottom rule uses `border-coffee-brown` which resolves to `#B8916A` in dark mode via the CSS variable — this is the intended behaviour, no special casing needed.

### `AdminStatsBar`

Optional horizontal stat strip rendered directly below `PageHeader`. Used on Active Orders and Order History. Not used on Cash Counter, Analytics, Inventory, or Menu Management.

**Props:**
- `stats: Array<{ label: string; value: string; clickable?: boolean; onClick?: () => void; hint?: string }>`

Each stat occupies equal width, separated by `neutral-border` vertical dividers. The optional `hint` string renders as a small muted line below the value (e.g. `"↗ tap for breakdown"`). The `onClick` handler is called when the cell is clicked (only when `clickable: true`).

**Revenue breakdown in Order History:** The breakdown expand is implemented directly in `OrderHistoryPage`, not inside `AdminStatsBar`. `AdminStatsBar` receives `clickable: true`, `hint: "↗ tap for breakdown"`, and an `onClick` callback. The `OrderHistoryPage` manages `isBreakdownOpen` state and renders an inline breakdown row below `<AdminStatsBar>` when open, using the existing `paymentBreakdown` value.

**Active Orders stat definitions:**
- `Active` — `orders.length` (total count of active orders including partially-served)
- `Live Total` — sum of `order.total_amount` across all active orders, formatted with `formatCurrency`
- `Pending Serve` — count of orders where at least one item has `is_served === false`
- `Ready to Bill` — count of orders where every item has `is_served === true`

### Design Tokens (no changes — roles clarified)

| Token | Role |
|---|---|
| `coffee-dark` | Page titles, headings |
| `coffee-brown` | Primary actions, accent rule |
| `cream` | Card/elevated surfaces |
| `off-white` | Page background |
| `lily-green` | Success, served status |
| `neutral-border` | Dividers, card borders |

### Button Hierarchy

| Variant | Usage |
|---|---|
| Primary (coffee-brown fill) | `Generate Bill`, `Open Counter`, `Verify & Approve` |
| Secondary (cream bg, border) | `Edit Order`, `Edit Payments`, `Reopen Counter` |
| Success (lily-green tint) | `Mark Served`, `Print Receipt` |
| Ghost (underline only) | `cancel order` — destructive but de-emphasised |

The large red "Cancel Order" button currently present on every Active Orders card is replaced with a ghost-style underline link in the detail panel footer.

### Status Badges

Consistent pill badges across all pages:

| Badge | Colour |
|---|---|
| `✓ Served` | lily-green tint, green text |
| `Pending` | amber tint, amber text |
| `Cancelled` | red tint, red text |
| `Parcel` | coffee-brown tint, dark text |

---

## Page Designs

### 1. Active Orders

**Layout change: master–detail split**

Replaces the current card grid with a two-panel layout:

```
┌─────────────────────────────────────────────────────┐
│ PageHeader                                          │
│ AdminStatsBar: Active | Live Total | Pending Serve | Ready to Bill │
├──────────────────────┬──────────────────────────────┤
│  Order List (left)   │  Detail Panel (right)        │
│  ─ scrollable        │  ─ selected order            │
│  ─ one row per order │  ─ items table               │
│  ─ 200px wide        │  ─ dine-in + parcel sections │
│                      │  ─ total + action buttons    │
└──────────────────────┴──────────────────────────────┘
```

**Order list row** (left panel):
- Table number + customer name (if present)
- Item count + age
- Serve-status badges: e.g. `2 served`, `1 pending`
- Active selection: 3px left border in `coffee-brown`, white background
- Age warning: border turns amber after 30 min, red after 60 min (see UX improvements)

**Detail panel** (right panel):
- Header: table number, customer name, order number, age, dine-in/parcel indicator
- Dine-in items table: Item | Qty | Status | Serve button
- Parcel section (if present): same table, visually separated with a `coffee-brown` left-accent header
- Footer: total amount, `Generate Bill` (primary), `Edit` (secondary), `cancel order` (ghost)
- Empty state when no order selected: centred icon + "Select an order from the list"

**State inventory for `AdminActiveOrdersPage`:**
```ts
const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);
const [paymentOrderId, setPaymentOrderId]   = useState<number | null>(null); // opens PaymentModal
const [editOrder, setEditOrder]             = useState<Order | null>(null);   // opens EditOrderModal
const [cancelOrderId, setCancelOrderId]     = useState<number | null>(null);  // opens cancel confirm
const [serveModalData, setServeModalData]   = useState<...| null>(null);      // opens PartialServeModal
const [editModalData, setEditModalData]     = useState<...| null>(null);      // opens item edit modal
```
`cancelOrderId` drives a cancel-confirmation UI; setting it non-null signals "confirm cancel for this order ID".

**Auto-select:** On page load, a `useEffect` watching `orders` sets `selectedOrderId` to `orders[0].id` if `selectedOrderId` is null and orders are available. After a cancel mutation succeeds, clear `selectedOrderId` to null — the `useEffect` above will then auto-select the new first order once the query re-fetches and resolves.

**Cancel calling pattern:** Use the callback-based `.mutate()` form (not `mutateAsync` with try/catch) so the `onSuccess` callback can call `setSelectedOrderId(null)`:
```ts
cancelOrder.mutate(cancelOrderId, {
  onSuccess: () => {
    setCancelOrderId(null);
    setSelectedOrderId(null);
  }
});
```

**No mobile master-detail:** Admin is desktop-only for order management. On small screens (< `lg`), the list renders full-width. The detail panel is not shown on mobile — this is acceptable as admin is not used for billing on phones.

### 2. Order History

No layout changes. Direction C polish applied.

- `PageHeader` with `AdminStatsBar` (Total Orders | Revenue — clickable | Avg Order)
- **Toolbar row:** date picker chip + search input + pill filter chips (All / Paid / Cancelled) — all in one horizontal row below the stats bar
- **Table rows:** `F5E6D3` dividers, cream hover, tighter column widths
- **Cancelled rows:** amount shown with `line-through` styling
- `View Details` button replaced with full-row click target (entire `<tr>` is clickable on desktop table). On mobile, the existing card layout (`md:hidden`) keeps its current explicit button replaced by making the entire card `div` clickable (`cursor-pointer` + `onClick`).
- Revenue stat cell shows a "↗ tap for breakdown" hint; clicking reveals a cash/UPI/card breakdown below the stats bar (inline expand, no modal — see `AdminStatsBar` spec)

### 3. Cash Counter

No layout changes. Direction C polish applied.

- `PageHeader` replaces current header
- Existing 2-column layout (form left, summary sidebar right) unchanged
- Card wrappers updated: `border-l-4` accent colour matches counter state (lily-green = open, amber = pending, blue = verified)
- `DenominationCounter` component untouched
- All form logic, modals, and reopen flow untouched

### 4. Analytics

Light-touch polish only.

- `PageHeader` replaces current header (hamburger + title)
- View toggle (Dashboard / Ask Questions) restyled: pill toggle with `coffee-brown` active state, replacing current border-box toggle
- All chart components, `AnalyticsDashboard`, `AskQuestionsView`, and settings modal untouched

### 5. Inventory

Light-touch polish only.

- `PageHeader` replaces current header
- Tab bar restyled: underline-style active tab with `coffee-brown` indicator, replacing current button-style tabs
- Tab content components (`DailyCountTab`, `InventoryItemsTab`, `InventoryCategoriesTab`, `InventoryTransactionsTab`) untouched

### 6. Menu Management

- `PageHeader` with optional action slot used for `+ Add Item` button
- Toolbar: search input + pill category filter chips in one row. Categories are derived dynamically from menu data. When the chip row would overflow (many categories), it scrolls horizontally with `overflow-x-auto` — no "more" dropdown needed.
- Table: consistent row hover, `F5E6D3` dividers
- **Inline availability toggle:** new `<toggle>` switch in the Available column — single click toggles `is_available` via the existing update API, no modal required. Unavailable items shown with muted text and price.
- `MenuItemForm` modal unchanged

---

## UX Improvements

### 1. Order Age Warning (Active Orders)

Order list items change colour based on age:

| Age | Left border | Background tint |
|---|---|---|
| < 30 min | `lily-green` | none |
| 30–59 min | `warning` amber | `rgba(255,152,0,0.04)` |
| ≥ 60 min | `error` red | `rgba(244,67,54,0.04)` |

Age badge in the list row also reflects the state (green / amber pill / red pill with warning icon).

### 2. Inline Availability Toggle (Menu Management)

The Available column in the menu table shows a toggle switch instead of a status dot.

- Uses existing `useMenu` / `useUpdateMenuItem` hook
- Optimistic update: toggle flips immediately, reverts on error with a toast using `sonner` (`import { toast } from 'sonner'`) — consistent with the rest of the admin pages
- No change to `MenuItemForm`

### 3. Empty Detail Panel State (Active Orders)

When no order is selected (initial load before auto-select kicks in, or edge cases):

```
[coffee-brown icon]
Select an order
Click any table on the left to view its details here
```

Centred in the detail panel, `off-white` background.

### 4. Revenue Breakdown Hint (Order History)

The revenue stat cell in `AdminStatsBar` shows a small `↗ tap for breakdown` affordance below the value. Clicking expands an inline row below the stats bar showing:

```
Cash ₹9,200 (50%) | UPI ₹7,840 (43%) | Card ₹1,380 (7%)
```

Uses `paymentBreakdown` data already computed in `OrderHistoryPage`. No API changes.

### 5. Skeleton Loading States (All Pages)

Each page replaces its full-page spinner with a layout-matched shimmer skeleton using Tailwind `animate-pulse`. Skeleton blocks use `bg-neutral-border/50` — this resolves correctly in both light and dark mode via the existing CSS variable.

**Error states are unchanged** — the existing `{error && <div>...}` blocks remain in place after the skeleton conditional. Skeleton is shown only when `isLoading === true`; error state is shown when `error` is truthy; both conditions are independent.

Skeletons mirror the actual page structure:
- **Active Orders:** skeleton list rows (left) + skeleton detail rows (right — `hidden lg:flex` to match the panel's responsive behaviour)
- **Order History:** skeleton stat cells + skeleton table rows
- **Cash Counter:** skeleton card
- **Analytics:** skeleton stat cells + skeleton chart placeholder
- **Inventory:** skeleton tab bar + skeleton category rows
- **Menu Management:** skeleton table rows

### 6. Keyboard Navigation (Active Orders)

Using the existing `useKeyboardShortcuts` hook (plural export from `useKeyboardShortcut.ts`).

Key strings must match `event.key` values (the hook does `toLowerCase()` comparison):

| `event.key` | Action |
|---|---|
| `ArrowUp` | Move selection to previous order in list |
| `ArrowDown` | Move selection to next order in list |
| `b` | Open Generate Bill (`PaymentModal`) for selected order |
| `e` | Open Edit Order (`EditOrderModal`) for selected order |

The `?` shortcut is **not** a new implementation task — `KeyboardShortcutsHelp` manages its own `isOpen` state internally and registers its own `Shift+?` listener. Simply mount `<KeyboardShortcutsHelp />` in `AdminActiveOrdersPage` (it is already self-activating).

**Shortcuts disabled when a modal is open:** pass `enabled: !isAnyModalOpen` to each shortcut config, where `isAnyModalOpen` is derived as:
```ts
const isAnyModalOpen = paymentOrderId !== null || editOrder !== null || cancelOrderId !== null || serveModalData !== null || editModalData !== null
```

**Hook API:** `useKeyboardShortcuts` accepts a `Record<string, ShortcutConfig>` where `ShortcutConfig` is `{ handler: () => void; enabled?: boolean; ctrl?: boolean; shift?: boolean; alt?: boolean; preventDefault?: boolean }`. The key in the record is the `event.key` string. The hook does `shortcuts[event.key.toLowerCase()] || shortcuts[event.key]` lookup, so both `'arrowup'` and `'ArrowUp'` resolve — but use the canonical `event.key` value as the record key to be explicit.

**`useMemo` for shortcuts object:** Wrap the shortcuts config object in `useMemo` with `[selectedOrderId, orders, isAnyModalOpen]` as dependencies. This prevents re-registering all event listeners on every render (the hook's `useEffect` depends on `[shortcuts]`), and ensures `enabled` and `handler` closures capture current state.

```ts
const shortcuts = useMemo(() => ({
  ArrowUp: { handler: () => { /* navigate to previous */ }, enabled: !isAnyModalOpen },
  ArrowDown: { handler: () => { /* navigate to next */ }, enabled: !isAnyModalOpen },
  b: { handler: () => { /* open bill modal */ }, enabled: !isAnyModalOpen && selectedOrderId !== null },
  e: { handler: () => { /* open edit modal */ }, enabled: !isAnyModalOpen && selectedOrderId !== null },
}), [selectedOrderId, orders, isAnyModalOpen]);
useKeyboardShortcuts(shortcuts);
```

### 7. Clickable Rows (Order History)

Entire `<tr>` is wrapped in an `onClick` handler that opens the order detail modal. The explicit "View Details" button is removed — the row click replaces it. Print and Edit buttons remain as inline action buttons.

---

## What Does Not Change

- All API endpoints and backend logic
- `DenominationCounter` component internals
- Payment method icon components (`UpiIcon`, `CashIcon`, `CardIcon`)
- All chart components under `analytics/charts/`
- `AnalyticsDashboard`, `AskQuestionsView`, analytics settings modal
- `MenuItemForm` modal
- All inventory tab content components
- `CartDrawer`, `PaymentModal`, `EditOrderModal`, `PartialServeModal` modals
- `MenuList`, `FloatingCartButton`, `TableGrid`, `KeyboardShortcutsHelp` components
- Dark mode — all new components respect existing dark mode CSS variables

---

## Background Treatment

**Choice: Linen texture — applied to all pages (admin + waiter).**

A new `LinenTexture` component replaces the existing `BackgroundPattern` on waiter pages and is added to all admin pages.

### `LinenTexture` component

`frontend/src/components/LinenTexture.tsx`

- `fixed inset-0 pointer-events-none z-0` overlay
- SVG `<pattern>` with fine crosshatch: horizontal + vertical lines at 4px spacing, 0.5px stroke
- Stroke colour: `var(--color-coffee-light)` (#A0826D)
- Opacity: 0.08 light mode, 0.05 dark mode. Use the existing `useTheme()` hook from `frontend/src/contexts/ThemeContext.tsx` — it returns `{ theme }` typed as `'light' | 'dark'` (never undefined). Derive `isDark = theme === 'dark'` and pass `style={{ opacity: isDark ? 0.05 : 0.08 }}`.
- No other props required

**Mount location:**
- **Admin pages**: mount `<LinenTexture />` once inside `AdminLayout.tsx` (the shared wrapper), so it applies to all 6 admin pages automatically. Do not add it individually to each admin page file.
- **Waiter pages**: add `<LinenTexture />` individually to `TablesPage`, `OrderPage`, and waiter `ActiveOrdersPage` — replacing the existing `<BackgroundPattern />` mount in each file.

**Practical note:** The existing `BackgroundPattern` (coffee beans + cups) is replaced on waiter pages — it remains in the codebase but is no longer mounted.

---

## Colour Palette Addition

**Choice: Warm amber `#C27A2A` added as a new accent token.**

Add to `frontend/src/index.css` following the exact two-part pattern used for existing tokens (`coffee-brown`, `lily-green`, etc.):

```css
/* In @theme {} block — light mode value, registers as Tailwind colour token */
--color-amber: #C27A2A;

/* In .dark {} block — dark mode override */
--color-amber: #D4943F;
```

There is **no** `:root {}` block needed, and **no** `var()` self-reference. The `@theme {}` block defines the CSS custom property with a hardcoded light-mode value (Tailwind v4 then generates `var(--color-amber)` in all utility classes). The `.dark {}` block overrides the same custom property with the dark-mode value at runtime. This is the exact same pattern as `--color-coffee-brown: #6F4E37` in `@theme {}` and `--color-coffee-brown: #B8916A` in `.dark {}`.

**Usage across the app:**

| Context | Token |
|---|---|
| Order age warning 30–59 min — left border + badge | `amber` |
| Cash counter "pending" card `border-l-4` accent | `amber` |
| Parcel badge tint | `amber` tint bg, dark text |
| Waiter order card "parcel" indicator | `amber` tint |

The `amber` token slots into the existing Order Age Warning table:

| Age | Left border | Background tint |
|---|---|---|
| < 30 min | `lily-green` | none |
| 30–59 min | `amber` | `rgba(194,122,42,0.04)` |
| ≥ 60 min | `error` red | `rgba(244,67,54,0.04)` |

---

## Waiter View Design

Three pages — `TablesPage`, `OrderPage`, `ActiveOrdersPage` (waiter) — plus the shared `BottomNav`. Primary usage: mobile + tablet. The design polish is lighter than the admin redesign; functional components (`MenuList`, `FloatingCartButton`, `CartDrawer`, `TableGrid`) are untouched.

### Header Style (all waiter pages)

Keep `bg-gradient-primary` header — it already carries strong brand presence. Add an eyebrow above the title on `TablesPage` and waiter `ActiveOrdersPage`:

```
LILY CAFE              ← eyebrow: lily-green, uppercase, tracking-widest, text-xs, opacity-80
Tables                 ← existing h1, font-heading
```

`OrderPage` header keeps its current back-button layout — no eyebrow (the table number is the contextual title).

### `TablesPage`

- Replace `<BackgroundPattern />` with `<LinenTexture />`
- Add eyebrow line above `<h1>` in the header
- No other layout changes

### `OrderPage`

- Replace `<BackgroundPattern />` with `<LinenTexture />`
- No other changes — the search bar, category chips, and menu list are already well-structured

### `ActiveOrdersPage` (waiter)

Three changes:

1. **Header consistency** — switch from `bg-coffee-brown` to `bg-gradient-primary` (matches TablesPage)
   Add eyebrow `LILY CAFE · ORDERS` above the h1.
   Add `<LinenTexture />`.

2. **Order card restyling:**
   - Background: `bg-off-white` → `bg-cream` (warmer)
   - Left accent: `border-l-4 border-coffee-brown`
   - Remove explicit "View Details" button — entire card is clickable (`cursor-pointer onClick={onViewDetails}`)
   - Add a serve-status strip below the item count: small pill badges showing `{served} served` (lily-green) + `{pending} pending` (amber) counts, derived from `order.order_items`
   - Parcel items: amber badge `Parcel` on the relevant item row inside the details modal
   - **Inline name edit preserved:** The existing inline customer-name edit feature (pencil icon → input + save/cancel buttons) is retained. All interactive elements within the edit flow must call `e.stopPropagation()` on their `onClick`/`onChange` handlers to prevent triggering the card-level `onViewDetails`. Specifically: the pencil edit button, the name input, the save button, and the cancel button all need `e.stopPropagation()`. When `isEditingName` is true, the card's root `onClick` can also be suppressed via a conditional: `onClick={isEditingName ? undefined : onViewDetails}`.

3. **Order details modal restyling:**
   - Modal bg: already `bg-off-white` ✓
   - Item rows: already `bg-cream` ✓ — no change needed
   - Add served/unserved status next to each item: `✓ Served` (lily-green text) or `Pending` (amber text) based on `item.is_served`

### `BottomNav`

Current state: `bg-off-white/95 backdrop-blur-md border-t-2 border-neutral-border/50`. Active tab uses `bg-gradient-primary text-cream` with a cream `h-1` top indicator bar. Inactive tabs use `text-neutral-text-light hover:text-coffee-brown`.

Direction C polish — migrate active tab away from gradient:

- Background: keep existing `bg-off-white/95 backdrop-blur-md` — no change
- **Active tab**: remove `bg-gradient-primary text-cream`; replace with `text-coffee-brown` icon + label and a 2px `coffee-brown` top border (`border-t-2 border-coffee-brown`) replacing the current cream `h-1` indicator. Scale-up on icon stays (`scale-110`).
- Inactive tab: keep `text-neutral-text-light hover:text-coffee-brown hover:bg-cream/60` — no change
- Theme button: keep as-is
- The outer `border-t-2 border-neutral-border/50` on the `<nav>` element stays unchanged

---

## What Does Not Change (Waiter View)

- `MenuList`, `FloatingCartButton`, `CartDrawer` — untouched
- `TableGrid` — untouched
- `KeyboardShortcutsHelp` — untouched
- All routing and navigation logic
- `ThemeToggle` position and behaviour

---

## Files Affected

**New files:**
- `frontend/src/components/PageHeader.tsx`
- `frontend/src/components/AdminStatsBar.tsx`
- `frontend/src/components/LinenTexture.tsx`

**Modified files:**
- `frontend/src/index.css` — add `amber` CSS variable + Tailwind token
- `frontend/src/components/AdminLayout.tsx` — minor
- `frontend/src/components/Sidebar.tsx` — no changes expected
- `frontend/src/components/BottomNav.tsx` — styling polish
- `frontend/src/pages/AdminActiveOrdersPage.tsx` — full rewrite (layout change)
- `frontend/src/pages/OrderHistoryPage.tsx` — header, toolbar, table styling, row click
- `frontend/src/pages/CashCounterPage.tsx` — header, card styling
- `frontend/src/pages/AnalyticsPage.tsx` — header, toggle styling
- `frontend/src/pages/InventoryPage.tsx` — header, tab styling
- `frontend/src/pages/MenuManagementPage.tsx` — header, toolbar, table, availability toggle
- `frontend/src/pages/TablesPage.tsx` — swap BackgroundPattern → LinenTexture, header eyebrow
- `frontend/src/pages/OrderPage.tsx` — swap BackgroundPattern → LinenTexture
- `frontend/src/pages/ActiveOrdersPage.tsx` (waiter) — header, LinenTexture, card restyling, clickable cards
