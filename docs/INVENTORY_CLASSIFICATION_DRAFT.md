# Inventory classification — draft for the owner to correct

A proposal for every **active** inventory item: how it is counted, what unit it is counted in,
and the pack size a recipe would need. It is a draft to correct, not a decision. Where a row is
wrong, fix the row. Nothing in the database has been changed.

- **Source:** production copy pulled 2026-09-26 (`prod.db`), 196 items, 173 active, 23 already
  retired, 0 saved counts. Cross-checked against `backend/scripts/inventory_review.py`.
- **Rules applied** (from [INVENTORY_PLAN.md](INVENTORY_PLAN.md) on `pre-release`):
  - Every item is either **number** (a count) or **yes/no** (have it or out).
  - Each item has one unit, the one on the bill. Count, price and set alerts in that unit.
  - Pack size (`1 bottle = 750 ml`) is only needed when a recipe uses a different kind of unit
    from the count unit. `kg ↔ g` and `L ↔ ml` convert on their own and need no pack size.
  - A yes/no item can never be costed in a dish. If a yes/no item turns out to matter to dish
    cost, change it to number.
  - "Never had a transaction" means the app has never tracked the item. It does **not** mean the
    item is dead. None of the 36 such items are proposed for retirement because of that alone.

## How to read the table

| Column | Meaning |
| --- | --- |
| Now | Unit and quantity in production today, e.g. `pcs · 1000` |
| Counted as | **number**, **yes/no**, or **merge →** for a duplicate |
| Unit | Proposed unit. `pack`, `packet`, `bottle`, `jar`, `tub`, `tin` and `carton` all mean one container as bought |
| Pack size | What one unit holds, only where a recipe would need it. `?` means the owner has to fill in the number. A figure followed by `?` is a common retail size, so check the label |
| Conf | high / med / **LOW**. Check the **LOW** rows first |
| Notes | Why, the converted quantity where the unit changes, and `untracked` for items with no transactions |

## Summary

| | Items |
| --- | --- |
| Counted as a number | 109 |
| Counted yes/no | 58 |
| Merge into another row (duplicate) | 6 |
| Low confidence: check these first | 18 |

### Stored in the wrong unit: fix these before anything gets a price

| Item | Now | Should be | Converted qty |
| --- | --- | --- | --- |
| CHEST BONELESS | pcs · 1000 | kg | 1.0 kg |
| LEG BONELESS | pcs · 2300 | kg | 2.3 kg (threshold `85` is meaningless in either unit, so reset it) |
| LEMON | g · 5 | pcs | 5 pcs |
| KIWI | g · 8 | pcs | 8 pcs |
| WATERMELON | g · 1 | pcs | 1 pcs |
| CHICKEN PATTY | g · 9 | pcs | 9 pcs (also filed under VEGETABLES) |
| MUSHROOM | g · 0 (history 2, 0, 1) | packet | Counts stored as grams |
| FRENCH FRIES | kg · 1800 | kg | 1.8 kg (grams typed into a kg item) |
| COCOA POWDER (FRONTIER) | g · 1 | merge | A count stored as grams. See duplicates |
| All other VEGETABLES | g | kg | Divide by 1000, e.g. PYAJ 2000 g → 2 kg. Vegetables are billed per kg |

### Duplicates: keep one, retire the other

Retiring means deactivating the row, which is a soft delete. Transactions keep pointing at the
retired row.

| Keep | Retire | Evidence | Conf |
| --- | --- | --- | --- |
| COCOA POWDER (BEVERAGES, #114) | COCOA POWDER (FRONTIER, #163) | Same name; #163 stores a count as grams | high |
| RAMEN NOODLES (#1) | JAPANESE NOODLE (RAMEN NOODLE) (#135) | Identical history 31, 37, 10, so the same stock was entered twice | high |
| CARAMEL SYRUP (#173) | CAREMAL SYRUPS (#119) | Misspelling of the same item; keep the correct spelling | med |
| FRENCH FRIES (#150) | FRIES (#80) | Both hold 1800, one under kg and one under g | med |
| KIT-KAT (#116) | KIT KAT (4 FINGERS) (#172) | Both at 6. If the 4-finger bar is a separate product, keep both | **LOW** |
| MAIDA (#12) | MAIDA (LOOSE) (#13) | Both untracked. May be packet and loose flour, which are two real items | **LOW** |

Possible duplicates that are probably **not** duplicates, which the owner should confirm:
CAJUN MASALA vs CAJUN MASALA POWDER (house blend vs bought powder?), TIL CHUTNEY vs TOMATO TIL
CHUTNEY, LAHSUN vs PEALED GARLIC (whole vs peeled, genuinely different).

---

## Full table

### BEVERAGES (28)

| Item | Now | Counted as | Unit | Pack size | Conf | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| BLUEBERRY JAM | pcs · 0 | number | jar | 1 jar = ? g | med | |
| BROWNIE | pcs · 2 | number | pcs | — | high | History 12, 3, 8, 2 |
| CARAMEL SYRUP | pcs · 1 | number | bottle | 1 bottle = 750 ml? | med | Keep this row. Syrups are costed per drink, so count them rather than yes/no |
| CAREMAL SYRUPS | pcs · 1 | merge → CARAMEL SYRUP | — | — | med | Duplicate |
| CHOCOLATE ICE CREAM | pcs · 0.5 | number | tub | 1 tub = ? ml | med | Half tubs already recorded |
| CHOCOLATE SYRUPS | pcs · 1 | number | bottle | 1 bottle = ? ml | med | |
| COCOA POWDER | pcs · 1 | number | pack | 1 pack = ? g | med | Keep this row. History contains a `500`, which looks like grams typed once |
| COFFEE BEANS | pcs · 0 | number | packet | 1 packet = 1000 g? | med | Biggest drink cost, so it must stay a number |
| COLD DRINKS | pcs · 1 | number | ? | — | **LOW** | One row for every brand? Crates or bottles? History 2, 4, 3, 1 |
| COOKIES | pcs · 0 | number | pcs | — | **LOW** | untracked. Three retired COOKIE rows exist. Bought per piece or per box? |
| DARK COMPOUND | pcs · 0 | number | slab | 1 slab = ? g | med | Chocolate compound. History 2, 1, 0.5, 0 |
| GREEN MINT | pcs · 0.5 | number | bottle | 1 bottle = ? ml | med | Assumed to be mint syrup |
| GRENADINE | pcs · 0.5 | number | bottle | 1 bottle = ? ml | med | |
| HOT CHOCOLATE MIX | pcs · 1 | number | pack | 1 pack = ? g | med | |
| INSTANT COFFEE | pcs · 3 | number | ? | ? g | **LOW** | History 8, 4, 3. Too many for jars, so sachets or packets? |
| KIT KAT (4 FINGERS) | pcs · 6 | merge → KIT-KAT | — | — | **LOW** | See duplicates |
| KIT-KAT | pcs · 6 | number | pcs | — | med | One bar per shake, so no pack size is needed |
| MARSHMALLOW | pcs · 0 | yes/no | packet | — | med | Garnish |
| MATCHA | pcs · 0 | number | pack | 1 pack = ? g | med | untracked. Expensive, so keep it countable |
| MILK | pcs · 9 | number | packet | 1 packet = 500 ml? | med | History 3, 7, 10, 9 packets. Recipes are in ml, so this needs a pack size |
| NUTELLA | pcs · 0.5 | number | jar | 1 jar = ? g | med | untracked |
| ORANGE JUICE | pcs · 1.5 | number | carton | 1 carton = 1000 ml? | med | |
| OREO | pcs · 2 | number | packet | 1 packet = ? pcs | med | Recipes are probably in biscuits |
| PLAIN SODA | pcs · 6 | number | bottle | 1 bottle = ? ml | med | Skip the pack size if a drink always uses a whole bottle |
| STRAWBERRY ICE CREAM | pcs · 0.5 | number | tub | 1 tub = ? ml | med | untracked |
| SUGAR FREE | pcs · 0.5 | yes/no | box | — | med | Sachets for customers, not costed |
| SUGAR SACHET | pcs · 0.5 | yes/no | box | — | med | untracked |
| VANILLA ICE CREAM. | pcs · 0.5 | number | tub | 1 tub = ? ml | med | untracked. The name has a trailing period |

### CHICKEN & SAUCES (33)

In-house sauces, oils, masalas and mixes become yes/no. Nobody weighs a sauce jar at close.

| Item | Now | Counted as | Unit | Pack size | Conf | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| BAO | pcs · 30 | number | pcs | — | high | |
| BIBIMBAP SAUCE | pcs · 1 | yes/no | — | — | high | |
| CAJUN MASALA | pcs · 1 | yes/no | — | — | med | Possible duplicate of CAJUN MASALA POWDER |
| CAJUN SAUCE | pcs · 1 | yes/no | — | — | high | |
| CHEST BONELESS | pcs · 1000 | number | kg | — | high | **Wrong unit.** Now → 1.0 kg. History 1250, 1400, 1500, 1000 are grams |
| CHI DUMPLINGS | pcs · 30 | number | pcs | — | high | |
| CHICKEN WONTON | pcs · 0 | number | pcs | — | med | untracked |
| CHILLI OIL | pcs · 1 | yes/no | — | — | high | |
| CURRY LEAF SAUCE | pcs · 0 | yes/no | — | — | high | |
| DRAGON SAUCE | pcs · 1 | yes/no | — | — | high | |
| FRY MIX | pcs · 1 | yes/no | — | — | med | If it is a bought premix that matters to cost, count it in kg instead |
| GARLIC MAYO | g · 0 | yes/no | — | — | high | untracked. `g` is meaningless here |
| GREEN CHILLI OIL | g · 0 | yes/no | — | — | high | untracked |
| HOT SAUCE | pcs · 1 | yes/no | — | — | med | If it is bought in bottles, it could be counted as a number |
| KARAGE | pcs · 3 | number | portion? | 1 portion = ? pcs | **LOW** | Threshold 5 against a stock of 3. Pieces or portions like WINGS? |
| KATSU | pcs · 9 | number | pcs | — | med | Cutlets. History 4, 6, 3, 9 |
| KATSU MASALA | pcs · 1 | yes/no | — | — | high | |
| KEEMA CHILLI OIL | pcs · 1 | yes/no | — | — | high | |
| KOREAN SAUCE | pcs · 0 | yes/no | — | — | high | |
| LEG BONELESS | pcs · 2300 | number | kg | — | high | **Wrong unit.** Now → 2.3 kg. Threshold 85 needs resetting |
| LEMON GRASS CHILLI OIL | g · 0 | yes/no | — | — | high | untracked |
| MASTURD MARINATION | pcs · 1 | yes/no | — | — | high | Spelling: MUSTARD |
| NUGGETS | pcs · 7 | number | packet? | 1 packet = ? pcs | **LOW** | 4 to 10 seems low for loose nuggets, so these are probably packets |
| PERI PERI SAUCE | g · 0 | yes/no | — | — | high | untracked |
| SANDWICH SAUCE | pcs · 1 | yes/no | — | — | high | |
| SWEET CHILLI MAYO | g · 0 | yes/no | — | — | high | untracked. The name has a trailing space |
| TIL CHUTNEY | pcs · 1 | yes/no | — | — | med | Same as TOMATO TIL CHUTNEY? |
| TINGMO | pcs · 10 | number | pcs | — | high | |
| TOMATO TIL CHUTNEY | g · 0 | yes/no | — | — | med | untracked |
| VEG DUMPLINGS | pcs · 10 | number | pcs | — | high | |
| VEG WONTON | pcs · 0 | number | pcs | — | med | untracked |
| WAFFLE MIX | pcs · 1 | yes/no | — | — | med | Same caveat as FRY MIX |
| WINGS | pcs · 3 | number | portion | 1 portion = ? pcs | high | Counted in portions, as decided on 2026-09-23. The drop from 16 to 3 suggests old counts were pieces |

### DRY GROCERY (43)

| Item | Now | Counted as | Unit | Pack size | Conf | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| ABC SWEET SOY SAUCE | pcs · 2 | number | bottle | 1 bottle = ? ml | med | untracked. Bought bottles are counted, house sauces are yes/no |
| ARRAROT | pcs · 0 | yes/no | — | — | med | untracked. Arrowroot, used in small amounts |
| BLACK PAPPER POWDER | pcs · 0 | yes/no | — | — | high | Spelling: PEPPER |
| BREAD CRUMB | pcs · 0 | number | packet | 1 packet = ? g | med | Coating for fried items, so it has real cost |
| BUTTER | pcs · 1 | number | pack | 1 pack = 500 g? | med | |
| CAJUN MASALA POWDER | pcs · 1 | yes/no | — | — | **LOW** | Duplicate of CAJUN MASALA? |
| CASHEW (KAJU) | g · 0 | number | kg | — | med | untracked. Threshold 250 g → 0.25 kg |
| CHEESE SLICE | pcs · 0 | number | packet | 1 packet = ? pcs | med | Recipes use slices |
| COCONUT MILK | pcs · 0 | number | tin | 1 tin = ? ml | med | |
| EGGS | pcs · 0 | number | pcs | — | med | If they are billed by the tray, use tray with 1 tray = 30 pcs |
| FRENCH FRIES | kg · 1800 | number | kg | — | med | **Wrong value.** Now → 1.8 kg. Keep this row and merge FRIES into it |
| GOCHUJANG | pcs · 0 | number | tub | 1 tub = ? g | med | History 6, 2, 0 |
| GOTA GOLKI | pcs · 0 | yes/no | — | — | med | untracked. Whole black pepper |
| HONEY | pcs · 0 | number | bottle | 1 bottle = ? g | med | |
| JAPANESE NOODLE (RAMEN NOODLE) | pcs · 31 | merge → RAMEN NOODLES | — | — | high | Same history as RAMEN NOODLES |
| LEMON JUICE | pcs · 0 | yes/no | — | — | med | untracked. The name has a trailing space |
| MAIDA | pcs · 0 | number | kg | — | med | untracked, **not dead**. Bulk flour for batters and bao, so it is costable |
| MAIDA (LOOSE) | pcs · 0 | merge → MAIDA? | — | — | **LOW** | untracked. See duplicates |
| MASTURD KASUNDI | pcs · 0 | yes/no | — | — | high | untracked |
| MAYONNAISE | pcs · 0.5 | number | pack | 1 pack = 1000 g? | med | untracked. The script suggests yes/no, but sandwiches use enough mayo to cost it |
| MIE GORENG NOODLES | pcs · 50 | number | packet | — | high | One packet per dish |
| MIRCH GUNTOOR | pcs · 0.5 | yes/no | — | — | med | Dried chillies |
| MSG | pcs · 0 | yes/no | — | — | high | |
| OYSTER SAUCE | pcs · 1 | number | bottle | 1 bottle = ? ml | med | History 1, 2, 1 |
| PANEER | pcs · 0 | number | kg | — | high | untracked. Billed by weight, perishable, costable |
| PEANUT BUTTER | pcs · 0 | number | jar | 1 jar = ? g | med | untracked |
| PERI PERI MASALA POWDER | pcs · 1 | yes/no | — | — | med | |
| PROCESSED CHEESE | pcs · 10 | number | ? | ? g | **LOW** | 10 blocks, packets or kg? |
| RAMEN NOODLES | pcs · 31 | number | packet | — | high | Keep this row |
| REFINED OIL (TIN) | pcs · 0.5 | number | tin | 1 tin = 15 L? | med | The script suggests yes/no, but frying oil is a major cost, so keep it a number |
| RICE VINEGAR | pcs · 2 | number | bottle | 1 bottle = ? ml | med | |
| SAFED TIL | pcs · 0.5 | yes/no | — | — | med | White sesame |
| SALT | pcs · 0 | yes/no | — | — | high | untracked, **not dead** |
| SOONTH | pcs · 2 | yes/no | — | — | med | Dry ginger powder |
| SOY MILK | pcs · 0 | number | carton | 1 carton = 1000 ml? | med | |
| SUGAR | pcs · 0 | number | kg | — | med | Used in every sweet drink |
| TEZ PATTA | pcs · 0 | yes/no | — | — | high | untracked |
| TOFU | pcs · 0 | number | packet | 1 packet = ? g | med | untracked |
| TOMATO KETCHUP | pcs · 0.5 | number | pack | 1 pack = 1000 g? | med | Heavy use, so count it |
| VEG OYSTER SAUCE | pcs · 1 | number | bottle | 1 bottle = ? ml | med | |
| VEG STOCK CUBE | pcs · 48 | number | pcs | — | high | |
| WALNUT | pcs · 0 | number | kg | — | med | untracked |
| YU NOODLES | pcs · 8 | number | packet | — | high | |

### FRONTIER (8)

FRONTIER looks like a **supplier name used as a category**. Once vendors exist (build step 7),
move these rows into real categories.

| Item | Now | Counted as | Unit | Pack size | Conf | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| BUTTER PAPER | pcs · 1 | yes/no | roll | — | med | |
| COCOA POWDER | g · 1 | merge → COCOA POWDER (#114) | — | — | high | A count stored as grams |
| DARK SOY SAUCE | pcs · 1 | number | bottle | 1 bottle = ? ml | med | |
| DRY YEAST | pcs · 1 | yes/no | — | — | med | If bao is costed, make it a number with 1 packet = ? g |
| FLAT RICE NOODLES | pcs · 1 | number | packet | 1 packet = ? g | med | |
| GLASS NOODLES | pcs · 3 | number | packet | 1 packet = ? g | med | |
| LIGHT SOY SAUCE | pcs · 2 | number | bottle | 1 bottle = ? ml | med | |
| VANILLA ESSENCE | pcs · 1 | yes/no | — | — | high | |

### HOUSE KEEPING (12)

None of these are in recipes. Yes/no is enough: "Out" is what triggers the order.

| Item | Now | Counted as | Unit | Pack size | Conf | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| DISHWASH BAR | pcs · 0 | yes/no | — | — | high | untracked |
| DISHWASH LIQUID | pcs · 0 | yes/no | — | — | high | |
| DISHWASH SCRUB | pcs · 0 | yes/no | — | — | high | untracked |
| GARBAGE BAG L | pcs · 0 | yes/no | — | — | med | untracked, **not dead**. Use a number of packs if "Out" warns too late |
| GARBAGE BAG M | pcs · 0 | yes/no | — | — | med | untracked, **not dead** |
| GARBAGE BAG XL | pcs · 0 | yes/no | — | — | med | untracked, **not dead** |
| GAS CYLINDER | pcs · 0 | number | cylinder | — | high | Knowing whether a spare is on hand matters |
| GLASS CLEANER | pcs · 0 | yes/no | — | — | high | |
| HANDWASH LIQUID | pcs · 0 | yes/no | — | — | high | |
| IRON WOOL | pcs · 0 | yes/no | — | — | high | |
| PHENYL | pcs · 0 | yes/no | — | — | high | |
| SURF | pcs · 0 | yes/no | — | — | high | |

### PACKAGING (16)

The five containers are counted in packs (0.5, 3) but alert at **50**, which is a threshold in
pieces. With that mismatch they are always "low". Pick one unit.

| Item | Now | Counted as | Unit | Pack size | Conf | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 25 ml | pcs · 2 | number | pack | 1 pack = ? pcs | **LOW** | Rename to "CONTAINER 25 ML". Threshold 50 vs stock 2 |
| 100 ml | pcs · 1 | number | pack | 1 pack = ? pcs | **LOW** | Same as above |
| 250 ml | pcs · 0.5 | number | pack | 1 pack = ? pcs | **LOW** | Same as above |
| 500 ml | pcs · 3 | number | pack | 1 pack = ? pcs | **LOW** | Same as above |
| 750 ml | pcs · 3 | number | pack | 1 pack = ? pcs | **LOW** | Same as above |
| M FOLD TISSUE PAPER | pcs · 1 | yes/no | — | — | med | |
| PACKING ENVELOPE (LARGE) | pcs · 1 | number | pack | — | med | |
| PACKING ENVELOPE (MEDIUM) | pcs · 0 | number | pack | — | med | untracked |
| PACKING ENVELOPE (SMALL) | pcs · 1 | number | pack | — | med | |
| PAPER PLATES (MK) | pcs · 1 | number | pack | — | med | |
| POLYBAG | pcs · 0.5 | yes/no | — | — | med | |
| STRAW | pcs · 3 | number | pack | — | med | |
| TAKEAWAY GLASS | pcs · 0.5 | number | pack | 1 pack = ? pcs | med | Needs a pack size only if takeaway drinks are costed |
| TISSUE PAPER | pcs · 30 | number | ? | — | **LOW** | 30 packets or 30 sheets? |
| WOODEN FORK | pcs · 2 | number | pack | — | med | |
| WOODEN SPOON | pcs · 2 | number | pack | — | med | |

### VEGETABLES (33)

Vegetables are billed per kg, so they should be counted in **kg**, not g. Divide today's number
by 1000. Grams keep working in recipes because kg and g convert on their own. Thresholds need
the same division.

| Item | Now | Counted as | Unit | Pack size | Conf | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| AALU | g · 500 | number | kg | — | high | → 0.5 |
| ADRAK | g · 100 | number | kg | — | high | → 0.1 |
| BROCCOLI | g · 0 | number | kg | — | high | Threshold 27 g looks like a typo |
| CABBAGE | g · 400 | number | kg | — | high | → 0.4 |
| CAULI FLOWER | g · 300 | number | kg | — | high | → 0.3 |
| CHICKEN PATTY | g · 9 | number | pcs | — | high | **Wrong unit** (9 patties, not 9 g). Wrong category too |
| CURRY PATTI | g · 40 | yes/no | — | — | **LOW** | Herb, bought by the bunch. Yes/no, or a number in bunches? |
| DHANIYA | g · 100 | yes/no | — | — | **LOW** | Same question as CURRY PATTI |
| FRIES | g · 1800 | merge → FRENCH FRIES | — | — | med | Duplicate |
| GAJAR | g · 500 | number | kg | — | high | → 0.5 |
| GREEN CHILLI | g · 100 | number | kg | — | med | → 0.1 |
| ICEBERG LETTUCE | g · 400 | number | kg | — | med | → 0.4. It could be counted in heads instead |
| KAFFIR LIME LEAVES | g · 0 | yes/no | — | — | med | |
| KHEERA | g · 1000 | number | kg | — | high | → 1.0 |
| KIWI | g · 8 | number | pcs | — | high | **Wrong unit.** 8 kiwis |
| LAHSUN | g · 200 | number | kg | — | high | → 0.2 |
| LEMON | g · 5 | number | pcs | — | high | **Wrong unit.** 5 lemons |
| LEMON GRASS | g · 0 | yes/no | — | — | med | |
| MUSHROOM | g · 0 | number | packet | 1 packet = 200 g? | med | **Wrong unit.** History 1, 0, 2, 0 are packets |
| NAPA CABBAGE | g · 1000 | number | kg | — | high | → 1.0 |
| PAALAK | g · 200 | number | kg | — | med | → 0.2 |
| PEALED GARLIC | g · 500 | number | kg | — | high | → 0.5. Spelling: PEELED |
| PUDINA PATTI | g · 100 | yes/no | — | — | **LOW** | Same question as CURRY PATTI |
| PYAJ | g · 2000 | number | kg | — | high | → 2.0 |
| PYAJ SAAG | g · 750 | number | kg | — | med | → 0.75 |
| RED CAPSICUM | g · 0 | number | kg | — | high | |
| SHIMLA | g · 450 | number | kg | — | high | → 0.45 |
| THAI RED CHILLI | g · 60 | number | kg | — | med | → 0.06 |
| TOMATO | g · 350 | number | kg | — | high | → 0.35 |
| VEG PATTY | g · 0 | number | pcs | — | med | untracked. Patties are counted, not weighed |
| WATERMELON | g · 1 | number | pcs | — | high | **Wrong unit.** 1 melon |
| YELLOW CAPSICUM | g · 0 | number | kg | — | high | |
| ZUCCHINI | g · 300 | number | kg | — | high | → 0.3 |

---

## Already retired (23), for reference

Inactive rows, left untouched: GLASS NOODLES, FLAT RICE NOODLES, DARK SOY SAUCE and LIGHT SOY
SAUCE (old DRY GROCERY rows, since recreated under FRONTIER); REFINED OIL (TIN), TISSUE, TOILET
TISSUE, STRAWS, TAKEAWAY GLASS, BROWN ENVELOPE (L/M/S), PAPER PLATES, WOODEN FORK, WOODEN
SPOON, 750ML, 500ML, 250ML, 100ML, 25ML (old HOUSE KEEPING rows, since recreated under
PACKAGING); COOKIE ×3.
