# Ask v2 — Morning Digest and Anomaly Flags
**Date:** 2026-09-20  
**Status:** Draft — for review

## Problem

Ask v1 answers questions the owner thinks to ask. Most of what matters to a cafe owner is something they *didn't* think to ask: a Tuesday that came in 35% under a normal Tuesday, a dish that quietly stopped selling, cash short three days running. v1 only speaks when spoken to.

v2 makes the system speak first: a short digest every morning, and flags whenever a rule fires. Both are computed by code from the same report registry v1 already has. No new query engine, no model in the loop for numbers.

## The invariant, carried over

The v1 rule stands: **a model never produces a figure.** Every number in a digest or a flag is computed by code. A model may, at most, smooth the phrasing of a sentence whose numbers are already fixed — and v2 ships without even that (templated captions, as in v1). See "Open decisions".

## Scope

**In scope:**
- Daily digest: one message per cafe, at opening time, delivered in-app and by email
- Anomaly rules: a fixed set, evaluated daily, each producing a one-line flag with the numbers behind it
- A "Today" card at the top of the Ask screen showing the latest digest and open flags
- Owner-tunable settings for delivery time, email on/off, and rule thresholds, via the existing settings page
- A script entry point so the digest can be triggered by a scheduler or by hand

**Out of scope:**
- WhatsApp or push delivery (no Business API account; email and in-app cover v2)
- Model-written commentary (v3, opt-in, with the number-check guardrail)
- Weekly/monthly digests (the daily one plus Ask covers it; add only if asked for)
- Any change to the 20 reports or the router

---

## Digest

### Content

Built for the previous trading day, in IST, from reports that already exist:

| Line | Source report | Example |
|------|---------------|---------|
| Revenue vs the same weekday's average | `sales_summary` + `best_days` (last 4 same weekdays) | *Yesterday ₹6,164 from 31 orders — 18% above your usual Saturday.* |
| Top item | `top_items` (yesterday, limit 1) | *Gajar Halwa sold best: 24 portions.* |
| Cash | `cash_counter` (yesterday) | *Cash balanced exactly.* / *Cash was ₹100 short.* |
| Stock | `inventory_status` | *Milk and Paneer are below reorder level.* |
| Open flags | anomaly rules (below) | one line each |
| Month so far | `sales_summary` (this month) | *September so far: ₹83,475 across 372 orders.* |

Lines with nothing to say are omitted (no cash counter recorded → no cash line, not a warning). A digest is 3–6 sentences. Every sentence uses the v1 caption functions (`app/ask/captions.py`) or a new one in the same style, so formatting and rounding match the Ask cards exactly.

"Your usual Saturday" = mean revenue of the last four Saturdays that had any sales. Fewer than two → the comparison clause is dropped rather than computed on noise.

### Delivery

| Channel | How | Notes |
|---------|-----|-------|
| In-app | `GET /api/v1/ask/digest` returns the latest digest; the Ask screen shows it as a "Today" card above the thread | Always on. Owner-only, like Ask. |
| Email | existing `app/utils/email_sender.send_email` (smtplib, settings in `smtp.*`) | On only if `smtp.enabled` and `digest.email_enabled`. Recipient: `digest.email_to`, default `restaurant.email`. |

Email is plain HTML: the same sentences, a heading with the cafe name and date, no charts. Charts are one tap away in Ask.

### Scheduling

There is no scheduler in the app and adding one (APScheduler, Celery) is a new moving part on a single Fly machine. Instead:

- `uv run python -m scripts.send_digest` computes and stores yesterday's digest, sends the email if enabled, and exits.
- Fly runs it on a schedule: `fly machine run . --schedule daily` on a second, tiny machine sharing the volume — or, simpler, a cron-style call to a new `POST /api/v1/ask/digest/run` guarded by `PRINT_AGENT_API_KEY`-style shared secret, hit by any external scheduler (Fly cron, GitHub Actions, the cafe PC's Task Scheduler alongside the print agent).
- Opening time comes from a setting (`digest.send_at`, default `08:00` IST). The trigger just needs to fire after that; the script is idempotent per day (`digest` table has a unique `date`).

**Decision needed:** which trigger. The print agent already runs on the cafe PC 24/7 and polls the backend; adding a once-a-day call there is zero new infrastructure. Recommended.

### Storage

One table, `daily_digest`: `date` (unique), `body_json` (the lines and the numbers behind them), `email_sent_at`, `created_at`. Kept so the in-app card is instant and past digests are queryable later.

---

## Anomaly rules

Evaluated as part of the digest run, against the previous trading day. Each rule is a small function in `app/ask/anomalies.py` returning either nothing or a `Flag(rule, severity, sentence, numbers)`. All thresholds are settings with defaults; all comparisons use at least two weeks of history or stay silent.

| Rule | Fires when | Default threshold | Sentence |
|------|-----------|-------------------|----------|
| `revenue_low` | yesterday < (1 − t) × same-weekday mean | t = 25% | *Saturday came in ₹2,100 (34%) below your usual Saturday.* |
| `revenue_high` | yesterday > (1 + t) × same-weekday mean | t = 40% | *Best Saturday in a month: ₹8,900, 41% above usual.* |
| `cancellations_spike` | cancellations yesterday ≥ 2 × 4-week daily mean and ≥ 3 | — | *5 orders cancelled yesterday, against a usual 1–2.* |
| `cash_short_streak` | variance < 0 for N consecutive closed days | N = 3 | *Cash has closed short three days running: ₹50, ₹100, ₹70.* |
| `cash_not_closed` | yesterday's counter opened but never closed | — | *Yesterday's cash counter was never closed.* |
| `dish_stalled` | a dish with ≥ 1 sale/day over the prior 4 weeks has sold 0 for D days | D = 5 | *Rava Dosa hasn't sold in 5 days; it usually sells 3 a day.* |
| `low_stock` | any item below `min_threshold` | — | *Milk is at 4 litres (reorder at 15).* |
| `aov_shift` | yesterday's average order value differs from 4-week mean by > t | t = 20% | *Average order was ₹180 yesterday, down from a usual ₹230.* |

Severity is just `info` / `warn`; `warn` for the cash and low-stock rules, `info` otherwise. Flags are stored with the digest and shown on the Today card until the next digest replaces them. No acknowledgement workflow in v2.

**What the rules deliberately don't do:** forecast, detect trends over weeks, or compare against last year. Each is "is yesterday odd against the last month". That is what an owner can act on the same morning.

---

## Settings (added to the existing settings page, `digest.*` group)

| Key | Type | Default |
|-----|------|---------|
| `digest.enabled` | bool | `true` |
| `digest.send_at` | string (HH:MM IST) | `08:00` |
| `digest.email_enabled` | bool | `false` |
| `digest.email_to` | string | `` (falls back to `restaurant.email`) |
| `digest.revenue_low_pct` | int | `25` |
| `digest.revenue_high_pct` | int | `40` |
| `digest.cash_short_days` | int | `3` |
| `digest.dish_stalled_days` | int | `5` |

---

## Backend layout

```
app/ask/
  digest.py      build_digest(db, day) -> Digest        # composes lines from reports + captions
  anomalies.py   evaluate(db, day) -> list[Flag]        # the rules above
  captions.py    (+ three new writers: comparison-to-usual, cash streak, stalled dish)
app/models/digest_models.py   DailyDigest
app/api/v1/endpoints/ask.py   GET /ask/digest, POST /ask/digest/run
scripts/send_digest.py
```

Tests: each rule against a seeded 5-week history (fires / doesn't fire / too little history → silent); digest composition on the demo seed; email body is the same sentences as the in-app card.

---

## Open decisions

1. **Trigger:** cafe PC print agent (recommended) vs Fly scheduled machine vs external cron.
2. **Same-weekday baseline window:** 4 weeks (recommended — festival weeks distort longer windows) vs 8.
3. **Should the digest go out on a day with no sales at all** (cafe closed)? Proposed: no digest, no flag — a closed day is not an anomaly. A `closed_days` setting can come later if a cafe has a fixed weekly off.
