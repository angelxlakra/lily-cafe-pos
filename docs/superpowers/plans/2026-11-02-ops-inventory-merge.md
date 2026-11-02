# Inventory in one place: move the old Inventory page into ops

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Everything the old `/admin/inventory` page does lives under `/admin/ops`, in the ops look. The old page is gone, and its links redirect.

**Architecture:** Frontend only. The backend endpoints stay as they are. Each old screen keeps its logic, and its markup moves to the ops classes in `frontend/src/ops/ops.css`. Where an old component is only restyled, it moves into `frontend/src/ops/` (git mv first, then the restyle) rather than being copied, so nothing is left duplicated. Once nothing imports `InventoryPage` and the old tab components, they are deleted.

**Tech Stack:** React + TypeScript, react-router, TanStack Query, plain CSS (`ops.css`), node `--test` for unit tests.

**Spec:** The owner's request of 2026-11-02 (below), plus `docs/INVENTORY_PLAN.md` § "Ops redesign".

> Keep inventory in one place. Managers use the daily count and check low stock, so they need it too. The ops page is the good one; the old page has uneven tab widths and the count still opens the old look.

## Global Constraints

- Branch `claude/ops-inventory-merge`, cut from `claude/ops-redesign`. Open the PR against `pre-release`, stacked on #76.
- Who sees what doesn't change:
  - **Admin (manager):** Inventory, Count, Daily sheet, Order, Stock log.
  - **Owner:** all of those, plus Setup (items, categories, count order, import) and Recipes.
  - The API already enforces this; the UI hides what a role can't use.
- **The count's behaviour stays exactly as it is.** That means one answer per row, the box placeholder showing the system quantity, Out / Have it buttons for yes/no items, and folding finished categories. The draft kept on the phone, the review sheet before save, the big-difference second look, and tonight's order after save also stay. Only the look changes. (Staff tested this; see memory "stock count simplicity".)
- Draft storage keys in `utils/countDraft.ts` are unchanged, so a count in progress on a phone survives the update.
- **Old URLs redirect:**
  - `/admin/inventory` goes to `/admin/ops/inventory`;
  - `/admin/inventory?tab=X` goes to that tab's ops page;
  - `/admin/inventory/count` goes to `/admin/ops/count`.
- The sidebar has one "Inventory" entry, pointing to `/admin/ops/inventory`. The "Ops" entry goes.
- The ops look: the `--ops-*` tokens, 16px base text, sentence-case labels, 44px touch targets, phone layout at ≤ 640px, and dark mode via `.dark .ops`.
- `uv run` for any Python; never commit `.claude/launch.json`.

## Pages after this change

| Ops page | Route | Who | Replaces |
|---|---|---|---|
| Inventory | `/admin/ops/inventory` | all | Items tab list (already built) |
| Count | `/admin/ops/count` (full screen, outside `OpsLayout`) | all | `/admin/inventory/count`, Daily count tab |
| Daily sheet | `/admin/ops/sheet` | all | Purchases tab (already built) |
| Order | `/admin/ops/order` | all | Order tab |
| Stock log | `/admin/ops/log` | all | Stock log tab |
| Setup | `/admin/ops/setup` | owner | Items tab grid + add form, Categories tab, count order, import |
| Recipes | `/admin/ops/recipes` | owner | (already built) |

Ops bar order: Inventory · Count · Daily sheet · Order · Stock log · Setup · Recipes. On a phone, the bar scrolls sideways (it already does).

## Calls made by the developer (check these)

1. **Daily count tab → Inventory page side panel.** Today's status (not started / in progress on this phone / done), the start-or-continue button, and the recent counts already sit on the ops Inventory page. "Continue" is added there when a draft exists; there is no separate count landing page.
2. **The single-item edit form is dropped.** The setup grid edits every field and deactivates items. A small "Add item" form stays, because the grid can't create items.
3. **Categories and count order go on the Setup page** as sections, not separate pages.
4. **Stock log keeps usage and one-off correction.** It drops "record a delivery", because the Daily sheet does that and two ways to enter a purchase is what this change is removing.

## Review Focus

1. **A count in progress when the update ships:** the draft from the old page loads on `/admin/ops/count`, with no entries lost.
2. **An admin opens an owner URL** (`/admin/ops/setup`, or an old `?tab=items` link): they get the same redirect as for Recipes today (`ProtectedRoute` sends them to `/admin/active-orders`), not a blank page.
3. **The count on a phone at 375px:** rows, the pinned bar and the review sheet fit without sideways scroll, and the thumb-reach actions stay at the bottom.
4. **Dark mode on the count and Setup pages:** no Tailwind light colours leak through from leftover classes.
5. **Old bookmarks with unknown `?tab=` values** go to the ops Inventory page.

---

### Task 1: Count in the ops look

**Files:**
- Move and restyle:
  - `src/pages/InventoryCountPage.tsx` → `src/ops/CountPage.tsx`;
  - `src/components/inventory/CountRow.tsx` → `src/ops/CountRow.tsx`;
  - `src/components/inventory/CountReviewSheet.tsx` → `src/ops/CountReviewSheet.tsx`.
- Modify:
  - `src/main.tsx` (the `/admin/ops/count` route, full screen like today's count route);
  - `src/ops/ops.css` (a `.ops-count` block);
  - `src/ops/OpsInventoryPage.tsx` (start/continue links to `/admin/ops/count`; a "Continue tonight's count" label when `loadCountDraft()` returns entries).
- Test: `tests/countDraft.test.ts`, if `utils/countDraft.ts` has no test yet. The check: an entry saved under today's key loads back unchanged.

- [ ] `git mv` the three files, update the imports, and check the build passes before restyling.
- [ ] Replace the Tailwind classes with `.ops-count` classes:
  - a pinned top bar (exit · category · progress);
  - rows with the name left and the control right;
  - the number box at 16px+ so iOS doesn't zoom;
  - the Out / Have it pair as two 44px buttons;
  - the review sheet as a bottom sheet in `--ops-bar`.
  Keep every handler, effect and the draft calls untouched.
- [ ] After save: "Send tonight's order" goes to `/admin/ops/order`, "Done" goes to `/admin/ops/inventory`. Exit goes to `/admin/ops/inventory`.
- [ ] Check in the browser at 375px and desktop, in light and dark mode. A full count plus save must end in the same `/counts` POST body as before (compare in network requests).
- [ ] Commit `feat(ops): tonight's count in the ops look`.

### Task 2: Order and Stock log pages

**Files:**
- Move and restyle:
  - `src/components/inventory/OrderTab.tsx` → `src/ops/OrderPage.tsx`;
  - `src/components/inventory/InventoryTransactionsTab.tsx` → `src/ops/StockLogPage.tsx`.
- Modify: `src/main.tsx` routes, `src/ops/OpsLayout.tsx` bar links, `src/ops/ops.css`.

- [ ] Move them, wire up the routes and links, and build.
- [ ] Order: one card per vendor (an `.ops-approve .chg`-style box). The message sits in a monospace `<pre>`, with the Copy button at its top right. Unassigned comes last.
- [ ] Stock log: an `.ops-t` table, newest first: date · item · change · type · note. Remove the delivery form, keep the usage and correction forms (call 4).
- [ ] Browser check: copy works, and a correction appears at the top of the log.
- [ ] Commit `feat(ops): order and stock log pages`.

### Task 3: Setup page (owner)

**Files:**
- Create: `src/ops/SetupPage.tsx`, with sections Items (the grid), Add item, Categories, Count order and Import.
- Move and restyle:
  - `InventorySetupGrid.tsx`, `CountOrderEditor.tsx` and `TemplateImportModal.tsx` → `src/ops/`;
  - the category list and form out of `InventoryCategoriesTab.tsx`;
  - the add-item form out of `InventoryItemsTab.tsx`'s `ItemFormModal`, create-only (call 2).
- Modify: `src/main.tsx` (owner-only route), `OpsLayout.tsx`, and `OpsInventoryPage.tsx` ("Edit all" → `/admin/ops/setup`).

- [ ] Move the files and build.
- [ ] The grid keeps its full-screen mode and column locks. Restyle its header, cells and focus ring with the `--ops-*` tokens: the typed-blue cells match the recipe page.
- [ ] Delete `ItemRow`, the edit path of `ItemFormModal`, and the `?edit=all` handling (no longer needed).
- [ ] Browser check: add an item, edit it in the grid, reorder a category, and deactivate the item.
- [ ] Commit `feat(ops): setup page for items, categories and count order`.

### Task 4: Retire the old page

**Files:**
- Delete:
  - `src/pages/InventoryPage.tsx`;
  - `src/components/inventory/DailyCountTab.tsx`, `InventoryItemsTab.tsx`, `InventoryCategoriesTab.tsx` and `PurchaseSheetTab.tsx`;
  - anything else in `src/components/inventory/` that nothing imports.
- Modify:
  - `src/main.tsx`: redirects. `/admin/inventory/count` goes to `/admin/ops/count`. A small `LegacyInventoryRedirect` reads `?tab=`, mapping `daily-count`→inventory, `order`→order, `purchases`→sheet, `items`/`categories`→setup, `transactions`→log, anything else→inventory.
  - `src/components/Sidebar.tsx`: one "Inventory" entry pointing to `/admin/ops/inventory`, with the Package icon. Drop the "Ops" entry.
  - `docs/INVENTORY_PLAN.md`: "What shipped" and "Next up".
- Test: `tests/legacyInventoryRedirect.test.ts`, if the `?tab=` mapping is a plain function. It asserts each mapping above, plus an unknown tab going to inventory.

- [ ] Add the redirects and the test, then delete the files. `grep -rn "admin/inventory\|components/inventory" src` must show only the redirect.
- [ ] Check that `/admin/ops/setup`, visited as an admin, is caught by `ProtectedRoute requiredRole="owner"` (Review Focus 2).
- [ ] Run `npm run build` and `npm test`, then check in the browser as admin and as owner.
- [ ] Commit `feat(ops): one inventory; old page redirects`.

### Task 5: Final check

- [ ] Walk through it on demo data, as admin and then owner, on a phone and on desktop:
  - count → order → daily sheet → stock log;
  - setup → recipe.
- [ ] Open the PR against `pre-release`, noting it builds on #76.
