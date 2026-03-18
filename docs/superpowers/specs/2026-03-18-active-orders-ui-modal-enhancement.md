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

**Left panel (`w-60 flex-shrink-0`)**
- Unchanged list of `OrderRow` components.
- Each row gains two inline icon-buttons below the item/pending badges:
  - **Bill** — terracotta pill (`bg-coffee-brown/10 text-coffee-brown`), `CurrencyInr` icon. Triggers `setPaymentOrderId(order.id)` directly.
  - **Edit** — cream pill (`bg-cream border border-neutral-border text-neutral-text-dark`), `PencilSimple` icon. Triggers `setEditOrder(order)`.
  - **Move** — green pill (`bg-lily-green/10 text-lily-green`), `ArrowsLeftRight` icon. Only shown on the **selected** row. Triggers `setMoveOrderId(order.id)`.
- Buttons are `text-[9px] font-semibold px-1.5 py-0.5 rounded-full` — same scale as the existing age/pending badges.

**Center panel (`flex-1 overflow-hidden flex flex-col`)**
- Header (`px-5 py-4 border-b bg-off-white/80`): table title (Fraunces italic) + order number + age badge + dine-in/parcel chip. Unchanged.
- Items area (`flex-1 overflow-y-auto`): items table unchanged.

**Right sidebar (`w-56 flex-shrink-0 border-l border-neutral-border bg-off-white/60 flex flex-col`)**
- **Summary card** — terracotta-tinted tile with total amount (Fraunces italic, large) + two mini stats: served count (green) and pending count (amber).
- **Generate Bill button** — `btn btn-primary w-full` with `CurrencyInr` icon.
- **Edit Order button** — `btn btn-secondary w-full` with `PencilSimple` icon.
- **Move Table button** — `btn w-full border border-lily-green/30 text-lily-green bg-lily-green/5` with `ArrowsLeftRight` icon.
- **Divider**, then **cancel order** text link (`text-xs text-neutral-text-muted underline hover:text-error`).
- All sidebar buttons call the same handlers as the existing footer buttons in the old `DetailPanel`.

**Mobile (`lg:` breakpoint)**
- Sidebar hidden below `lg`. Below `lg`, the old footer (Generate Bill + Edit) remains in the center panel.
- Row quick-actions always visible on all screen sizes.

### Move Table modal (new — `MoveTableModal.tsx`)
A focused `max-w-xs` modal reusing the table-number select and `useUpdateOrder` mutation from `EditOrderModal`. No item editing, no customer name — just the table selector.

- Header: green gradient (`#3d7a50 → #2e6040`), `ArrowsLeftRight` phosphor icon, title "Move Table".
- Body: single `<select>` for table number, warning note if same table selected.
- Footer: Cancel + "Move to Table N" button (green).

---

## 2. Modal Visual Overhaul

### Shared shell pattern

All modals get this structure:

```
┌─────────────────────────────────────────┐
│  [gradient header]                       │
│  ○ icon   Title (Fraunces italic)        │
│           subtitle / meta               │  × close
├─────────────────────────────────────────┤
│  body — bg-off-white, p-5/p-6           │
│  (content unchanged)                    │
├─────────────────────────────────────────┤
│  footer — border-t, actions             │
└─────────────────────────────────────────┘
```

**Header gradient by intent:**

| Intent | Gradient | Used by |
|--------|----------|---------|
| Terracotta | `#c04e30 → #b5462a` | ConfirmDialog (danger), PaymentModal, EditOrderModal, DailyRevenueModal, EditPaymentsModal |
| Green | `#3d7a50 → #2e6040` | PartialServeModal, MoveTableModal |
| Amber | `#C27A2A → #a06020` | ConfirmDialog (warning), EditServedQuantityModal, AnalyticsSettingsModal |
| Info blue | `#2196F3 → #1565C0` | ConfirmDialog (info), TemplateImportModal |

**Header anatomy:**
- `padding: 1rem 1.25rem`, `display: flex`, `align-items: center`, `gap: 0.75rem`
- Icon container: `w-9 h-9 rounded-full bg-white/20 flex items-center justify-center` — Phosphor duotone icon, `size={20}`, `color="white"`
- Title: `text-white font-heading italic text-base font-bold`
- Subtitle: `text-white/70 text-xs` (order number, item name, date, etc.)
- Close `×`: `ml-auto text-white/60 hover:text-white text-xl leading-none`

**Body:**
- Background: `bg-off-white` (was `bg-white` in most modals)
- No other structural changes — content layout preserved exactly.

**Specific modal updates:**

### ConfirmDialog
- Replace `bg-white dark:bg-neutral-800` with `bg-off-white border border-neutral-border`
- Replace hardcoded Warning icon + plain title row with the gradient header shell
- Variant → gradient mapping: `danger` → terracotta, `warning` → amber, `info` → info blue
- Cancel button: `btn btn-secondary` (was plain border)
- Confirm button: variant-coloured, unchanged logic

### PartialServeModal + EditServedQuantityModal
- Replace `bg-white` modal shell with `bg-off-white border border-neutral-border`
- Add green (Serve) / amber (Edit) gradient header with checkmark / pencil icon
- Slider fill colour: `#c04e30` (was hardcoded `rgb(139, 98, 72)` old coffee-brown)
- Status info box: `bg-cream border border-neutral-border` (was `bg-neutral-background`)
- Quick-select buttons (None/Half/All): `bg-cream border border-neutral-border hover:bg-neutral-border/50` (was plain grey)

### PaymentModal
- Header: terracotta gradient (replaces the plain `p-8 bg-off-white` left column header)
- `bg-green-50 border-green-200` remaining tile → `bg-lily-green/10 border-lily-green/30 text-lily-green`
- `bg-orange-50 border-orange-200` remaining tile → `bg-amber/10 border-amber/30 text-amber`
- Error box: `bg-error/10 border border-error/30` (already exists, keep)

### DailyRevenueModal
- Header: terracotta gradient (replaces `bg-off-white border-b`)
- Payment method icon circles: replace `bg-green-100 text-green-700`, `bg-blue-100 text-blue-700`, `bg-purple-100 text-purple-700` with:
  - Cash → `bg-lily-green/10 text-lily-green`
  - UPI → `bg-info/10 text-info`
  - Card → `bg-amber/10 text-amber`

### EditOrderModal
- Header: terracotta gradient header (replaces plain `border-b` header)
- Form inputs: `input-field` utility class (was custom inline styles)

### EditPaymentsModal, AnalyticsSettingsModal, TemplateImportModal
- Add gradient header matching intent (terracotta / amber / info)
- Replace `bg-white` modal body with `bg-off-white`

---

## 3. Files Changed

| File | Change |
|------|--------|
| `src/pages/AdminActiveOrdersPage.tsx` | Add right sidebar component, row quick-action buttons, `MoveTableModal` state |
| `src/components/MoveTableModal.tsx` | **New file** — focused move-table modal |
| `src/components/ConfirmDialog.tsx` | Gradient header, variant-to-gradient mapping, style tokens |
| `src/components/PartialServeModal.tsx` | Green gradient header, slider colour, style tokens |
| `src/components/EditServedQuantityModal.tsx` | Amber gradient header, slider colour, style tokens |
| `src/components/PaymentModal.tsx` | Terracotta gradient header, remaining/green tile palette fix |
| `src/components/DailyRevenueModal.tsx` | Terracotta gradient header, payment icon circle palette fix |
| `src/components/EditOrderModal.tsx` | Terracotta gradient header |
| `src/components/EditPaymentsModal.tsx` | Appropriate gradient header |
| `src/components/analytics/AnalyticsSettingsModal.tsx` | Amber gradient header |
| `src/components/inventory/TemplateImportModal.tsx` | Info gradient header |

---

## 4. Out of Scope

- No changes to modal business logic or data fetching
- No changes to `index.css` — all styling uses existing design tokens
- No changes to waiter-facing pages
- No keyboard shortcut changes (existing `b` and `e` shortcuts preserved)
