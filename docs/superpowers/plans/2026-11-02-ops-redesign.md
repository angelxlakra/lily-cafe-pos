# Ops Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Four new owner/manager pages (recipes list, recipe page, daily sheet with price approval, inventory) plus the backend for brand, price approval and kitchen-made items (sub-recipes).

**Architecture:** Extend the existing FastAPI inventory/costing code. Pricing stays derived from the purchase log, but only from approved rows. Made items reuse `dish_costings`, and costing recurses into them. The frontend gets a self-contained `src/ops/` area with its own layout and CSS, on the existing API client and React Query.

**Tech Stack:** FastAPI + SQLAlchemy + SQLite (`uv run pytest`), React 18 + TS + React Query + react-router 6, Vite, Tailwind 4 (ops pages use a scoped CSS file instead).

**Spec:** `docs/INVENTORY_PLAN.md`, section "Ops redesign (2026-11-02)". Mockups are in `docs/ops-redesign-mockups/`, and the look is copied from them.

## Global Constraints

- Python is always run through uv: `cd backend && uv run pytest tests/...`. Frontend tests: `cd frontend && npm test` (needs Node ≥ 22: `nvm use 22`). Build: `npm run build`.
- New columns are added only through `_INVENTORY_ADDED_COLUMNS` / ensure-functions in `backend/app/db/session.py` (idempotent, run on startup). There's no Alembic.
- Money is Decimal, rounded half-up to 0.01 (`costing_utils.money`). Prices are per the item's own unit (`inventory_items.unit`).
- Costing endpoints are owner-only (`_OWNER`). Purchases are staff (`_STAFF`). The sheet's other days are owner-only (existing 403).
- The ops pages have their own look: a plain spreadsheet style with light and dark themes. They must work at 375 px with no horizontal page scroll (tables scroll inside their own wrapper) and touch targets ≥ 44 px on phone.
- Copy is sentence case, with no "Title Case" buttons.
- PRs target `pre-release`. Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Don't modify `.claude/launch.json`.

## Review Focus

1. **Two pending purchases of one item** approved out of order: the price is the approved row with the highest id. Test in Task 1.
2. **A made item whose recipe has a gap** (salt unpriced): every dish using it shows as incomplete ("≥"), never as fully costed. Test in Task 2.
3. **A recipe cycle through two made items** (A uses B, B uses A): the save is refused with the chain named, and costing never recurses forever. Test in Task 2.
4. **An admin edits a same-day purchase's total** after an owner approved it: it goes back to pending. Test in Task 1.
5. **A menu item deleted while it has a recipe**, or a made item retired: the recipes list and the Menu chip list don't 500. Test in Task 3.

---

### Task 1: Brand and price approval (backend)

**Files:**
- Modify: `backend/app/models/inventory_models.py` (InventoryItem.brand, InventoryTransaction.price_status/price_reviewed_at)
- Modify: `backend/app/db/session.py` (`_INVENTORY_ADDED_COLUMNS`)
- Modify: `backend/app/utils/pricing.py`
- Modify: `backend/app/schemas/inventory*.py` (brand on item in/out/update and on the bulk grid patch)
- Modify: `backend/app/api/v1/endpoints/inventory.py` (record_purchase, patch purchase, `_purchase_dict`, new review endpoints)
- Test: `backend/tests/test_price_approval.py`

**Interfaces (produces):**
- `inventory_items.brand VARCHAR(100)` nullable, `brand: Optional[str]` on every item schema, and accepted by `PATCH /inventory/items` (grid) and `PATCH /inventory/items/{id}`.
- `inventory_transactions.price_status VARCHAR(10)` (NULL = approved, legacy) and `price_reviewed_at DATETIME`.
- In `pricing.py`: `PRICE_PENDING = "pending"`, `PRICE_APPROVED = "approved"`, `PRICE_REJECTED = "rejected"`. `_priced_purchases` keeps only rows where `price_status IS NULL OR price_status = 'approved'`.
- `_purchase_dict(t)` adds `price_status`.
- `GET /inventory/purchases/pending-prices` (owner) returns `List[PendingPrice]`: `{purchase_id, item_id, item_name, brand, unit, recorded_by, created_at, quantity, total_amount, pack_count, old_price: Decimal|None, new_price: Decimal|None, change: Decimal|None (fraction), is_new_item: bool, ripple: None}`. Task 3 fills in `ripple`.
- `POST /inventory/purchases/{id}/price-review` (owner), body `{action: "approve"|"reject"}`. Sets the status and `price_reviewed_at = now`, and returns `_purchase_dict`. 404 if missing, 400 if it's not a pending purchase.
- `POST /inventory/purchases/price-review/approve-all` (owner) returns `{approved: int}`.

- [ ] **Step 1: Write failing tests** in `test_price_approval.py`, using the fixtures/clients in `tests/conftest.py` and the patterns in `tests/test_purchase_sheet.py`:
  - `test_admin_purchase_is_pending_and_not_the_price`: an admin logs onion 4 kg ₹160 when the typed price is ₹32/kg. Then `price_status == "pending"`, the item's `current_price == 32`, and `price_source == "typed"`.
  - `test_owner_purchase_is_approved`: an owner logs the same purchase. Status is `"approved"` and `current_price == 40`.
  - `test_same_price_purchase_auto_approved`: an admin logs at the current price, so it's `"approved"`.
  - `test_approve_makes_it_the_price` and `test_reject_keeps_stock_but_not_price`: stock rose by 4 in both, the day's total includes ₹160, and the price is 40 vs 32.
  - `test_out_of_order_approval_uses_highest_id`: two pending purchases at ₹40 then ₹44. Approve the second, then the first, and the price is 44.
  - `test_pending_prices_lists_change`: `old_price 32`, `new_price 40`, `change 0.25`, `is_new_item False`. With no prior price, `is_new_item True`.
  - `test_admin_cannot_review` returns 403.
  - `test_edit_total_resets_to_pending`: an owner approves, then an admin patches the total, and it's `"pending"` again.
  - `test_brand_round_trips`: set via PATCH, read back on GET items, and also via the grid's bulk PATCH.
- [ ] **Step 2: Run them and check they fail:** `cd backend && uv run pytest tests/test_price_approval.py -q`.
- [ ] **Step 3: Implement.** In `record_purchase`: `approved` if `current_user.role == "owner"`, or the line's unit price equals the current resolved price (at 0.0001), or there's no positive total. Otherwise `pending`. Set `price_reviewed_at` when approved. In the purchase PATCH: when the total changes and the editor is not an owner, set `pending` and clear `price_reviewed_at`. The >30% check (`_price_check`) already compares against `resolve_many`, which now ignores pending rows, so nothing else is needed there.
- [ ] **Step 4: Run** `uv run pytest tests/test_price_approval.py tests/test_purchase_sheet.py tests/test_price_after_unit_change.py -q`. All pass. Existing tests that expect a staff purchase to become the price immediately must now approve it first (or be logged as owner). Update them to say so, without weakening what they check.
- [ ] **Step 5: Commit** `feat(inventory): brand on items, owner approval before a purchase becomes the price`.

### Task 2: Kitchen-made items: recipes for inventory items, recursive costing, pack price (backend)

**Files:**
- Modify: `backend/app/models/costing_models.py`, `backend/app/models/inventory_models.py` (relationships)
- Modify: `backend/app/db/session.py`, with a new `ensure_costing_made_items(bind=None)` called on startup next to `ensure_inventory_columns`
- Modify: `backend/app/schemas/costing*.py`, `backend/app/api/v1/endpoints/costing.py`, `backend/app/crud/costing*.py`
- Modify: `backend/app/utils/usage.py` (skip made-item recipes as sales sources)
- Modify: `backend/app/api/v1/endpoints/inventory.py` (pack-price endpoint)
- Test: `backend/tests/test_made_items.py`

**Interfaces (produces):**
- `DishCosting.inventory_item_id` Integer FK `inventory_items.id`, nullable, unique, indexed. `DishCosting.menu_item_id` becomes nullable. Relationships: `DishCosting.made_item` ↔ `InventoryItem.recipe` (uselist=False).
- `ensure_costing_made_items`: if `dish_costings` lacks `inventory_item_id`, or `menu_item_id` is NOT NULL, rebuild the table with SQLite's documented procedure: `PRAGMA foreign_keys=OFF`; create `dish_costings_new` from the model's DDL; `INSERT … SELECT` the shared columns; `DROP` old; `ALTER TABLE dish_costings_new RENAME TO dish_costings`; recreate indexes; `PRAGMA foreign_keys=ON`. Never rename the old table first, because SQLite would rewrite the FK in `dish_costing_ingredients`. Idempotent. Test it on a DB created with the old schema.
- `DishCostingIn`: `menu_item_id: Optional[int] = None`, `inventory_item_id: Optional[int] = None`, `yield_units: Optional[Decimal] = Field(None, gt=0)`. Exactly one id is set, else 422/400. A dish still requires `yield_units`. For a made item, when it's omitted, the yield is the sum of the line quantities converted to the made item's unit (`app.utils.units.convert`). If any line can't convert: 400 `"Type how much one batch makes"`.
- `DishCostingOut` adds `inventory_item_id`, `kind: Literal["dish","made"]`, `name` (the menu item or made item name), `unit` (the made item's unit, or None), and `used_in: List[{costing_id, name, kind}]` (recipes that list this made item as an ingredient).
- `GET /costing/item/{inventory_item_id}` returns `DishCostingOut` (404 if none). Create and update go through the existing `POST /costing` and `PATCH /costing/{id}`. `POST /costing/preview` accepts made items too.
- Costing recursion in `costing.py`: `_build_ingredient_inputs(..., memo: dict | None = None, stack: tuple[int, ...] = ())`. For an ingredient whose item has a `recipe`, the unit price is `breakdown.raw_material_cost / yield_units` (no overheads), `price_source = "recipe"`, and missing prices inside make the line `price_missing=True` with `reason="no_price"`, so the dish reads incomplete. Memoize by item id within one request.
- `find_cycle(db, made_item_id: int, ingredient_item_ids: list[int]) -> list[str] | None` returns the names along the loop. On save it's a 400 with detail `"A recipe can't use itself: Cajun masala → Spice mix → Cajun masala"`.
- `GET /costing` (the Menu chip list) and `_get_reprice_impacts` skip costings with `menu_item_id IS NULL`. `usage.py` only reads menu-item recipes.
- `POST /inventory/items/{id}/pack-price` (owner), body `{price: Decimal>0, pack_quantity: Decimal>0, pack_unit: str}`. If the item's unit is in the same family as `pack_unit` (kg/g, L/ml), set `cost_per_unit = price / convert(pack_quantity, pack_unit, item.unit)`. Otherwise set `pack_size = pack_quantity`, `pack_unit = pack_unit`, `cost_per_unit = price` (per one of the item's own unit). Returns the item. Refused (400) for yes/no items.

- [ ] **Step 1: Write failing tests** in `test_made_items.py`:
  - `test_cookie_costs_from_whatsapp_sample`: create 8 `pkt` items and price each via pack-price: butter 58/100 g, powder sugar 75/1000 g, brown sugar 180/1000 g, fresh cream 60/250 g, vanilla 439/500 ml, maida 35/500 g, baking powder 38/100 g, choco chunks 220/400 g. Then a menu item at ₹130 (13000 paise) with a recipe, yield 4, lines 100 g, 25 g, 25 g, 50 g, 5 ml, 190 g, 3 g, 100 g. Asserts: `raw_material_cost == Decimal("150.21")`, `raw_cost_per_unit == Decimal("37.55")`, `cost_per_unit == Decimal("48.82")`, `62 <= margin_percent < 63`.
  - `test_cajun_masala_made_item`: the 8 spices (salt with no price; oregano 99/10 g, thyme 99/18 g, Kashmiri 140/100 g, paprika 99/52 g, garlic 99/100 g, onion 99/80 g, pepper 195/100 g), a made item "Cajun masala" in `g` with lines 200, 20, 40, 80, 266, 206, 100, 100 g and no yield given. Asserts: `yield_units == 1012`, `raw_material_cost == Decimal("1559.11")`, `is_complete is False`.
  - `test_dish_uses_made_item`: a dish with 10 g of Cajun masala gets that line's `price_source == "recipe"` and `price_missing True` (the salt gap propagates). After pricing salt via pack-price (₹28/1000 g → +₹5.60), the line costs `money((1559.11+5.60)/1012*10)`.
  - `test_cycle_refused`: made A uses B, then saving B with A is a 400 whose detail contains `"→"`.
  - `test_made_recipe_needs_yield_when_units_differ`: a pcs made item with gram lines and no yield is a 400.
  - `test_menu_chip_list_skips_made_items`: `GET /costing` lists only dishes.
  - `test_migration_rebuilds_old_table`: create the old `dish_costings` DDL (menu_item_id NOT NULL) in a fresh engine with one row plus an ingredient. Run `ensure_costing_made_items` twice. The row and ingredient are intact, `menu_item_id` is nullable, and `PRAGMA foreign_key_check` is empty.
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement** to the interfaces above.
- [ ] **Step 4: Run** `uv run pytest -q`. The whole suite passes except the 3 known `.env` credential failures in `test_auth*` (see INVENTORY_PLAN "Test isolation"). Report the exact failing names.
- [ ] **Step 5: Commit** `feat(costing): kitchen-made items with their own recipes, costed recursively; pack price entry`.

### Task 3: Ripple and recipes overview (backend)

**Files:**
- Modify: `backend/app/api/v1/endpoints/costing.py`, `backend/app/utils/pricing.py`, `backend/app/api/v1/endpoints/inventory.py` (pending-prices ripple), `backend/app/schemas/costing*.py`
- Test: `backend/tests/test_ops_overview.py`

**Interfaces (produces):**
- `pricing.resolve_many(db, items, as_of: datetime | None = None)`. With `as_of`, it uses only approved purchases with `coalesce(price_reviewed_at, created_at) <= as_of`. Typed prices are unchanged. Thread `as_of` through `_build_ingredient_inputs` and its recursion.
- `_get_reprice_impacts(db, overrides)` is transitive: a dish is affected when a line uses an overridden item directly or through any made item. Each `DishImpact` gains `via: List[str]` (made item names passed through). It also returns `made_impacts: List[{item_id, name, unit, cost_before, cost_after}]`.
- `PendingPrice.ripple = {affected_dishes: List[DishImpact], unaffected_count: int, made_items: List[...]}`, computed with `overrides = {item_id: new_price}` for that one purchase.
- `GET /costing/overview` (owner) returns `{rows: List[OverviewRow], totals: {below_target, missing_prices, no_recipe, average_margin}}`.
  - `OverviewRow = {kind: "dish"|"made", costing_id: int|None, menu_item_id: int|None, inventory_item_id: int|None, name, category: str|None, cost_per_unit: Decimal|None, unit: str|None, selling_price: Decimal|None, margin_percent, target_margin_percent, missing_count: int, cost_last_week: Decimal|None, status}`.
  - `status ∈ {"below_target","missing_prices","no_recipe","on_target","costed"}`. Active menu items without a recipe are rows with `status "no_recipe"`. Made items show `cost_per_unit` per their own unit. `cost_last_week` is the cost per unit priced `as_of = now - 7 days`. `average_margin` is the mean over dishes with a margin.
  - Rows are sorted: below_target (worst margin first), missing_prices, no_recipe, then the rest by name.

- [ ] **Step 1: Write failing tests:**
  - `test_ripple_passes_through_made_item`: onion is used by made "Bao buns", which is used by 3 dishes, and directly by 1. A pending onion purchase +25% gives `affected_dishes` length 4, the bao dishes' `via == ["Bao buns"]`, and `made_items` contains Bao buns with `cost_after > cost_before`.
  - `test_overview_statuses_and_order`: below target first, then missing prices, then no recipe. Totals match.
  - `test_overview_last_week`: a purchase approved 8 days ago at ₹32 (set `price_reviewed_at`), and one today at ₹40. `cost_last_week` uses 32.
  - `test_overview_survives_retired_made_item_and_deleted_menu_item`: 200, no crash.
- [ ] **Step 2: Run them and check they fail.** **Step 3: Implement.** **Step 4: Run the full suite** (same known failures as Task 2).
- [ ] **Step 5: Commit** `feat(costing): transitive price ripple and the recipes overview`.

### Task 4: Ops layout, routes, API hooks, recipe page (frontend)

**Files:**
- Create: `frontend/src/ops/ops.css` (all ops styles, scoped under `.ops`, with CSS variables for light and dark keyed off the app's existing dark-mode mechanism: check `ThemeToggle.tsx` / where `dark` is set on `<html>`)
- Create: `frontend/src/ops/OpsLayout.tsx` (top bar: Inventory · Daily sheet · Recipes (owner) · back to admin; `<Outlet/>`)
- Create: `frontend/src/ops/api.ts`. Typed calls and React Query hooks for every endpoint from Tasks 1–3, reusing `src/api/client.ts`. Extend the types in the existing `src/api/costing.ts`/`inventory.ts` types rather than duplicating them.
- Create: `frontend/src/ops/packPrice.ts`, `frontend/tests/packPrice.test.ts`
- Create: `frontend/src/ops/RecipePage.tsx`
- Modify: `frontend/src/main.tsx` (routes), `frontend/src/components/Sidebar.tsx` (one "Ops" entry → `/admin/ops/inventory`)

**Interfaces:**
- Routes, inside `<ProtectedRoute>` + `OpsLayout`, outside `AdminLayout`:
  - `/admin/ops` → redirect to `/admin/ops/inventory`
  - `/admin/ops/inventory`
  - `/admin/ops/sheet`
  - `/admin/ops/recipes` (owner)
  - `/admin/ops/recipes/dish/:menuItemId` (owner)
  - `/admin/ops/recipes/made/:itemId` (owner)
  - `/admin/ops/recipes/made/new` (owner)
- `parsePackPrice(text: string): { price: number; quantity: number; unit: string } | null` accepts `"₹99 / 10 g"`, `"99/10g"`, `"60 / 250 g"`, `"439/500ml"`, `"75 / kg"` (quantity 1), `"₹35/500 g"`. Anything else returns null.
- `formatPackPrice(price, packQuantity, packUnit)` returns `"₹99 / 10 g"`. The recipe page shows an item's price this way when it has a pack size, else `"₹40 / kg"`.

- [ ] **Step 1: Failing test** `frontend/tests/packPrice.test.ts` (node:test, like the existing tests there) for each accepted form above, plus `parsePackPrice("abc") === null` and `parsePackPrice("99") === null`.
- [ ] **Step 2: Run** `cd frontend && npm test` and check it fails. **Step 3: Implement** packPrice.ts and check it passes.
- [ ] **Step 4: Build the layout, routes, api.ts and RecipePage** to the spec's "Recipe page" and mockup `sketches-v1.html`:
  - The stat strip: batch makes, raw material per batch, cost per portion, menu price, margin with a below-target pill.
  - The table: Ingredient · Brand · Amount used · Price per pack · Cost in recipe · % of food cost.
  - Typed cells are editable inputs with a tinted background. Worked-out cells are plain.
  - An "Add ingredient" row with a search picker over active inventory items. Made items are marked "made". Enter in the amount moves to the next row's picker.
  - The amount input takes a number plus a unit select defaulting to the item's pack unit, then its unit.
  - The price cell is editable only when `price_source !== "purchase"`. On blur it parses with `parsePackPrice` and calls pack-price. An unparseable value shows an inline "Type it like ₹99 / 10 g".
  - The brand cell PATCHes the item.
  - The overhead rows (dish only) take a % or ₹ toggle.
  - Live totals come from `POST /costing/preview` (debounced ~300 ms). There's a Save button, and a "Saved" toast via `src/utils/toast.ts`.
  - A made item shows yield (editable, with the placeholder showing the auto sum), cost per unit, and "Used in" links.
  - Gaps read "no price yet" and totals read "≥ ₹…".
  - Phone: the table scrolls horizontally inside its wrapper, the ingredient column is sticky, and the stat strip wraps.
- [ ] **Step 5: Verify:** `npm run build` passes and `npm test` passes. Commit `feat(ops): ops layout and the recipe page`.

### Task 5: Recipes list page (frontend)

**Files:** Create `frontend/src/ops/RecipesListPage.tsx`, and modify `frontend/src/main.tsx` if the route still needs wiring.

- [ ] **Step 1:** Build it to the spec's "Recipes list" and mockup `recipes-overview-v1.html`, from `GET /costing/overview`:
  - Totals strip.
  - Search, plus filter chips: All / Needs attention / Made here / No recipe.
  - The table: Name · Type · Cost / portion · Menu price · Margin · vs last week (+₹ in red, −₹ in green, "—" when null or equal) · Status pill.
  - Row click goes to the dish or made route.
  - "+ New recipe": a small menu with "Dish from the menu…" (a picker over menu items without a recipe → dish route) and "Made in the kitchen" (→ `made/new`, which asks for name, unit, category, then creates the item via `POST /inventory/items` and opens its recipe).
  - Phone: the table becomes stacked rows (name and status on top; cost · price · margin below).
- [ ] **Step 2:** `npm run build` passes. Commit `feat(ops): recipes list`.

### Task 6: Daily sheet with price approvals (frontend)

**Files:** Create `frontend/src/ops/DailySheetPage.tsx`. Reuse `src/utils/purchaseSheet.ts` and the purchase endpoints and hooks that `PurchaseSheetTab.tsx` uses. Read that component for behaviour: keyboard-first new line, frequent-item ranking, quick-add unknown item, >30% jump confirmation, same-day edit and delete, day-end into tonight's count.

- [ ] **Step 1:** Build it to the spec's "Daily sheet" and the mockup:
  - Columns: Item · Brand · Unit qty · Rate · Purchased · In (₹) · Out (used) · Remaining · Day-end · Wastage, with "Spent today" at the bottom.
  - The same behaviour as PurchaseSheetTab, in the new look.
  - The date: admin sees today with no picker. Owner gets `<input type="date">` and prev/next. The URL is `?date=`.
  - Each row shows a small "awaiting approval" tag when `price_status === "pending"`.
  - Owner only: a "Price changes to approve (N)" section from `pending-prices`. Each card shows the item · brand, old → new per unit, a % pill (red > +10%, amber otherwise, "new" when `is_new_item`), who bought it and how much, and ripple bullets: "N dishes cost more, ₹a to ₹b a portion", "X drops to M%, below the T% target" per dish crossing target, and "Also through {made}: +₹d per {unit} → K dishes". Buttons: Approve / Not this time, plus "Approve all". After an action, invalidate the purchases, pending-prices, overview and items queries.
  - Phone: the new-line entry is a stacked form (item, unit qty, rate, purchased) above the table, and the table scrolls inside its wrapper.
- [ ] **Step 2:** `npm run build` passes. Commit `feat(ops): daily sheet with price approvals`.

### Task 7: Inventory page and Brand in the setup grid (frontend)

**Files:** Create `frontend/src/ops/OpsInventoryPage.tsx`. Modify `frontend/src/components/inventory/InventorySetupGrid.tsx` (a Brand text column next to Name, saved through the existing bulk PATCH) and `src/types` for item `brand`.

- [ ] **Step 1:** Build it to the spec's "Inventory" and mockups `inventory-v1.html` and `inventory-phone-v1.html`:
  - Laptop: a table of Item · Brand · In stock · Alert below · Price (formatted like the recipe page) · Value (stock × price, blank when no price) · Counted, grouped by category. Made items (those with a recipe) go in a "Made in the kitchen" group with a "made" pill. Low stock values are pill-highlighted.
  - Filters: All / Low (n) / Made here (n), plus search. The header shows item count and total stock value.
  - Side box: a "Start tonight's count" button → `/admin/inventory/count`, plus the last 7 nights from `GET /inventory/counts`, with date, counted_by, and items_checked / items_total. "no count" for missing nights. Tapping a night opens the existing transactions or stock-log view for that date if one exists, else no link.
  - "Edit all" → the existing setup grid (`/admin/inventory`, grid tab).
  - Phone (< 768 px): the count box goes on top, then search and chips, then one 52 px row per item (name; brand · price; stock and alert on the right).
  - The "made" flag comes from `GET /costing/overview` for owners. Admin can't call costing, so add `has_recipe: bool` to the item schema in the backend (`InventoryItem.recipe is not None`), add a test assertion for it to `test_made_items.py`, and use that instead.
- [ ] **Step 2:** `npm run build` passes, and `uv run pytest tests/test_made_items.py -q` passes. Commit `feat(ops): fresh inventory page; brand column in the setup grid`.

### Task 8: Verify and PR (controller)

- [ ] Run the app on a copy of production (`backend-prodcopy` + `frontend-local` launch configs). Enter the cookie and the Cajun masala through the UI. Check that the numbers match Task 2. Log an admin purchase, approve it as owner, and see the ripple. Check every page at 375 px and at desktop width, in light and dark.
- [ ] Update `docs/INVENTORY_PLAN.md` "What shipped". Push and open the PR to `pre-release`.
