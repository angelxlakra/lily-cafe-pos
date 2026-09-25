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

## Not covered here

`docs/master-project-document.md` predates this work — its header still reads October 2024.
Treat it as background, not as the current plan for inventory.
