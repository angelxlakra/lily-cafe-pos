# UI walkthrough notes — 2026-10-18

Entering real recipes, units, pack sizes and prices through the owner UI, on a local copy of
production (`backend/prodcopy.db`, branch `claude/recipe-units-by-weight`). Everything is typed as
an owner would: no API calls, no database edits.

Two kinds of note:
- **Rigid / lacking**: the flow couldn't do something a real kitchen needs, or fought it.
- **Irregular**: pills, button text, labels, layout, anything inconsistent or odd.

Prices typed here are estimates for testing, not real bills.

Left out on purpose: a few slips during entry were my automated typing, not the UI. A value landed on the
previous row after a search, and Cmd+A didn't select. The code has no search debounce and no Cmd+A
handling, so these aren't listed.

## Rigid / lacking

- **Nightly counts cover about a third of the list.** Each of the last 7 counts left 107–126 of
  173 items "not counted". There is no clean opening count for reconciliation to start from.
- **Pack size isn't visible in the Items list.** After saving 1 pcs = 100 g, BUTTER's row still
  reads "Alert below 1 · ₹54/pcs". You only see the pack size by opening the form.
- **No confirmation on save.** The item form closes silently; nothing says "Saved".
- **A unit change across families leaves stock as it was.** g → kg is handled well: the grid says
  "1 unit change converts stock, alert level and price on Save (2000 g becomes 2 kg)" and does it.
  But CHEST BONELESS going `pcs` → `kg` kept its 1202 (really grams) as 1202 kg, with no message.
  The grid should flag stock whenever the unit changes family.
- **A price typed before a unit change isn't converted.** I typed ₹0.06 on PUDINA while it was in g. The
  grid warned "price is per g or ml: switch those to kg or L", so I switched to kg, and it saved ₹0.06/kg
  (meant ₹60/kg). Conversion is skipped for a price edited in the same save, but the banner still says
  "converts … price". Either convert it or say "the price you typed is now per kg".
- **Clicking a grid cell doesn't select its contents** (request, not a bug). Typing after a click
  appends, so ₹0 + "22" saved as ₹220, then ₹22220. Enter moving down a column already selects the next
  cell; clicking into a cell should do the same, as in a spreadsheet.
- **No sanity check on grid prices.** ₹22,220 for a noodle packet saved without a question. The purchase
  sheet warns on a >30% jump; the grid doesn't warn on anything.
- **Escape reverts the cell, not just the suggestion list.** On a pack-unit cell with its suggestion list
  open, Escape cleared what I'd typed.

### Recipe sheet

- **An item with a pack size still defaults to its count unit.** PLAIN SODA (1 pcs = 750 ml) and GREEN MINT
  (1 pcs = 750 ml) were added as `pcs`, so "200" meant 200 bottles: ₹4,000 of soda, and the Lemon Mint
  Cooler read **₹16,909.95 per portion** against a ₹100 menu price. The same happened with VANILLA ICE
  CREAM (4 L tub). An item has a pack size because recipes use it in another unit, so the pack's unit
  should come first. *(Fixed in PR #73: the pack's unit now leads; checked with MILK → ml.)*
- **No sanity check on a line.** A single ingredient costing 40× the dish's menu price raised nothing.
  "This line costs ₹4,000 — 200 bottles?" would catch every wrong-unit slip.
- **A yes/no item asks for a quantity in "yes/no".** KEEMA CHILLI OIL shows `Qty [   ] yes/no`, and a line
  with no quantity isn't saved, so you type a meaningless 1. A yes/no line should need no quantity.
- **Enter in a quantity box does nothing.** Enter adds an ingredient and focuses its quantity, which is great,
  but Enter again doesn't return to "Add an ingredient". Every next ingredient needs the mouse.
- **The quantity box accepts letters.** Typing on after the quantity left "1chest" in the box.
- **The ingredient list sometimes doesn't open.** After clicking "Add an ingredient" and typing "sugar",
  no suggestions showed until I deleted and retyped a letter.
- **The pack size isn't shown on the line.** The ice cream line reads "₹700 / pcs · typed price" and costs
  60 ml correctly at ₹10.50, but nothing on the line says 1 pcs = 4 L, so the sum can't be checked.
- **The suggested-price box appears a beat late.** For a moment after the last edit, below-target dishes show
  no box at all, not even "A suggested price appears once…".

## Irregular

- **Unit list mixes two styles** (my change in PR #73): "Pieces (pcs)", "Kilograms (kg)" … then
  bare "pkt", "bottle", "tin". Give them the same "Packet (pkt)" form.
- **"Cost per unit (₹)"** doesn't name the unit. "₹ per kg" or "₹ per pcs" would follow the unit select.
- **"Alert below 0"** shows on BUTTER PAPER: an alert that can never fire, but it still reads like a setting.
- **The "Low stock" filter button looks pressed** (filled beige) even when it's off. It has the same
  fill as the secondary buttons, so on and off are hard to tell apart.
- **Recent counts show the username `lily_admin`**, a login name rather than a person.
- **The grid shows ₹0 where the price is really unset** (SOY MILK, COCONUT MILK) and a blank for others.
  0.00 and "no price" look different for no reason a user would know.
- **The "Recipe added" toast covers the sheet's title** (top of the screen, over the dish name).
- **The Menu table reflows when a margin chip appears.** "35% · below 65%" is wider than "+ Recipe", so the
  Name column narrows and names wrap ("BROWNIE / BOX"). Give the Margin column a fixed width.
- **"Needs attention (111)" is nearly the whole menu** while recipes are missing. The count says nothing
  useful yet. Count only costed dishes that miss target, and show "no recipe" separately.
- **Every row has a red Delete button beside Edit**, at the same size. One slip deletes a dish.
- **Button text is inconsistent:** "+ Add Item" (Title Case, typed plus) vs "Add item" in Inventory;
  "Add recipe" on a new sheet, "Save recipe" on an existing one.
- **Category pills mix cases**: "NOODLES" in capitals beside "Noodle Soup", "Something Sweet". That's
  data (the category's name), but the pill could normalise it.
- **The ingredient picker shows only the unit** ("pcs"), not the pack size, so BUTTER and BUTTER PAPER look
  alike and you can't tell which items already bridge to g or ml.
- **The save message is easy to miss**: "Saved 7 items. Stock changed on 1, logged as adjustments." sits
  in small grey text beside the counter, at the same weight as "no changes".

## Data found along the way

- CHEST BONELESS counted in `pcs` but holds 1202, which is grams.
- Vegetables in `g` holding 2–10: MUSHROOM 2, KIWI 4, LEMON 5, WATERMELON 1, CHICKEN PATTY 10, VEG PATTY 10.
- Duplicates: COCOA POWDER (BEVERAGES, pcs) and COCOA POWDER (FRONTIER, g); CARAMEL SYRUP / CAREMAL SYRUPS;
  KIT KAT (4 FINGERS) / KIT-KAT; RAMEN NOODLES / JAPANESE NOODLE (RAMEN NOODLE), both 42.

- Two fries items: FRENCH FRIES (DRY GROCERY, kg) and FRIES (VEGETABLES, g, 1000).
- Frying oil (REFINED OIL (TIN)) is a real cost on every fried dish that a per-dish recipe can't easily
  hold. It probably belongs in an overhead.

## Items changed (Edit all grid + item form)

| Item | Was | Now | Price (estimate) |
| --- | --- | --- | --- |
| BUTTER | pcs | pcs, 1 pcs = 100 g | ₹54 |
| MAIDA (LOOSE) | pcs | kg | ₹40 |
| SUGAR | pcs | kg | ₹45 |
| CHEST BONELESS | pcs, stock 1202 | kg, stock 1.2 | ₹280 |
| WINGS | pcs | portion, 1 portion = 6 pcs | ₹70 |
| NUGGETS | pcs | pkt, 1 pkt = 1 kg | ₹420 |
| VANILLA ICE CREAM. | pcs | pcs, 1 pcs = 4 L | ₹700 |
| MILK | pcs | pcs, 1 pcs = 500 ml | ₹30 |
| INSTANT COFFEE | pcs | pcs, 1 pcs = 50 g | ₹190 |
| PLAIN SODA | pcs | pcs, 1 pcs = 750 ml | ₹20 |
| GREEN MINT | pcs | pcs, 1 pcs = 750 ml | ₹450 |
| ABC SWEET SOY SAUCE | pcs | pcs, 1 pcs = 620 ml | ₹260 |
| LEMON | g, stock 5 | pcs | ₹6 |
| WATERMELON | g, stock 1 | kg, stock 3 | ₹30 |
| PUDINA PATTI, PYAJ SAAG, ICEBERG LETTUCE, CABBAGE | g | kg (stock converted) | ₹60, ₹80, ₹120, ₹30 |
| EGGS, RAMEN NOODLES, CHI DUMPLINGS, BAO, BROWNIE, MIE GORENG NOODLES, FRENCH FRIES | — | price only | ₹7, ₹30, ₹15, ₹12, ₹45, ₹22, ₹180 |

CHI DUMPLINGS at ₹15 a piece is probably high: it puts Chicken Dumplings at a 22% margin.

## Recipes entered

All 13 entered on the Menu page's recipe sheet. Margins use the default overheads (labour 15%, fixed 10%,
wastage 5%) and the estimated prices above.

| Dish | Menu ₹ | Recipe | Cost / portion | Margin |
| --- | --- | --- | --- | --- |
| Chicken Dumplings | 150 | 6 dumplings, chilli oil | ₹117 | 22% |
| Brownie | 90 | 1 brownie | ₹58.50 | 35% |
| Brownie with Ice-cream | 150 | 1 brownie, 60 ml vanilla | ₹72.16 | 51% |
| Chicken Bao Cajun Sauce | 150 | 2 bao, 100 g chest, 15 g iceberg, cajun sauce | ₹69.94 | 53% |
| Chicken Mie Goreng | 180 | 1 mie goreng, 100 g chest, 1 egg, 40 g cabbage, 15 ml sweet soy | ₹83.83 | 53% |
| Milk Coffee | 60 | 150 ml milk, 3 g instant coffee, 10 g sugar | ₹27.11 | 54% |
| MK Chicken Ramen | 250 | 1 ramen, 120 g chest, 1 egg, 10 g pyaj saag, keema chilli oil | ₹92.82 | 62% |
| Fried Chicken Nuggets in Korean Sauce | 250 | 160 g nuggets, korean sauce | ₹87.36 | 65% |
| Fried Chicken Wings in Korean Sauce | 280 | 6 pcs wings (1 portion), korean sauce | ₹91 | 67% |
| Lemon Mint Cooler | 100 | 1 lemon, 5 g pudina, 30 g sugar, 200 ml soda, 20 ml green mint | ₹32.48 | 67% |
| Butter Cookie (50g) | 50 | batch of 6: 100 g butter, 150 g maida, 60 g sugar | ₹13.59 | 72% |
| French Fries | 150 | 150 g fries | ₹35.10 | 76% |
| Watermelon Cooler | 120 | 300 g watermelon, 15 g sugar, ½ lemon, 100 ml soda | ₹19.96 | 83% |
