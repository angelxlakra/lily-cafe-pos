# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Waiters** take orders table by table on their phones on the cafe floor. They can see table status, start orders, add items and kitchen notes, and view active orders. They cannot bill, cancel orders or edit the menu.
- **Counter admin** stays at the counter and sees only today's data. This person settles bills, records split payments (cash, card, UPI), prints receipts and runs the cash counter and the daily inventory count.
- **Owner** uses both a phone and a desktop and has full access: menu and category master data, bill and payment corrections, order history, analytics, dish-frequency reports, settings, and a read-only MCP connection for asking ChatGPT or Gemini about the business.

Staff are not tech-savvy. The interface has to be obvious and forgiving.

## Product Purpose

Lily Cafe POS replaced paper order-taking at Lily Cafe by Mary's Kitchen, a small-to-medium cafe in India. It tracks every table's running order, produces GST-correct bills and thermal receipts, reconciles cash at close and tracks stock. It is working when the counter settles bills quickly and correctly under a queue, nothing gets lost between waiter, kitchen and counter, and the owner can trust the day's numbers.

## Positioning

The system is built for one cafe's real workflow rather than as a generic POS. A table keeps one open order that grows over the visit and is billed once at the end. Access is split into three levels: waiter, today-only counter, and owner. The daily inventory count and the cash-counter close are shaped around how this cafe already worked, including its old WhatsApp stock templates.

## Operating Context

- **Peak pressure: billing at the counter.** The admin settles bills, splits payments and prints receipts while customers queue. This is the moment the UI must never slow down or confuse.
- Waiters place orders on phones during service. The kitchen receives printed chits with kitchen notes.
- At close, the admin counts cash by denomination and does the daily stock count on a phone, aiming for under 15 minutes.
- The owner checks analytics and history on either a phone or a desktop, at any time of day.
- The business day and all "today" filters use IST.

## Capabilities and Constraints

- Business rules: one active order per table; orders build up over the visit and are billed at the end; prices are whole rupees and quantities are integers; payments can be split across methods.
- GST rate is configurable. When it is 0, GST rows are hidden on receipts.
- Receipts and kitchen chits print on a thermal printer. This is a core, durable requirement.
- Hosting: the backend runs in the cloud on Fly.io (Singapore) and is reachable off-site. The earlier local-only principle is retired. Legacy Windows `.bat` launchers still exist in the repo.
- Security: login is required for the counter, cash and inventory. Master data and bill edits are owner-only. Failed sign-ins are throttled per client IP. The MCP server is read-only and uses OAuth.
- Stack: React + TypeScript + Vite + Tailwind v4 frontend, and a FastAPI + SQLAlchemy + SQLite backend.

## Brand Commitments

- Name: **Lily Cafe by Mary's Kitchen**.
- The minimalist lily logo is binding. Its variants are in `frontend/public/logos/` (`logo.jpg`, `logo-dark.png`, `logo_cream.png`, `lily_logo_white.png`, `Lilycleaned.png`).
- The 2024 coffee-brown/cream palette in `docs/master-project-document.md` is **not** a binding commitment.

## Evidence on Hand

- Real menu and category data: `menu_items.csv`, `categories.csv`.
- Receipt and chit specs: `docs/receipt-design-instructions.md`, `docs/ORDER_CHIT_GUIDE.md`, `docs/chit-preview.html`.
- Payment method icons: `frontend/public/icons/` (cash, card, UPI).
- There are no customer testimonials, sales benchmarks or usage metrics on file. Do not invent them.

## Product Principles

1. **The counter never waits on the software.** Billing speed and correctness outrank everything else.
2. **Obvious over clever.** Every action should be clear to a non-technical staff member on the first try, and mistakes should be recoverable.
3. **Show each role only what it can act on.** Hide controls a role cannot use rather than showing them locked.
4. **Money is exact.** Totals, GST and payment splits must be correct and must match the printed receipt.
5. **Fit the cafe's existing rhythm.** Follow its real habits: table-long orders, end-of-day counts and printed chits.

## Accessibility & Inclusion

- Touch targets must be at least 48px on the phone-first waiter and count screens.
- The UI must stay usable in a busy, bright, one-handed setting.
