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

## Next up

Read this first in a new session. Last checked 2026-10-18 against `origin/pre-release`
(`767cff3`) and `origin/main` (`6c75aa4`).

**Where things stand.** Steps 1–5 and 7 are built. The first batch (setup grid, hybrid
count) reached `main` in #59 and is live. Production's backend reports commit `c99044b`,
which is that merge. The second batch is 26 commits on `pre-release` that have never been
deployed: the purchase sheet, pack size in costing, the dish costing screen, vendors and order
messages, and the unit fix. `main` has 4 commits `pre-release` lacks (the waiter order review
and chit centring). A trial merge is clean.

**The bottleneck is owner data entry, not code.** Reconciliation is the payoff, and it can't
read true until the owner has repriced items and entered recipes, and a clean week of counts
and purchases has run on top of them. Code for step 6 can be written in parallel, but nobody
should read its numbers before then.

### Critical path

1. **Land `pre-release` on `main` and deploy** (dev, then owner). See "Landing
   `pre-release`" below.
2. **Re-price items whose unit changed before the unit fix** (owner, right after the deploy).
   Older purchases were backfilled with the item's unit *at deploy time*, so an item that went
   g → kg earlier may price wrongly. Log a fresh purchase or type a price for those items.
3. **Enter real recipes on the Menu page** (owner). Start with the dishes that sell most and
   the expensive middle of the list: chicken, cheese, bulk sauces. Reconciliation only covers
   items that appear in a recipe.
4. **Name the opening count** (owner). The first full count after recipes exist is the opening
   balance. Reconciliation starts the week after it. Until then, every week's variance is
   setup noise.
5. **Build the waste log, then step 6, reconciliation** (dev). They can be built during 2–4.
   Prompts are under "Session prompts".
6. **First week of variance = a recipe-accuracy test** (owner). Fix recipes where the gap is
   a portioning difference, not a loss.

### Pending work, not on the critical path

| Work | Size | Blocked by | Notes |
| --- | --- | --- | --- |
| Waste log: `WASTE` type + `reason`, one button on the Purchases tab | ~½ day | — | Not built; `TransactionType` has only PURCHASE / USAGE / ADJUSTMENT. Reasons: spoiled, spilled, burnt / remade, staff meal, returned. Without it every variance is anonymous. |
| Reconciliation (step 6) | ~1½ days | waste log; recipes for real numbers | Weekly, worst-first, in rupees. |
| Cash link: day's purchase total as a named deduction on the cash counter | ~½ day | owner answer: paid from the till or separate cash? | Unbuilt. `expected_closing` deducts nothing for cash purchases today. |
| Settings toggle for the morning digest | ~½ day | — | `digest.enabled` defaults to `true` and has no UI; changing it is a DB edit. The scheduler is already live from #59. |
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

Not checked: how many items have prices, recipe counts, and which items had unit changes.
That needs production data, which wasn't read for this plan.

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

**Morning digest.** The scheduler went live with #59 and `digest.enabled` defaults to
`true` (`digest.email_enabled` defaults to `false`). Whether the owner turned it off isn't
known. If they want it off, set it in `app_settings` (`flyctl ssh console -a lily-cafe-pos`,
then an `INSERT OR REPLACE` of `('digest.enabled','false',…)`). Turning it back on needs an
app restart, because the boot check is what creates the task.

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
