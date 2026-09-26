# Inventory, costing and purchases — where the plan lives

The design for the inventory rework, dish costing and the purchase sheet lives in three
living documents, not in this file. They are editable and commentable, and they are the
source of truth. This file exists so anyone in the codebase can find them.

| Document | What's in it |
| --- | --- |
| [The plan (spine)](https://claude.ai/code/artifact/30397532-3e3f-4f74-bb49-2ba053856314) | The ledger identity, shared vocabulary, order of work, decisions log |
| [Hybrid stock count](https://claude.ai/code/artifact/118e2484-b467-4ef8-b622-096b050098db) | Item kinds, the count screen, the setup grid, pack size, migration |
| [Purchases and reconciliation](https://claude.ai/code/artifact/fd94a0a3-5dde-43f6-b47c-865b73685002) | The daily purchase sheet, where price comes from, waste, variance |

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

## Build queue

In dependency order.

0. **Merge dish costing's backend, fix its four bugs** (~½ day) — do this soon and
   independently of everything else. See below.
1. **Setup grid** (~2 days) — bulk-edit every item's kind, unit, pack size, threshold, price.
   The only true prerequisite; nothing else can be configured without it.
2. **Hybrid count** (~1½ days) — yes/no items and the two-button row.
3. **Purchase sheet** (~1½ days) — daily log with amount and vendor. Runs alongside 2.
4. **Pack size** (~½ day) — the two columns plus the prompt when an item joins a recipe.
5. **Dish costing UI** (2–3 days, not yet specced) — recipe builder and cost readout.
   Pointless before real prices exist, so it follows 3.
6. **Reconciliation** (~1½ days) — weekly variance per item. Needs everything above.
7. **Vendors and order messages** (~1 day) — independent once low stock is trustworthy.

Shipped already: the typed-input count row (`6b8cbf6`).

## State of `feature/dish-costing`

Backend is done — models, CRUD, endpoints, schemas and strict unit conversion, ~1,250 lines.
There is **no frontend**: the only frontend files on the branch are a stray `pnpm-lock.yaml`
and `pnpm-workspace.yaml`, which should not be merged since this project uses npm.

The branch is 49 commits behind `main` and 13 ahead, drifting further each day. Since it is
backend-only it merges cheaply now and expensively later — merge it early and leave the API
unused until prices exist.

Four confirmed bugs to fix on the way in:

- `details=` instead of `detail=` on `HTTPException` at `endpoints/costing.py:66,68,99`, and
  `sataus_code=` at `:306`. All four are `TypeError`s that surface as 500s.
- `utils/costing.py:99` calls `convert()` before checking the price, so one ingredient with an
  unconvertible unit raises and kills the whole dish instead of one line.
- `price_missing` tests only for `None`, so a price of `0` counts as free. With 98 live items
  priced `0.00`, dishes would report confident ₹0 ingredient lines and still look complete.

## Session prompts

One per module, each self-contained so a fresh session needs no other context. Two things
are in every prompt on purpose: read `origin/pre-release` rather than `main` (it is more
than twenty commits ahead), and read the spec before touching code.

**Running these:** prompts 1, 2 and 3 all touch inventory files. Run them one at a time,
or give each its own git worktree — concurrent sessions in a single checkout will
overwrite each other. Suggested order: 0 now, then 1, then 2 and 3 together, then
4 → 5 → 6, with 7 whenever ordering help matters more than waste reporting.

### 0 — Fix and merge dish costing's backend

Fix on the branch first, then merge. A merge commit that also carries fixes is hard to
review and hard to back out of, and if the merge goes badly you keep the fixes.

```
In /Users/angelxlakra/dev/lily-cafe-pos: get origin/feature/dish-costing ready and merge
it into pre-release. Read docs/INVENTORY_PLAN.md first — its "State of
feature/dish-costing" section lists what's wrong. Work ON that branch, don't merge first.

Step 1, fix these four bugs as their own commit on feature/dish-costing:
- `details=` should be `detail=` at endpoints/costing.py:66,68,99, and `sataus_code=`
  should be `status_code=` at :306. All four are TypeErrors that surface as 500s.
- utils/costing.py calls convert() before checking the price, so one ingredient with an
  unconvertible unit raises and kills the whole dish instead of costing one line at 0.
- price_missing only tests for None, so a price of 0 counts as free. 98 live items are
  priced 0.00, so dishes would report confident ₹0 lines and still look complete.

Step 2, add three tests — there are currently none for ~1,250 lines of money handling:
a normal cost calculation, one with a missing price, one with an unconvertible unit.

Step 3, merge main into the branch, then the branch into pre-release. Do NOT bring its
frontend/pnpm-lock.yaml or pnpm-workspace.yaml — this project uses npm.

Don't build any costing UI; the frontend doesn't exist yet and comes much later. Leave
the API unused until real prices exist.

Done = bugs fixed with tests proving it, merged into pre-release, full test suite passes.
```

### 1 — Setup grid

```
In /Users/angelxlakra/dev/lily-cafe-pos, branch from pre-release. Build the inventory
setup grid: one editable table where the owner sets every item's kind, unit, pack size,
threshold and price, with ONE save.

Read docs/INVENTORY_PLAN.md, then the "Setup grid" section of the linked Hybrid stock
count doc. Check TemplateImportModal.tsx on pre-release before planning — it was rebuilt
and differs from main.

Key points from the spec: plain inputs in table cells (no grid library), paste from
Google Sheets support, freeze Name/Category, per-column locks with Stock locked by
default, dirty-cell highlighting and Revert, one bulk PATCH endpoint. ~196 rows means
memoize per row.

The grid also needs a way to retire an item. Run backend/scripts/inventory_review.py first
for the candidate list — note that "sitting at zero" does NOT mean dead: 36 active items
have never had a transaction and they include SALT, MAIDA and the garbage bags. Retire
means deactivate, not delete: DELETE /items/{id} is already a soft delete that flips
is_active, because transactions reference those rows.

Done = the owner can edit every field for all items, retire dead ones, and save once.
```

### 2 — Hybrid count

```
In /Users/angelxlakra/dev/lily-cafe-pos, branch from pre-release. Add yes/no items to
the nightly stock count.

Read docs/INVENTORY_PLAN.md and the Hybrid stock count doc it links.

Items split two ways: counted with a number, or answered Out / Have it. Add count_mode
to inventory_items, clamp presence quantities in a model validator — there are FIVE
writers of current_quantity, not one. Replace the count row's control with two buttons
for presence items.

Do NOT reintroduce the ✓ / − / + cluster; it failed user testing. Keep the review sheet,
the saved counts and the 1½ fraction idiom. Exclude presence items from the
"big differences" list.

Done = a yes/no item can be answered, saved, and reads correctly in the review sheet
and stock log.
```

### 3 — Purchase sheet

```
In /Users/angelxlakra/dev/lily-cafe-pos, branch from pre-release. Build the daily
purchase sheet.

Read docs/INVENTORY_PLAN.md, then the linked Purchases and reconciliation doc.

POST /inventory/transactions/purchase already exists and raises stock — it just has no
concept of money or vendors. Extend it: total_amount and vendor_id on the transaction.

Capture the TOTAL paid, not a unit price — people know "4 kg for ₹480". Show a running
day total. Entry must take ~90 seconds for 5–15 lines; this is an append log, not the
setup grid. Allow adding an unknown item inline. No credit purchases — buying and paying
are one event.

Done = a day's purchases can be logged in under two minutes and stock goes up correctly.
```

### 4 — Pack size

```
In /Users/angelxlakra/dev/lily-cafe-pos, branch from pre-release. Add pack size to
inventory items.

Read docs/INVENTORY_PLAN.md and the "Data model" section of the Hybrid stock count doc.

Two optional columns meaning "1 bottle holds 700 ml" / "1 portion = 6 pcs". You count and
price in the item's own unit; pack size bridges to the recipe's unit. Only needed when the
recipe unit is in a different family from the count unit — backend/app/utils/units.py on
the costing branch handles same-family conversion already.

Prompt for it when an item joins a recipe and units don't bridge, not from everyone at setup.

Done = a recipe in ml can cost against an item counted in bottles.
```

### 5 — Dish costing UI

```
In /Users/angelxlakra/dev/lily-cafe-pos, branch from pre-release. Build the frontend for
dish costing. The backend already exists (merged from feature/dish-costing) — read its
endpoints and schemas before designing anything.

Read docs/INVENTORY_PLAN.md for context. There is NO spec for this UI yet — propose one
before building, and check it with me.

A recipe builder per menu item (pick inventory items, quantity, unit) plus a cost readout
with margin. Items that can't be costed — yes/no items, no price, unconvertible units —
must show as incomplete with a named reason, never as ₹0. Show the price's as-of date.

Done = a menu item's recipe can be built and its true cost read, with honest gaps.
```

### 6 — Reconciliation

```
In /Users/angelxlakra/dev/lily-cafe-pos, branch from pre-release. Build weekly stock
reconciliation.

Read docs/INVENTORY_PLAN.md, then the "Reconciliation" section of the Purchases doc.

opening + purchased − waste − counted = consumed; dishes sold × recipe = expected;
the gap is unexplained. Add a WASTE transaction type with a reason code.

WEEKLY, not daily — daily variance at this scale is noise. Only for items where every term
exists; don't list yes/no items. Present as "these five don't add up, worst first, in
rupees" — not a ledger dump. Say in the UI that early variance reflects recipe accuracy,
not theft.

Done = a weekly variance list the owner can act on.
```

### 7 — Vendors and order messages

```
In /Users/angelxlakra/dev/lily-cafe-pos, branch from pre-release. Build vendors and the
end-of-day order message.

Read docs/INVENTORY_PLAN.md, then "Vendors and the order message" in the Purchases doc.

A vendors table, an optional default vendor per item, and the low-stock list grouped by
vendor rendered as paste-ready messages with a copy button each. Unmapped items go in an
"Unassigned" group — vendor setup must never block the alert. Suggested quantities are
editable suggestions, not calculations.

Copy-paste only for now. If automatic delivery comes up: Telegram is a bot token and a
chat id; WhatsApp needs the Business API with approved templates and per-message fees.

Done = the owner finishes a count and can send each vendor an order in one tap each.
```

## Deploying, and knowing what's deployed

The frontend auto-deploys from `main` on every push (Vercel). The backend does **not** —
it needs someone to run `flyctl deploy` by hand. The two drift, silently.

**Two gotchas, both of which have already caused an outage:**

1. **The local `fly.toml` says `app = "lily-cafe-pos-dev"`.** It is gitignored, so it
   differs per machine. A plain `flyctl deploy` from the repo root deploys to the *dev*
   app. Production needs the app named explicitly:

   ```
   flyctl deploy -a lily-cafe-pos --build-arg GIT_SHA=$(git rev-parse HEAD)
   ```

2. **A deploy can report success while shipping stale code.** On 2026-09-26 the backend
   was found to have no `/inventory/counts` routes at all, five days after they landed on
   `main` and four days after a "successful" release. A misplaced `.dockerignore` had
   excluded source from the build context, so the image built, the health check passed and
   `fly releases` looked clean — while the endpoint the staff needed simply was not there.
   The cafe counted 82 items that night and lost all of it to a 404. Fixed in
   [#56](https://github.com/angelxlakra/lily-cafe-pos/pull/56).

**The underlying gap was that nothing reported what is actually deployed.** `GET /`
returned `version: 0.2.0`, hardcoded and equally true of the stale image. It now also
returns the commit the image was built from, so checking is one line rather than grepping
inside a running container:

```
curl -s https://lily-cafe-pos.fly.dev/ | jq -r .commit    # vs: git rev-parse origin/main
```

An unstamped build reports `"unknown"` rather than claiming a version it cannot vouch for,
so a forgotten `--build-arg` is visible instead of silent. Either way, after any backend
change, verify the thing you shipped rather than the release status — hit the new endpoint
and check it answers.

## Not covered here

`docs/master-project-document.md` predates this work — its header still reads October 2024.
Treat it as background, not as the current plan for inventory.
