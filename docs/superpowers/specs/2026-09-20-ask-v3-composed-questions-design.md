# Ask v3 — Composed Questions, Drill-down, and Small Wins
**Date:** 2026-09-20  
**Status:** Draft — for review, after v2

## Problem

v1 answers any question that maps to one of 20 reports. v2 tells the owner things unprompted. What's left is the question that spans two reports — "compare chai and coffee this month against last" — and the follow-through after an answer: tapping into a day, saving a question, sharing a card, setting a target. v3 is that layer, plus the two cheap features held back from v1.

## The invariant, still

**A model never produces a figure.** v3 lets the model do more *deciding* — which reports, in what order, with what parameters — but every number still comes from code, and a model-written sentence is only shown if every number in it can be found in the data it was given.

## Scope

**In scope:**
1. Multi-step questions: the model plans up to three report calls; code runs them and lays them out
2. Drill-down: tap a bar or row → the day or item broken down, via one new report
3. Reorder suggestions from usage velocity
4. Pinned questions, share-as-text, monthly revenue target
5. Voice input and Hindi/Hinglish speech (held from v1)
6. Opt-in model-written insight line with the number-check guardrail
7. Dish synonyms (chai ↔ tea, etc.)

**Out of scope:**
- Free-form SQL or a general "ask anything" mode — the registry stays closed
- Forecasting beyond a linear pace-to-target
- Menu engineering by margin (needs per-dish cost, which the data model lacks)
- Multi-cafe comparisons (each deployment is one cafe)

---

## 1. Multi-step questions

### What changes in the router

The v1 decision is one report. v3 adds an optional `steps` plan:

```json
{ "action": "compose",
  "steps": [
    { "report": "dish_details", "dish": "masala tea",   "period": {"kind": "named", "name": "this_month"} },
    { "report": "dish_details", "dish": "filter coffee", "period": {"kind": "named", "name": "this_month"} },
    { "report": "dish_details", "dish": "masala tea",   "period": {"kind": "named", "name": "last_month"} },
    { "report": "dish_details", "dish": "filter coffee", "period": {"kind": "named", "name": "last_month"} }
  ],
  "layout": "side_by_side" }
```

Constraints enforced in code, not trusted from the model: at most 4 steps; every step is a real report id with valid parameters (the v1 validation runs per step); dishes resolve or the whole question becomes a clarification; total work is bounded (no step may be `period_summary`). `layout` is one of `side_by_side | stacked | table`, chosen by the model from an enum, rendered by fixed components.

### What the owner sees

A compose card: a short templated caption per step, laid out per `layout`, with each step's period label. **No derived comparison numbers** ("chai is up 12%") unless a report already computes them (`compare_periods` does, within its three fixed pairs). If the owner wants a derived comparison the registry doesn't have, the card shows the two figures and lets them read it — that is the honest ceiling of v3.

### Prompt change

A new rule: "If the question needs more than one report, use action=compose with the smallest set of steps that answers it. Never compose to compute a difference; show the parts." Plus two examples. The eval script gets five composed cases.

## 2. Drill-down

One new report, `day_breakdown(day)`: that day's revenue by hour and by category, top 5 items, payment split, and every order's time and amount (no customer names). Renderers pass a `onDrill(date)` callback from `BestDays` bars and the summary's daily chart; tapping sends the question "show me {date}" with the decision pre-filled, so it goes through the same path as any other question and appears in the thread. No new UI concept, just a shortcut into Ask.

Same trick for items: tapping a row in `TopItems` sends "how did {name} do {period_label}".

## 3. Reorder suggestions

New report `reorder_suggestions`: for every stock item, average daily usage over the last 14 days from `InventoryTransaction` (USAGE rows), days of cover = quantity ÷ daily usage, and a suggested quantity to bring cover to 14 days. Items with under 3 days of cover listed first. Purely arithmetic on existing rows; no forecasting.

Caption: *"Milk will run out in about 2 days at current use — order 25 litres to cover two weeks."*

`ponytail:` linear usage; seasonality and lead time per supplier if a cafe asks.

## 4. Small wins

| Feature | Implementation | Cost |
|---------|----------------|------|
| Pin a question | Star on a user message → saved to `localStorage`, shown as a chip above the built-in ones. No backend. | tiny |
| Share | `navigator.share({ text: caption + "\n" + period_label })`; falls back to copy. Text, not an image — an image needs a rasteriser dependency and a phone renders the text better in WhatsApp anyway. | tiny |
| Monthly target | Setting `goal.monthly_revenue` (existing settings page). Ask shows on `sales_summary` for this month: *"₹83,475 of ₹1,50,000 — on pace for ₹1,25,000."* Pace = linear on trading days so far. | small |
| Synonyms | `entities.py` gets a 10-entry map applied before matching: chai↔tea, coffee↔kaapi, paratha↔parantha, … Extend from real misses in the eval. | tiny |

## 5. Voice

Browser `SpeechRecognition` (Chrome on Android, Safari on iOS), `lang` toggle between `en-IN` and `hi-IN`, transcript dropped into the composer for the owner to confirm before sending — never auto-sent. Mic button only rendered when the API exists. No dependency, no server. Needs testing on actual phones; it is the one feature here a desktop browser cannot verify.

## 6. Model-written insight (opt-in)

After a report runs, a second Luna call receives the computed JSON and the caption, and returns one sentence of *observation* — "Weekends are carrying the month; Tuesday was the weak spot." Rules in the prompt: restate only, no arithmetic, no advice. Then the guardrail, in code:

```
numbers_in(sentence) ⊆ numbers_in(data)   else discard the sentence
```

where `numbers_in` extracts every integer/decimal (₹ and % stripped, Indian grouping removed). A sentence that fails is silently replaced by nothing — the template caption is already there. Toggle: `ask.insights_enabled`, default off. Cost about ₹0.02 per question on top of the router call.

This is the only place in the product where a model writes prose the owner reads as fact, and it is fenced on both sides: it cannot introduce a number, and it is optional.

---

## Sequencing

1. Synonyms + pinned questions + share (a day, no risk, immediately visible)
2. Drill-down + `day_breakdown` (adds the "tap to go deeper" feel)
3. Target + reorder (two new reports, both plain arithmetic)
4. Voice (needs phone testing time more than code)
5. Multi-step compose (the largest change to the router; ship last, with its own eval cases)
6. Insight line (last, opt-in, once everything else is trusted)

## Open decisions

1. Compose ceiling: is "show the parts, no derived comparison" acceptable, or should the registry grow a general `compare_two_periods(report, a, b)` that computes deltas in code? The latter is safe and about a day's work; it would make "chai this month vs last" a single deterministic report and shrink compose to rarer cases. Recommended.
2. Insight line default: off (recommended) or on with a visible "AI" label.
3. Voice languages: `hi-IN` recognises Hindi script well and Hinglish poorly; `en-IN` the reverse. Two buttons, or one auto-detect that tries both? Start with two.
