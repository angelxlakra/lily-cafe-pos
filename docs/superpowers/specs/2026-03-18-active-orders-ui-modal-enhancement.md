# Active Orders UI + Modal Enhancement — Design Spec

**Date:** 2026-03-18
**Status:** Approved for implementation

---

## Overview

Three related enhancements to the admin dashboard:

1. **Active Orders layout** — replace the too-wide single detail panel with a three-column layout plus inline row quick-actions.
2. **Table row quick actions** — Bill, Edit, and Move shortcuts directly on each table row.
3. **Modal visual overhaul** — apply the Terracotta & Sand palette with intent-coded gradient headers to all modals.

---

## 1. Active Orders Layout (B + C combined)

### Current state
The detail panel fills the full remaining width after the left list column, leaving a vast empty space with only a narrow content block.

### New layout — three columns

```
┌──────────────┬────────────────────────────┬────────────┐
│  Table list  │     Items table (flex-1)   │  Sidebar   │
│  w-60        │                            │  w-56      │
│  (with row   │  header: table title +     │  summary   │
│   actions)   │  order meta                │  bill btn  │
│              │  scrollable items          │  edit btn  │
│              │                            │  move btn  │
│              │                            │  cancel    │
└──────────────┴────────────────────────────┴────────────┘
```

### Left panel (`w-60 flex-shrink-0 border-r border-neutral-border overflow-y-auto`)

Each `OrderRow` gains two (or three) pill buttons in a `flex gap-1.5 mt-1.5 flex-wrap` row below the existing age/pending badges:

- **Bill** — `text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-coffee-brown/10 text-coffee-brown` with `CurrencyInr` phosphor icon (`size={10}`). Calls `setPaymentOrderId(order.id)`.
- **Edit** — `text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-cream border border-neutral-border text-neutral-text-dark` with `PencilSimple` icon (`size={10}`). Calls `setEditOrder(order)`.
- **Move** — `text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-lily-green/10 text-lily-green` with `ArrowsLeftRight` icon (`size={10}`). Only rendered when `isSelected === true`. Calls `setMoveOrderId(order.id)`.

**Nested button issue:** The existing `OrderRow` is a `<button>` element. Placing interactive buttons inside it creates invalid HTML. Each pill button must call `e.stopPropagation()` before its handler so that clicking Bill/Edit/Move does not also fire the row's `setSelectedOrderId` click:

```tsx
<button
  onClick={(e) => { e.stopPropagation(); setPaymentOrderId(order.id); }}
  ...
>Bill</button>
```

`OrderRow` itself remains a `<button>` — do NOT refactor it to a `<div>`.

### Center panel (`flex-1 overflow-hidden flex flex-col`)

- Header (`px-5 py-4 border-b border-neutral-border bg-off-white/80`): table title (Fraunces italic) + order number + age badge + dine-in/parcel chip. **Unchanged.**
- Items area (`flex-1 overflow-y-auto px-4 py-3 space-y-4`): items table. **Unchanged.**
- **The existing `DetailPanel` footer (Generate Bill + Edit + cancel order link) is removed entirely.** These actions move to the right sidebar and the row pills. This applies at all screen sizes.

### Right sidebar (`hidden lg:flex flex-col w-56 flex-shrink-0 border-l border-neutral-border bg-off-white/60`)

Shown only on `lg` and above. Contains:

**Summary card:**
```
bg-coffee-brown/10 border border-coffee-light/30 rounded-xl p-4 mx-4 mt-4
```
- Label: `text-[10px] font-bold uppercase tracking-widest text-neutral-text-muted mb-1` — "Total"
- Amount: `font-heading italic text-2xl text-coffee-dark` — e.g. `₹420`
- Mini stats row (`flex gap-2 mt-2`):
  - Served: `text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-lily-green/10 text-lily-green`
  - Pending: `text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-amber/10 text-amber`

**Action buttons** (`flex flex-col gap-2 px-4 mt-4`):
- Generate Bill: `btn btn-primary w-full text-sm flex items-center justify-center gap-1.5` with `CurrencyInr` icon
- Edit Order: `btn btn-secondary w-full text-sm flex items-center justify-center gap-1.5` with `PencilSimple` icon
- Move Table: `w-full text-sm font-semibold py-2 px-3 rounded-lg border border-lily-green/30 text-lily-green bg-lily-green/5 hover:bg-lily-green/10 transition-colors flex items-center justify-center gap-1.5` with `ArrowsLeftRight` icon

**Divider:** `border-t border-neutral-border mx-4 mt-4`

**Cancel link:** `text-center mt-2 px-4` → `<button className="text-xs text-neutral-text-muted underline hover:text-error transition-colors">cancel order</button>`

All sidebar buttons call the same handlers as the removed `DetailPanel` footer:
- Generate Bill → `setPaymentOrderId(selectedOrder.id)`
- Edit Order → `setEditOrder(selectedOrder)`
- Move Table → `setMoveOrderId(selectedOrder.id)`
- cancel order → `setCancelOrderId(selectedOrder.id)`

### Mobile behaviour

Below `lg`: the right sidebar is `hidden`. The center panel footer is gone. **Row pill buttons (Bill, Edit, Move-on-selected) are the only action path on mobile.** No fallback footer is needed — the row pills are always visible at all breakpoints.

### New state variable in `AdminActiveOrdersPage`

Add alongside the existing modal state:

```tsx
const [moveOrderId, setMoveOrderId] = useState<number | null>(null);
```

Add to the `isAnyModalOpen` guard:

```tsx
const isAnyModalOpen =
  paymentOrderId !== null ||
  editOrder !== null ||
  cancelOrderId !== null ||
  serveModalData !== null ||
  editModalData !== null ||
  moveOrderId !== null;  // ← add this
```

Render the modal at the bottom of the JSX alongside the other modals:
```tsx
{moveOrderId && (
  <MoveTableModal
    order={orders.find(o => o.id === moveOrderId)!}
    onClose={() => setMoveOrderId(null)}
  />
)}
```

---

## 2. MoveTableModal (new file: `src/components/MoveTableModal.tsx`)

A focused `max-w-xs` modal for moving an order to a different table. Reuses `useUpdateOrder` and `useAppConfig` from `EditOrderModal`.

**Props:**
```tsx
interface MoveTableModalProps {
  order: Order;
  onClose: () => void;
}
```

**Structure:** Standard three-zone shell (see Section 3 shell pattern).

- **Header:** Green gradient (`#3d7a50 → #2e6040`), `ArrowsLeftRight` phosphor icon (duotone, size 20, white), title "Move Table" (Fraunces italic), subtitle "Table {order.table_number} · {order.order_number}".
- **Body (`bg-off-white p-5`):**
  - `<select>` for table number — lists all tables 1–`max_tables` from `useAppConfig`. **All tables are selectable including the current one.**
  - When the selected table equals `order.table_number`, show a muted warning paragraph directly below the select: `<p className="text-xs text-neutral-text-muted mt-1.5">Already on Table {order.table_number} — select a different table to move.</p>`
- **Footer (`border-t border-neutral-border p-4 flex gap-2 bg-off-white`):**
  - Cancel: `btn btn-secondary flex-1` — calls `onClose()`
  - Move button: `btn flex-1 bg-lily-green text-white hover:bg-lily-green-light disabled:opacity-50` — label "Move to Table {selectedTable}". **Disabled when selected table equals `order.table_number`.** On click: calls `updateOrder.mutateAsync` with the full payload — `items` is **required** by `OrderItemsUpdateRequest` so pass the existing items alongside `table_number`:
    ```tsx
    updateOrder.mutateAsync({
      id: order.id,
      data: {
        items: order.order_items.map(i => ({
          menu_item_id: i.menu_item_id,
          quantity: i.quantity,
          is_parcel: i.is_parcel,
        })),
        table_number: selectedTable,
      },
    })
    ```
    On success: show success toast, call `onClose()`.

---

## 3. Modal Visual Overhaul

### Shared shell pattern

All modals are restructured into three zones:

```
┌─────────────────────────────────────────┐
│  [gradient header]                       │
│  ○ icon   Title (Fraunces italic)        │  × close
│           subtitle / meta               │
├─────────────────────────────────────────┤
│  body — bg-off-white, p-5 or p-6        │
├─────────────────────────────────────────┤
│  footer — border-t border-neutral-border│
└─────────────────────────────────────────┘
```

**Note for `PartialServeModal` and `EditServedQuantityModal`:** Both modals currently render everything inside a flat `<div className="flex flex-col gap-6">` — there is no header/body/footer separation. These two modals require a structural DOM refactor (add header div, wrap existing content in body div, add footer div) in addition to the class changes described below. The existing content (status box, slider, quick-select buttons) moves into the body zone unchanged.

### Header anatomy (all modals)

```tsx
<div
  style={{ background: 'linear-gradient(135deg, #START, #END)' }}
  className="flex items-center gap-3 px-5 py-4"
>
  <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
    <PhosphorIcon size={20} weight="duotone" color="white" />
  </div>
  <div className="flex-1 min-w-0">
    <h2 className="text-white font-heading italic text-base font-bold leading-tight">
      {title}
    </h2>
    <p className="text-white/70 text-xs mt-0.5">{subtitle}</p>
  </div>
  <button
    onClick={onClose}
    aria-label="Close"
    className="text-white/60 hover:text-white text-xl leading-none ml-auto flex-shrink-0"
  >
    &times;
  </button>
</div>
```

**All close buttons across all modals use `aria-label="Close"`.**

### Intent → gradient mapping

| Intent | Gradient start | Gradient end | Used by |
|--------|---------------|--------------|---------|
| Terracotta | `#c04e30` | `#b5462a` | ConfirmDialog (danger), PaymentModal, EditOrderModal, DailyRevenueModal, EditPaymentsModal |
| Green | `#3d7a50` | `#2e6040` | PartialServeModal, MoveTableModal |
| Amber | `#C27A2A` | `#a06020` | ConfirmDialog (warning), EditServedQuantityModal, AnalyticsSettingsModal |
| Info blue | `#2196F3` | `#1565C0` | ConfirmDialog (info), TemplateImportModal |

### ConfirmDialog

- Replace `bg-white dark:bg-neutral-800` modal shell with `bg-off-white border border-neutral-border rounded-2xl shadow-2xl`
- Replace the existing `flex items-start gap-4 mb-4` header row with the gradient header shell above. Gradient determined by `variant`:
  - `danger` → terracotta, icon: `Warning` duotone
  - `warning` → amber, icon: `Warning` duotone
  - `info` → info blue, icon: `Info` duotone (from `@phosphor-icons/react`)
- Remove the standalone `Warning` icon + separate title div — both move into the header
- Body: `px-5 py-4` wrapping the `<p>` message (remove the `ml-11` offset — no longer needed)
- Footer: `px-5 pb-5 flex gap-3 justify-end`
  - Cancel: `btn btn-secondary`
  - Confirm: class stays as is (`${styles.button} text-white rounded-lg ...`)

### PartialServeModal

**Structural refactor required** (flat → three-zone). Current outer div is `max-w-md bg-white rounded-2xl shadow-2xl p-6`. Replace with:
- Outer: `max-w-md bg-off-white rounded-2xl shadow-2xl border border-neutral-border overflow-hidden`
- Zone 1: green gradient header — icon: `CheckCircle` duotone, title: "Serve Items", subtitle: `item.menu_item_name`
- Zone 2 body (`p-5 flex flex-col gap-5`): existing status box + slider + quick-select buttons
  - Status box: `bg-cream border border-neutral-border rounded-xl p-4` (was `bg-neutral-background`)
  - Quick-select buttons: `bg-cream border border-neutral-border hover:bg-neutral-border/50` (was `bg-neutral-background`)
  - Slider fill: `#c04e30` (was `rgb(139, 98, 72)`)
- Zone 3 footer (`border-t border-neutral-border p-4 flex gap-3`): existing Cancel + Serve buttons, unchanged logic

### EditServedQuantityModal

**Structural refactor required** (same as PartialServeModal above).
- Header: amber gradient, icon: `PencilSimple` duotone, title: "Edit Served Quantity", subtitle: `item.menu_item_name`
- Body, footer, style token changes: identical to PartialServeModal above

### PaymentModal

This modal uses a two-column layout (`lg:flex-row`). The gradient header **spans the full width of the modal** (above both columns), replacing the inline `<h2>` that was inside the left column.

Changes:
- Add a full-width terracotta gradient header **outside and above** the `lg:flex-row` columns div. Header title: "Payment for Table {order?.table_number}". Subtitle: order number if available.
- **Remove** the existing standalone close `<button>` from the right column (lines 239–246) — it is replaced by the `×` in the gradient header.
- The existing left column `<h2>` ("Payment for Table {order?.table_number}") is removed — superseded by the header.
- `bg-green-50 border-green-200 text-green-*` remaining-amount tile → `bg-lily-green/10 border border-lily-green/30` with `text-lily-green` for label/value
- `bg-orange-50 border-orange-200 text-orange-*` → `bg-amber/10 border border-amber/30 text-amber`
- Error box `bg-red-50 border-red-200 text-red-700` → `bg-error/10 border border-error/30 text-error`

### DailyRevenueModal

- Replace `bg-off-white p-6 border-b flex items-center justify-between` header with terracotta gradient header. Title: "Revenue Breakdown". Subtitle: formatted date string.
- Remove the existing standalone close `<button>` from the old header.
- Payment icon circles:
  - Cash: `bg-lily-green/10 text-lily-green` (was `bg-green-100 text-green-700`)
  - UPI: `bg-info/10 text-info` (was `bg-blue-100 text-blue-700`)
  - Card: `bg-amber/10 text-amber` (was `bg-purple-100 text-purple-700`)
- Total revenue tile: `bg-coffee-brown/10 border border-coffee-light/30` (was `bg-coffee-light/10 border-coffee-light`)

### EditOrderModal

- Replace `flex items-center justify-between p-6 border-b` header div with terracotta gradient header. Title: "Edit Order". Subtitle: `#{order.order_number} · Modify items, table, or customer`.
- Remove existing close `<button>` from the old header.

### EditPaymentsModal

- Add terracotta gradient header at the top of the modal. Title: "Edit Payments". Subtitle: `Table {order.table_number} · {order.order_number}`.
- Replace `bg-white` modal shell with `bg-off-white border border-neutral-border`.

### AnalyticsSettingsModal

- Add amber gradient header. Title: "Chart Settings". Subtitle: "Show or hide dashboard charts".
- Replace the inline `style={{ backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff' }}` on the modal shell with `className="... bg-off-white"` — remove only this `style` prop.
- Replace the chart item inline `style={{ backgroundColor: theme === 'dark' ? 'rgba(55, 65, 81, 0.5)' : '#f9fafb' }}` with `className="... bg-cream"`. The `borderColor` inline style for selected charts can remain or be replaced with a `border-coffee-brown` conditional class.
- **Leave `useTheme` and `theme` in place.** The file uses `theme` in six additional inline `style` props for text colours on headings and body text — these are not covered by this spec and must not be removed.

### TemplateImportModal

- Add info blue gradient header. Title: "Import Template". Subtitle: appropriate context from the existing header content.
- Replace `bg-white` modal shell with `bg-off-white border border-neutral-border`.

---

## 4. Files Changed

| File | Change type | Notes |
|------|------------|-------|
| `src/pages/AdminActiveOrdersPage.tsx` | Modify | Add right sidebar, row pill buttons, `moveOrderId` state, `isAnyModalOpen` update, `MoveTableModal` render |
| `src/components/MoveTableModal.tsx` | **New file** | Focused move-table modal |
| `src/components/ConfirmDialog.tsx` | Modify | Gradient header, variant mapping, structural cleanup |
| `src/components/PartialServeModal.tsx` | Modify | **Structural refactor** + green header + style tokens |
| `src/components/EditServedQuantityModal.tsx` | Modify | **Structural refactor** + amber header + style tokens |
| `src/components/PaymentModal.tsx` | Modify | Full-width gradient header, remove right-col close btn, palette fixes |
| `src/components/DailyRevenueModal.tsx` | Modify | Gradient header + payment icon palette fix |
| `src/components/EditOrderModal.tsx` | Modify | Gradient header |
| `src/components/EditPaymentsModal.tsx` | Modify | Gradient header + shell colour |
| `src/components/analytics/AnalyticsSettingsModal.tsx` | Modify | Gradient header + replace inline `style` backgroundColor with Tailwind classes |
| `src/components/inventory/TemplateImportModal.tsx` | Modify | Gradient header + shell colour |

---

## 5. Out of Scope

- No changes to modal business logic or data fetching
- No changes to `index.css` — all styling uses existing design tokens
- No changes to waiter-facing pages
- No keyboard shortcut changes (existing `b` and `e` shortcuts preserved)
- No changes to `OrderRow` element type — it stays a `<button>`
