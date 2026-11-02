# Inventory, costing and purchases — where the plan lives

The design for the inventory rework, dish costing and the purchase sheet lives in three
living documents, not in this file. They are editable and commentable, and they are the
source of truth. This file exists so anyone in the codebase can find them.

| Document | What's in it |
| --- | --- |
| [The plan (spine)](https://claude.ai/code/artifact/30397532-3e3f-4f74-bb49-2ba053856314) | The ledger identity, shared vocabulary, order of work, decisions log |
| [Hybrid stock count](https://claude.ai/code/artifact/118e2484-b467-4ef8-b622-096b050098db) | Item kinds, the count screen, the setup grid, pack size, migration |
| [Purchases and reconciliation](https://claude.ai/code/artifact/fd94a0a3-5dde-43f6-b47c-865b73685002) | The daily purchase sheet, where price comes from, waste, variance |
| [Dish costing screen](https://claude.ai/artifact/13qxuj8UoDnqMRZcrNik19) | Step 5's spec: the recipe sheet, named gaps, the backend it needs |

Start at the spine. When a spec and the spine disagree, the spine is wrong — fix it there.

## Decisions so far

Kept here as well as in the spine, because decisions are worth having in git history.

| Date | Decision |
| --- | --- |
| 2026-09-23 | The ✓ / − / + count row is not coming back; one answer per row. It failed testing with staff. |
| 2026-09-23 | Roll forward on `main`; keep the review sheet and server-saved counts. |
| 2026-09-23 | Start fresh rather than migrate. 278 adjustments over 6 days is setup noise, not history. |
| 2026-09-23 | Items split two ways: counted with a number, or answered yes/no. |
| 2026-09-23 | Pack size (`1 bottle = 700 ml`) bridges the count unit to the recipe unit. |
| 2026-09-23 | Wings are counted in portions, not pieces. |
| 2026-09-23 | Low stock exists to drive ordering, not to inform. |
| 2026-09-23 | Price comes from the purchase log; the typed price is a fallback. |
| 2026-09-23 | Bulk editing is an in-app grid with paste, not a CSV round-trip. |
| 2026-09-24 | No credit purchases — buying and paying are the same event. |
| 2026-09-26 | One unit per item — the one on the bill. Count, price and alert in it; never price in g or ml. |
| 2026-09-26 | The purchase sheet is the owners' table: Item · Unit qty · Rate · Purchased · In · Used · Remaining · Day-end · Wastage. Staff type rate × count (the owners' call, overriding "total only"); In is computed. |
| 2026-09-26 | The sheet's rows are only what was bought that day. |
| 2026-09-26 | Day-end on the sheet *is* tonight's count for that item — one number, one source. |
| 2026-09-26 | Each day's sheet is kept; staff see today's, only the owner opens other days. The sheet's day is the count night (to 04:00). |
| 2026-10-15 | Dish costing lives on the Menu page, owner only: a Cost column and a recipe sheet per dish. |
| 2026-10-15 | Yes/no items on a recipe are covered by overheads — shown, never costed, never a gap. |
| 2026-10-15 | No sub-recipes yet: a batch-made sauce is an inventory item with a typed price. |
| 2026-10-15 | Overhead defaults confirmed: labour 15%, fixed 10%, wastage 5%, packaging ₹0, target margin 65%. |
| 2026-10-15 | A suggested price rounds up to the next ₹10, and is offered only when every line is costed. |
| 2026-10-16 | An order suggestion brings stock back to twice the alert level; there is no separate par level yet. |
| 2026-11-02 | Inventory gets a fresh set of operational pages (see "Ops redesign"), with their own plain spreadsheet look, separate from the POS theme. Old tabs stay until the owners switch. |
| 2026-11-02 | Dish costing moves to its own pages, one table per dish. Reverses 2026-10-15 "costing lives on the Menu page" (the Menu chip keeps working; it reads the same rows). |
| 2026-11-02 | Sub-recipes are in: a kitchen-made item (Cajun masala, sauces, bao) is an inventory item with its own recipe, costed from it. Reverses 2026-10-15 "no sub-recipes yet". |
| 2026-11-02 | A purchase becomes the price only once an owner approves it. Owners' own entries are approved as they're made. Amends 2026-09-23 "price comes from the purchase log". |
| 2026-11-02 | Brand is a plain field on the item. Two brands stocked at once are two items; nothing enforces either way. |
| 2026-11-02 | AI insights and alerts wait for a second pass, after a couple of weeks of real prices. |

## Ops redesign (2026-11-02)

Agreed with the owner's developer on 2026-11-02, from the owners' two paper sketches (the daily
"ingredient / inventory calculator" and the dish costing table) and their WhatsApp sample data.
Mockups: [docs/ops-redesign-mockups/](ops-redesign-mockups/). This section is authoritative for the
new pages. Where the spine artifact disagrees on costing, sub-recipes or price approval, this wins.

**Why.** The owners tried the recipe sheet on the Menu page and the inventory tabs and found them
too hard to onboard. They do this by hand today on paper and in WhatsApp, and they picture a
Google Sheet: a table where people type some columns and the rest is worked out.

**Who.**
- The **manager** (admin login) buys chicken, vegetables and masalas and logs them on the daily
  sheet, on a phone or laptop. Staff count stock nightly on a phone.
- The **owners** (owner login) want the overview. They check every price change and approve it,
  and they can log purchases too. Phone and laptop both.

**Goals.** Owners see what each dish costs per portion and its margin, what changed today and which
dishes it hit, and stock as plain numbers. The manager logs a day's buying fast on a phone.

**Non-goals for this pass.** AI insights and alerts. A "made a batch" action (see Known gaps).
Retiring the old Inventory tabs or the Menu recipe sheet.

**Anti-goals.** Anything that needs the owners to understand pack-size bridging or units to get a
cost. A count screen that asks more than one answer per row.

### Three kinds of thing

1. **Bought ingredients** (onion, Amul butter, Ganesh maida): an inventory item with a brand and a
   price per pack, counted in inventory.
2. **Kitchen-made items** (Cajun masala, house sauces, bao): an inventory item that is never bought.
   It has its own recipe, and its cost per unit is the recipe's batch cost ÷ the batch yield. It's
   counted in inventory, has no menu price, and gets no overheads.
3. **Dishes**: a menu item with a recipe of ingredients and/or kitchen-made items. It has a cost per
   portion, a menu price and a margin, with overheads (packaging, labour, fixed, wastage) as today.

### Pages

All under `/admin/ops/…`, in a standalone layout (no POS sidebar, like `/admin/tools`), with a small
top bar linking the four pages. Light and dark, phone and laptop. The admin sidebar gets one entry.

| Page | Route | Who |
| --- | --- | --- |
| Recipes list | `/admin/ops/recipes` | owner |
| Recipe page (a dish or a made item) | `/admin/ops/recipes/dish/:menuItemId`, `/admin/ops/recipes/made/:itemId` | owner |
| Daily sheet | `/admin/ops/sheet` (today) and `?date=` | admin: today only; owner: any day, plus approvals |
| Inventory | `/admin/ops/inventory` | admin and owner |

**Recipe page.** Sketch 2's columns plus brand: *Ingredient · Brand · Amount used · Price per pack ·
Cost in recipe · % of food cost*. Under the lines: raw material for the batch, per portion and as %
of menu price, then *Packaging · Labour · Fixed cost · Wastage* (each a % of raw material or a ₹
amount, defaulting to 0 / 15 / 10 / 5%), then cost per portion, menu price, margin against target.
Top of the page: *Batch makes* (e.g. 4 cookies; for a made item, e.g. 1,012 g), raw material per
batch, cost per portion, menu price, margin.
- Typed by a person: ingredient, amount used, batch size, menu price, overheads. Worked out: cost
  in recipe, %, totals, margin. Typed and worked-out cells look different.
- **Price per pack** shows the item's current price as "₹99 / 10 g" with its source. When the item
  has no approved purchase, the owner can type it right in the cell, in that form: one entry sets
  price and pack together. If the item's unit is kg/g/L/ml, the price converts to the item's unit.
  Otherwise the pack size and pack unit are set from it (so "₹99 / 10 g" on a pkt item means
  1 pkt = 10 g at ₹99). The cell then reads "typed" until a purchase replaces it.
- A made item is a line like any other: *Cajun masala · 10 g · ₹1,541 / kg · ₹15.41*.
- A line with no price reads "no price yet", and totals show as "≥ ₹…".
- Overheads and menu price appear only on dishes. A made item's page shows batch cost, yield
  and cost per unit, plus a list of the dishes that use it.
- Brand is shown from the item and editable from this page.

**Recipes list.** One table of every dish and made item: *Name · Type · Cost / portion (made: per kg
or pc) · Menu price · Margin · vs last week · Status*. Status is below target / N prices missing /
no recipe / on target / costed. Totals at the top: below target, missing a price, no recipe yet,
average margin. Filters: All, Needs attention (worst first), Made here, No recipe. "+ New recipe"
creates a dish recipe for a menu item, or a new made item with its recipe. "vs last week" is the
change in cost per portion priced as of 7 days ago.

**Daily sheet.** Sketch 1's columns plus brand: *Item · Brand · Unit qty · Rate · Purchased · In (₹) ·
Out (used) · Remaining · Day-end · Wastage*, with "Spent today" at the bottom. The manager types item,
unit qty, rate, purchased and day-end. In, Out, Remaining and Wastage are worked out, exactly as on
today's Purchases tab (same endpoints, same rules). The new part, owner only: **price changes to
approve**. Each pending purchase whose price differs from the current one, or which is a new item,
shows: old → new per unit, % change, who bought it and how much, and its ripple. The ripple lists how
many dishes cost more, the range per portion, which drop below target, and which made items it
passes through ("Bao buns +₹0.40 → 3 dishes"). Buttons: Approve, Not this time, Approve all. A
purchase at the same price as the current one is approved without asking.

**Inventory.** Laptop: a table of plain numbers, *Item · Brand · In stock · Alert below · Price ·
Value · Counted*, grouped by category, with made items in their own group tagged "made". Filters:
All, Low, Made here, plus search. A side box has "Start tonight's count" and the last 7 nights (who,
and how many of all items were counted; tap for that night's changes). Phone: the count box on top,
then one row per item (name, brand · price; stock and alert on the right), touch-sized. "Start
tonight's count" opens the existing count screen (`/admin/inventory/count`): number boxes, one
answer per row, Out / Have it for yes/no items. Staff accepted it, so it stays. "Edit all" opens the
existing setup grid (`InventorySetupGrid`) with a Brand column added.

### Backend

- `inventory_items.brand` (VARCHAR, nullable), via `_INVENTORY_ADDED_COLUMNS`. Returned on items,
  editable in the grid, the item form and the recipe page.
- **Price approval.** `inventory_transactions.price_status` (`pending` / `approved` / `rejected`;
  NULL means approved: rows from before the gate) and `price_reviewed_at`.
  - A purchase is saved `pending` when logged by admin, and `approved` when logged by an owner or
    when its unit price equals the current price.
  - `latest_priced_purchases` and the >30% jump check read approved rows only.
  - "Not this time" sets `rejected`: stock and the day's spend still count, it just never becomes
    the price.
  - Approving does **not** go through `/costing/reprice`, which writes `cost_per_unit` and would turn
    a purchase price into a typed one.
  - Endpoints: `GET /purchases/pending-prices` (with ripple), `POST /purchases/{id}/price-review`
    (`approve` / `reject`), and an approve-all.
  - Production has no purchases, so nothing to backfill.
- **Made-item recipes.** `dish_costings` gets a nullable `inventory_item_id` (unique), and
  `menu_item_id` becomes nullable. Exactly one of the two is set, checked in the API. SQLite can't
  drop NOT NULL in place, so the startup migration rebuilds the table once (copy rows, swap) when
  `menu_item_id` is still NOT NULL. Production has 0 rows. A made item's yield is stored as
  `yield_units` in the made item's own unit. It defaults to the summed line quantities when every
  line converts to that unit, and is typed otherwise (bao, a reduced sauce). Everything that walks
  `dish_costings` assuming a menu item (the Menu chip list, `usage.py`, reprice) must skip
  made-item recipes, or use them only through recursion.
- **Costing recurses.** When an ingredient has its own recipe, its unit price is that recipe's raw
  batch cost ÷ yield (no overheads), memoized per request. Saving a recipe that would use itself,
  directly or through another made item, is refused with the chain named. A made item's missing
  prices propagate as gaps.
- **Ripple is transitive.** `_get_reprice_impacts` counts a dish as affected when any line uses the
  changed item directly or through a made item, and reports the made items it passed through.
- **As-of pricing** for "vs last week": the latest approved purchase reviewed before the date (typed
  prices have no history, so they read as unchanged).
- **Check left behind:** one test seeds the WhatsApp sample. It asserts cookie (makes 4, ₹130):
  raw ₹150.21 a batch, ₹37.55 a cookie, ₹48.82 with default overheads, 62% margin. It asserts Cajun
  masala's priced lines total ₹1,559.11, with salt as a gap. It also asserts that a dish using
  10 g of masala picks up its cost, and that a self-referencing recipe is refused.

### Calls made by the developer, not the owners

Check these when reading. All are cheap to change.
- Brand lives on the item, not on each purchase line. A one-off purchase of another brand shows
  in the approval list (the price will differ) but doesn't change the item's brand.
- An owner's own purchases skip approval. A purchase at an unchanged price skips it too.
- Price and Value on the inventory page are visible to admin as well as owner. The manager types
  rates anyway. The recipe pages stay owner-only, as costing is today.
- The count screen and the setup grid are reused as they are (plus Brand), not redesigned this pass.
- The daily sheet is rebuilt in the new look on the existing purchase endpoints, rather than
  restyling `PurchaseSheetTab`.
- One PR to `pre-release`, built in this order: backend → recipe page → recipes list → daily sheet
  with approvals → inventory page.

### Known gaps after this pass

- **Nothing records "made a batch".** Sales × recipes take Cajun masala out of stock, but nothing
  takes the spices out when a batch is made. Until a "Made 1 batch" button exists on the made item's
  page (spices out, masala in), the daily sheet's Out and Wastage for spices used only inside made
  items read low or empty.
- **Typed prices have no history**, so "vs last week" sees only purchase-driven changes.
- AI insights and alerts (second pass).

## Next up

**New (2026-11-02):** the ops redesign above is the current build. Its PR targets `pre-release`.

Read this first in a new session. Last checked 2026-10-18 against `origin/pre-release`
(`767cff3`) and `origin/main` (`6c75aa4`).

**Where things stand.** Steps 1–5 and 7 are built. The first batch (setup grid, hybrid
count) reached `main` in #59 and is live. Production's backend reports commit `c99044b`,
which is that merge. The second batch is 26 commits on `pre-release` that have never been
deployed: the purchase sheet, pack size in costing, the dish costing screen, vendors and order
messages, and the unit fix. `main` has 4 commits `pre-release` lacks (the waiter order review
and chit centring). A trial merge is clean.

**The bottleneck is owner data entry, not code.** Reconciliation is the payoff, and it can't
read true until purchases have been logged, recipes entered, and a clean week of counts and
purchases has run on top of them. Code for step 6 can be written in parallel, but nobody
should read its numbers before then.

**Production data, from a read-only snapshot on 2026-10-18:**

| What | Count | So |
| --- | --- | --- |
| Active inventory items | 173 (21 yes/no) | — |
| Items with a price above ₹0 | **0** | Every dish cost reads as gaps until purchases are logged or prices typed |
| Purchases ever logged | **0** | No price history exists. Nothing can misprice from the old g → kg unit changes, so that re-pricing step is dropped |
| Recipes (`dish_costings`) | **0** of 112 menu items | Used / Remaining / Wastage on the sheet and all of reconciliation are empty until recipes exist |
| Nightly counts | 5 of the last 7 days, last on 2026-10-16 | The count habit is in place |
| `digest.enabled` / `smtp.enabled` | `false` / `false` | The digest is already off in production; no action needed before deploying |

Starting `pre-release` against the snapshot applied its migrations cleanly: the four new
transaction columns and the `vendors` table. That's a dry run of the production deploy.

### Critical path

1. **Land `pre-release` on `main` and deploy** (dev, then owner). See "Landing
   `pre-release`" below.
2. **Start logging purchases on the Purchases tab** (staff, daily from the deploy). That's
   where prices come from, and production has none. Two weeks of logging prices the items
   bought often. Type prices in the setup grid only for things bought rarely.
3. **Enter real recipes on the Menu page** (owner). Start with the dishes that sell most and
   the expensive middle of the list: chicken, cheese, bulk sauces. Reconciliation only covers
   items that appear in a recipe.
4. **Name the opening count** (owner). The first full count after recipes exist is the opening
   balance. Reconciliation starts the week after it. Until then, every week's variance is
   setup noise.
5. **Build the waste log, then step 6, reconciliation** (dev). They can be built during 2–4, against a local copy of production (see "Testing locally on a
   copy of production").
   Prompts are under "Session prompts".
6. **First week of variance = a recipe-accuracy test** (owner). Fix recipes where the gap is
   a portioning difference, not a loss.

### Pending work, not on the critical path

| Work | Size | Blocked by | Notes |
| --- | --- | --- | --- |
| Waste log: `WASTE` type + `reason`, one button on the Purchases tab | ~½ day | — | Not built; `TransactionType` has only PURCHASE / USAGE / ADJUSTMENT. Reasons: spoiled, spilled, burnt / remade, staff meal, returned. Without it every variance is anonymous. |
| Reconciliation (step 6) | ~1½ days | waste log; recipes for real numbers | Weekly, worst-first, in rupees. |
| Cash link: day's purchase total as a named deduction on the cash counter | ~½ day | owner answer: paid from the till or separate cash? | Unbuilt. `expected_closing` deducts nothing for cash purchases today. |
| Settings toggle for the morning digest | ~½ day | — | Low priority: production already has `digest.enabled = false`. The code default is still `true` and there's no UI, so turning it on is a DB edit plus a restart. |
| Per-item stock target in order suggestions | small | — | Optional. Replaces "twice the alert level" (2026-10-16). |
| Test isolation from the local `.env` | small | — | `load_dotenv()` lets `backend/.env` usernames and passwords leak into tests: 14 failures locally, 3 with `ADMIN_USERNAME=admin OWNER_USERNAME=owner` set. The code is fine; `main` fails the same way. Pin test credentials in `conftest.py`. |

### Open questions for the owner

From the Purchases doc. Each one changes what gets built.

- **Where does purchase money come from: the till or separate cash?** This decides the cash
  link. It also matters because across 194 closed days the drawer read about ₹3,000 *over*
  expected. That deserves its own investigation.
- **Staff meals: track them or ignore them?** If the kitchen feeds staff daily, that shows up
  as unexplained variance every week unless it's logged under its own reason.
- **Photograph bills?** Useful in disputes, but it costs storage and adds a step at entry.
  Nothing is built for it.
- **Who logged a purchase.** Every row already stores `recorded_by`. Check whether the sheet
  should show it before calling this settled.

### Walkthrough of the owner screens (2026-10-18)

13 recipes and 22 item fixes were entered through the UI, on a local copy of production, to see where
it fights a real kitchen. Everything found, plus the recipes and estimated prices used, is in
[UI_WALKTHROUGH_NOTES.md](UI_WALKTHROUGH_NOTES.md). The ones that matter most:

- **Recipe lines defaulted to the count unit**, so "200" of soda meant 200 bottles and a ₹100 cooler read
  ₹16,909 a portion. Fixed in #73, along with offering g/ml for piece-counted items and pack size on the
  item form.
- **Nothing sanity-checks a number.** Not a ₹22,220 noodle packet in the grid, and not a line costing 40×
  the dish's menu price.
- **A unit change across families (pcs → kg) leaves stock untouched**, so 1202 g read as 1202 kg. Same-family
  changes are converted correctly.
- **Yes/no items on a recipe still ask for a quantity**, and every next ingredient needs the mouse.
- **The data needs an owner pass before reconciliation:** duplicate items (COCOA POWDER, CARAMEL/CAREMAL,
  KIT KAT, RAMEN/JAPANESE NOODLE, FRIES/FRENCH FRIES), CHEST BONELESS holding grams in `pcs`, and nightly
  counts that cover about a third of the list.

### Testing locally on a copy of production

Enter test data here, never in production. Snapshot production read-only with SQLite's
backup API into `backend/prodcopy.db` (gitignored, like every `*.db`). Use the same method as
`scripts/refresh-dev-db-from-prod.sh`, but download the file instead of installing it on
staging. Then start the `backend-prodcopy` and `frontend-local` configurations in
`.claude/launch.json`. The backend serves the copy on :8000 with MCP off. The frontend pins
`VITE_API_BASE_URL=http://localhost:8000`, so it can't reach production by accident. The copy
holds customer data: delete it when you're done.

## What shipped

Shipped already: the typed-input count row (`6b8cbf6`), the setup grid (1), yes/no items in
the nightly count (2): the Out / Have it row, the model-level clamp, review sheet and stock log;
the purchase sheet (3), pack size in costing (4), the dish costing screen (5), and vendors with
the order messages (7).

Purchase sheet (3), backend only: `total_amount` and `vendor_id` on purchase rows, a minimal
`vendors` table, `POST /transactions/purchase/check` (the >30% jump warning, dry run) and
`GET /purchases?business_date=` (the day's lines and total). Price resolution lives in
`backend/app/utils/pricing.py`; items return `current_price`, `price_source`, `price_as_of`,
and dish costing now prices from it. Every stock movement records the unit it was entered in
(`inventory_transactions.unit`), and a purchase is read in the item's unit as it is now: after a
g → kg change, "4000 g for ₹480" still prices at ₹120/kg and shows as 4 kg on the day's sheet. A
purchase in a unit the item can no longer convert from (pcs → kg) is passed over for the typed
price. Rows from before the column existed were backfilled with their item's unit at the time.

Purchase sheet screen (3), shipped as the **Purchases** tab in Inventory, built to the owners'
paper sketch: an editable table per day plus a keyboard-first new line (item ⏎ rate ⏎ count ⏎;
unit qty defaults to 1). Rows carry `pack_count`, so unit qty = quantity ÷ count and rate =
total ÷ count — only totals are stored. Items still in g/ml are entered in kg/L. The picker ranks
by what gets restocked (`GET /purchases/frequent`); an unknown item is added inline via
`POST /items/quick` and flagged `needs_setup` ("New" in the setup grid until the owner saves it).
Same-day corrections: `PATCH`/`DELETE /purchases/{id}`, refused once a count has taken the line in.
Day-end writes one line into tonight's count (`PUT /counts/tonight/items/{id}`). Used / Remaining /
Wastage come from sales × recipes (`app/utils/usage.py`) and read "needs recipe" until recipes
exist — prod has none yet, so those columns fill in only after the dish costing UI (5).

Pack size (4), backend: dish costing now bridges a recipe unit to the item's unit through its
pack size (`to_item_unit` in `backend/app/utils/units.py`, shared with the sheet's Used column),
so 30 ml of chilli oil counted in 700 ml bottles costs 30/700 of a bottle. A line that only a
pack size would fix comes back with `needs_pack_size: true` and a warning naming the question
("1 bottle = how many ml?"); yes/no items and unknown units (tbsp) never ask. The prompt itself
is the dish costing UI's job (5): ask when that flag is set, save it through the setup grid's
pack columns, and re-cost.

Dish costing screen (5), shipped on the **Menu** page, owner only: a Margin chip per dish
(`54% · below 65%`, `≤ 54% · 2 gaps`, `+ Recipe`) and a "Needs attention" filter that lists
below-target dishes worst first, then dishes with gaps, then dishes with no recipe. The chip opens
the recipe sheet (`frontend/src/components/costing/RecipeSheet.tsx`): ingredients with quantity
and unit, a live cost from `POST /costing/preview`, each price's source and date, a named reason
on every line that isn't costed, the pack-size question asked on the line itself, per-dish
overheads and target, and "Use ₹X as the menu price" behind a confirmation. Unsaved changes are
kept on the device. Every costing route is now owner-only, and a recipe in the item's own unit
(1 packet of a packet item) always costs, even for units the converter doesn't know.

Vendors and order messages (7): each item has an optional usual vendor (`default_vendor_id`), set
in the setup grid's Vendor column, where "+ New vendor…" adds one. A new **Order** tab in Inventory
groups what's below its alert level by vendor, A to Z, with Unassigned last, and renders one
paste-ready message per vendor ("Good evening. Please send tomorrow: • Hot sauce — 3 bottles")
with a Copy button. The count's "Count saved" screen leads there, and the Daily count tab says how
many items are low. Quantities are suggestions back to twice the alert level, rounded up to whole
units or hundreds of g/ml, and editable; a line can be left out; yes/no items go by name alone.
The owner can add or change a vendor's phone on the same screen (`PATCH /vendors/{id}`).
Copy-paste only: nothing is sent automatically.

## Session prompts

Self-contained, so a fresh session needs no other context. Prompts for shipped steps were
removed. Their history is in git (`git log -p docs/INVENTORY_PLAN.md`). Branch from
`pre-release` and target PRs there. The two prompts both touch inventory files, so run them
one after the other, or in separate worktrees.

### Waste log

```
In /Users/angelxlakra/dev/lily-cafe-pos, branch from pre-release. Add a waste log.

Read docs/INVENTORY_PLAN.md, then "Waste, logged rather than inferred" and "Data model"
in the linked Purchases and reconciliation doc.

Add WASTE to TransactionType and a nullable `reason` column on inventory_transactions
through the idempotent ADD COLUMN path in app/db/session.py. Reasons are a fixed list:
spoiled, spilled, burnt / remade, staff meal, returned, plus an optional note. Waste lowers
stock like any movement and must show in the stock log. Keep it in the one transactions
table: the ledger is a sum over movements.

UI: one button on the Purchases tab, a few seconds per entry. It's for the tray that got
thrown out, not a spilled spoonful. Staff can log, same as purchases. Show staff meal
separately from waste wherever totals appear.

Done = staff log a thrown-out tray in seconds, stock drops, the stock log names the reason.
```

### Reconciliation (step 6)

```
In /Users/angelxlakra/dev/lily-cafe-pos, branch from pre-release. Build weekly stock
reconciliation. The waste log should already be merged; check first.

Read docs/INVENTORY_PLAN.md, then the "Reconciliation" section of the Purchases doc.
Reuse app/utils/usage.py (sales × recipes, the sheet's Used column) and units.py's
to_item_unit. Don't write a second expected-consumption path.

opening + purchased − waste − counted = consumed; dishes sold × recipe = expected;
the gap is unexplained. Count nights run to 04:00 (app/core/business_day.py).

WEEKLY, not daily: daily variance at this scale is noise. Only list items where every term
exists, and never yes/no items. A missed count breaks the chain, so mark that week
incomplete rather than assuming the previous number. Present it as "these five don't add
up, worst first, in rupees", not a ledger dump. Say in the UI that early variance reflects
recipe accuracy, not theft. Owner only.

Done = a weekly variance list the owner can act on.
```

## Landing `pre-release`

This lands the second batch. The first landed in #59. Checked 2026-10-18:

- The trial merge of `pre-release` into `main` is clean. Merge `main` into `pre-release`
  first so the PR carries the 4 commits `main` has.
- The frontend builds. The backend suite passes apart from the `.env` leak noted in
  "Pending work".
- Schema changes are additive: a `vendors` table; `total_amount`, `vendor_id`, `pack_count`
  and `unit` on `inventory_transactions`; `default_vendor_id` and `needs_setup` on items.
  The `unit` backfill only fills `WHERE unit IS NULL`, so running it twice is safe.
- `orders`, `payments`, `print_jobs`, `cash_counter`, `auth` and `admin` aren't touched.

Order:

1. `scripts/refresh-dev-db-from-prod.sh`, then `scripts/deploy-backend.sh dev`. Click
   through Purchases, Order and a dish's recipe sheet on staging.
2. Merge to `main`. Vercel ships the frontend on push.
3. `scripts/deploy-backend.sh prod`, outside service hours. The script refuses anything but
   `origin/main` and confirms the live commit afterwards.
4. Check: `curl -s https://lily-cafe-pos.fly.dev/ | jq -r .commit` equals
   `git rev-parse origin/main`, and `GET /api/v1/inventory/purchases?business_date=…`
   answers rather than 404s.

**Morning digest.** Already off: production's `app_settings` has `digest.enabled = false`
(checked 2026-10-18), so this deploy starts nothing. To turn it on, set the row to `'true'`
over `flyctl ssh console -a lily-cafe-pos`, then restart the app, because the boot check is
what creates the task.

## Deploying, and knowing what's deployed

The frontend auto-deploys from `main` on Vercel. The backend deploys only by hand, through
`scripts/deploy-backend.sh <prod|dev>`. Don't run `flyctl deploy` directly. It builds from
the working directory rather than git, and the local `fly.toml` names the *dev* app. Both
have already caused outages (2026-09-26: a "successful" release without the count routes,
and the cafe lost a night's count to a 404).

`GET /` returns the commit the image was built from. `"unknown"` means an unstamped build.
After any backend change, hit the new endpoint rather than trusting the release status.

Images v26 and earlier carry a copy of a developer's local `.env` (fixed in #56). It was
inert in production, but those images still hold it.

## Not covered here

`docs/master-project-document.md` predates this work — its header still reads October 2024.
Treat it as background, not as the current plan for inventory.
