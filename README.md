# Lily Cafe POS

A Point of Sale system for Lily Cafe by Mary's Kitchen — order taking, billing,
thermal-printed kitchen chits and receipts, inventory, daily cash counting, and
analytics you can ask questions about in plain language.

**Version 0.2.0** · [Changelog](CHANGELOG.md) · [Deployment guide](DEPLOYMENT.md)

## Features

### Orders and billing
- Table-based order management, one active order per table
- Mobile-friendly waiter interface with a cart drawer
- Partial serving — track what has gone out and what has not
- Split payments across UPI, Cash and Card, editable after the fact
- GST-compliant billing with a CGST/SGST split; the rate is configurable
  (5% by default) and set by the owner on the Settings page
- 80mm thermal receipts and automatic kitchen order chits
- Order history with per-day revenue

### Inventory
- Inventory items and categories with unit tracking and low-stock thresholds
- Mobile daily count screen designed for an end-of-day stock walk
- Purchase recording, usage recording, and a transaction ledger
- One-time bulk import from the cafe's old WhatsApp checklist format

A rework of inventory, dish costing and purchases is in design:
[docs/INVENTORY_PLAN.md](docs/INVENTORY_PLAN.md).

### Cash counter
- Open, close and verify a day's cash drawer
- Denomination-level counting
- Owner-password verification, with a history view

### Analytics and Ask
- Revenue, product performance, category performance and payment trends
- Peak-hour and day-of-week analysis, heatmaps, order-flow and waterfall charts
- **Ask** — questions in English, Hindi or Hinglish ("kal ka cash counter",
  "which dish performed best since August") answered by fixed reports. The model
  only chooses which report and which period; every figure is computed by the
  backend. See [ANALYTICS_SETUP.md](ANALYTICS_SETUP.md).

### Administration
- Owner-only Settings page: restaurant details, GST rate, table count,
  timezone, receipt options, SMTP
- JWT authentication with separate admin and owner roles
- Optional read-only MCP server so the owner can connect ChatGPT or Gemini
  (off by default — see [DEPLOYMENT.md](DEPLOYMENT.md) section 5)

## Tech Stack

**Backend** — Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic V2, SQLite, `uv`

**Frontend** — Vite, React 18, TypeScript, Tailwind CSS v4, React Router,
TanStack Query, Recharts, Axios

**Deployment** — Fly.io (backend + SQLite on a persistent volume), Vercel
(frontend), and a Python print agent on the cafe's Windows PC

## Prerequisites

- **Python 3.11 or higher** — [Download](https://www.python.org/downloads/)
- **Node.js 18 or higher** — [Download](https://nodejs.org/)
- **uv** — Python package manager

  ```bash
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Windows
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

## Quick Start

### 1. Clone and configure

```bash
cd lily-cafe-pos

# Copy environment variables
cp .env.example .env
```

`.env` holds secrets and bootstrap values only. Restaurant details, the GST
rate, table count and timezone live in the database and are edited on the
Settings page — see the comments at the top of `.env.example`.

### 2. Backend

```bash
cd backend

# Install dependencies (creates .venv automatically)
uv sync

# Initialize database and seed sample data
uv run python -m scripts.seed_data

# Start the backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API at `http://localhost:8000`, interactive docs at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend at `http://localhost:5173`.

### 4. Or use the start scripts

```bash
# macOS/Linux — runs both
./scripts/macos/start-dev.sh
```

```bat
REM Windows — runs both with hot reload
scripts\windows\start-dev.bat
```

See [scripts/README.md](scripts/README.md) for the full set.

## Accessing from Mobile Devices

1. Find your computer's local IP address:

   ```bash
   # macOS
   ipconfig getifaddr en0

   # Linux
   ip addr show | grep "inet "
   ```

2. Add it to `CORS_ORIGINS` in `.env`:

   ```
   CORS_ORIGINS=http://localhost:5173,http://192.168.1.100:5173
   ```

3. Open `http://192.168.1.100:5173` on the phone.

## Development Commands

### Backend

```bash
uv sync                                   # Install dependencies
uv add package-name                       # Add a dependency
uv run uvicorn app.main:app --reload      # Run the server
uv run python -m scripts.seed_data        # Seed sample data
uv run pytest                             # Run the test suite
uv run pytest tests/test_orders.py        # Run one file
uv run black .                            # Format
uv run ruff check .                       # Lint
```

Always use `uv run` rather than activating the virtualenv — see
[docs/UV-QUICK-REFERENCE.md](docs/UV-QUICK-REFERENCE.md).

### Frontend

```bash
npm install        # Install dependencies
npm run dev        # Dev server
npm run build      # Production build
npm run preview    # Preview the production build
npm run lint       # Lint
```

## Project Structure

```
lily-cafe-pos/
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── api/v1/endpoints/     # Route handlers — orders, menu, categories,
│   │   │                         #   auth, admin, config, inventory,
│   │   │                         #   cash_counter, analytics, print_jobs,
│   │   │                         #   settings, ask
│   │   ├── ask/                  # Ask: report registry, periods, entities, LLM router
│   │   ├── mcp/                  # Read-only MCP server + OAuth (opt-in)
│   │   ├── core/                 # config, security, settings_store, login_throttle
│   │   ├── db/                   # Session and base
│   │   ├── models/               # SQLAlchemy models (orders, inventory, cash,
│   │   │                         #   settings, print jobs, oauth)
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── crud/                 # Database operations
│   │   ├── utils/                # Printer and receipt rendering
│   │   ├── version.py
│   │   └── main.py               # App entry point
│   ├── scripts/                  # Seeding, migrations, backup, Ask eval
│   ├── tests/                    # pytest suite
│   ├── Dockerfile                # Fly.io image
│   └── pyproject.toml
│
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/           # Shared components (+ analytics/, ask/,
│   │   │                         #   inventory/, icons/, ui/)
│   │   ├── pages/                # Order, tables, admin, analytics, inventory,
│   │   │                         #   cash counter, settings, login
│   │   ├── api/                  # client.ts + analytics, ask, cash, inventory,
│   │   │                         #   settings
│   │   ├── contexts/ · hooks/ · types/ · utils/
│   │   ├── App.tsx · main.tsx · index.css · version.ts
│   ├── package.json · vite.config.ts · tsconfig.json · vercel.json
│
├── agent/                        # Windows print agent (polls for print jobs)
├── scripts/                      # Start/update/log scripts (windows/, macos/)
├── docs/                         # Guides, specs, and docs/history/ for
│                                 #   point-in-time records
├── .env.example
├── fly.toml
├── ANALYTICS_SETUP.md · DEPLOYMENT.md · CHANGELOG.md
└── README.md                     # This file
```

## Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `changeme123` |
| Owner | `owner` | `owner123` |

**Change both in production** by setting `ADMIN_PASSWORD`, `OWNER_PASSWORD` and
`OWNER_PASSWORD_HASH` in `.env`. The owner role is required for the Settings
page, cash counter verification, Ask and the MCP connection.

## Database

SQLite. Locally the file is `backend/restaurant.db`; on Fly.io it is
`/data/restaurant.db` on a persistent volume.

### Tables

| Area | Tables |
|------|--------|
| Menu | `categories`, `menu_items` |
| Orders | `orders`, `order_items`, `payments` |
| Inventory | `inventory_categories`, `inventory_items`, `inventory_transactions` |
| Cash | `daily_cash_counter` |
| Settings | `app_settings` |
| Printing | `print_jobs` |
| MCP OAuth | `oauth_clients`, `oauth_tokens`, `oauth_authorization_codes`, `oauth_pending_authorizations` |

Migrations are plain scripts in `backend/scripts/` — see
[backend/scripts/README_MIGRATIONS.md](backend/scripts/README_MIGRATIONS.md).
Backups: [docs/DATABASE_BACKUP_AND_SYNC.md](docs/DATABASE_BACKUP_AND_SYNC.md).

## Design System

Colors are CSS custom properties in `frontend/src/index.css`, with a dark-mode
set alongside them.

| Token | Light | Purpose |
|-------|-------|---------|
| `--color-coffee-brown` | `#6F4E37` | Primary brand |
| `--color-coffee-dark` | `#4A3728` | Hover states |
| `--color-coffee-light` | `#A0826D` | Accents |
| `--color-cream` | `#F5E6D3` | Backgrounds |
| `--color-lily-green` | `#8B9D83` | Secondary brand |

**Typography** — Inter, system-ui, sans-serif. Touch targets are a minimum of
48px for mobile use.

## API Documentation

With the backend running:

- **Swagger UI** — `http://localhost:8000/docs`
- **ReDoc** — `http://localhost:8000/redoc`

The auto-generated docs are the authoritative reference for all ~75 endpoints.
[docs/API_REFERENCE_CARD.md](docs/API_REFERENCE_CARD.md) is a hand-written card
covering the core order and menu routes only.

Route groups: `/api/v1/` + `auth`, `categories`, `menu`, `orders`, `admin`,
`config`, `inventory`, `cash-counter`, `analytics`, `print-jobs`, `settings`,
`ask`.

## Security Notes

- All amounts are stored in paise to avoid float precision issues
- JWT tokens expire after 24 hours (configurable on the Settings page)
- Separate admin and owner roles; owner is required for financial screens
- Repeated failed logins lock out a source address
  (`LOGIN_MAX_FAILURES` / `LOGIN_FAILURE_WINDOW_MINUTES`)
- The MCP server is off unless `MCP_ENABLED=true`, is read-only, and only the
  owner login can approve a connection

## Troubleshooting

### Backend won't start

- Check Python 3.11+: `python --version`
- Check port 8000 is free: `lsof -i :8000`
- Check uv is installed: `uv --version`
- Try `uv sync --reinstall`

### Frontend won't start

- Check Node 18+: `node --version`
- `rm -rf node_modules && npm install`
- Check port 5173 is free: `lsof -i :5173`

### Database issues

```bash
cd backend
rm restaurant.db
uv run python -m scripts.seed_data
```

### Printing

Kitchen chits and receipts print through the agent on the cafe PC, not the
backend. See [docs/AUTO_PRINT_SETUP_GUIDE.md](docs/AUTO_PRINT_SETUP_GUIDE.md)
and [docs/ORDER_CHIT_GUIDE.md](docs/ORDER_CHIT_GUIDE.md).

## Deploying the backend

There are two Fly apps, each fed by one branch:

| Target | Branch | Fly app | URL | Frontend |
|--------|--------|---------|-----|----------|
| `dev` (staging) | `pre-release` | `lily-cafe-pos-dev` | https://lily-cafe-pos-dev.fly.dev | Vercel previews |
| `prod` | `main` | `lily-cafe-pos` | https://lily-cafe-pos.fly.dev | Vercel production |

Each has its own volume and data. Always deploy with the script, never with a bare
`flyctl deploy`, and always name the target — there is no default:

```bash
git checkout pre-release && git pull --ff-only
./scripts/deploy-backend.sh dev          # staging

git checkout main && git pull --ff-only
./scripts/deploy-backend.sh prod         # production
```

Add `--dry-run` to run every guard and print the target, app, SHA and URL without
calling `flyctl`.

**The flow is `pre-release` → dev → `main` → production.** Land work on `pre-release`,
deploy it to dev, test it end to end through a Vercel preview, then merge
`pre-release` into `main` and deploy prod from `main`. Production can only ever
receive a commit that is on `origin/main`.

`flyctl deploy` builds whatever is on disk, not what is in git, so a checkout one
commit behind ships a stale image while the release, health check, and traffic all
report success. That is as true of dev as of prod, and "we tested it on dev" means
nothing if dev was running something else. The script:

1. **Refuses** unless `HEAD` equals the target's branch on origin (`origin/main` for
   prod, `origin/pre-release` for dev; it fetches first) and no tracked file is
   modified or staged. Untracked files don't block — outside `backend/` they never
   reach the image — but untracked files under `backend/` are listed as a warning,
   because they can ship.
2. **Supplies** what is easy to forget: `-a <app>` for both targets (the committed
   `fly.toml` names the dev app, so its app name is never trusted) and
   `--build-arg GIT_SHA=$(git rev-parse HEAD)`.
3. **Verifies** by polling the target's `GET /` until its `commit` field equals the
   deployed SHA, and exits non-zero with `DEPLOY NOT VERIFIED` if it never does. A
   deploy that reports success without shipping is exactly the failure this exists
   to catch.

To check by hand what each app is running:
`curl -s https://lily-cafe-pos.fly.dev/ | grep -o '"commit": *"[^"]*"'` (swap in
`lily-cafe-pos-dev` for staging). First-time setup (app, volume, secrets) is in
[DEPLOYMENT.md](DEPLOYMENT.md).

## Documentation

| Topic | Document |
|-------|----------|
| Deploying | [DEPLOYMENT.md](DEPLOYMENT.md) |
| Analytics and Ask | [ANALYTICS_SETUP.md](ANALYTICS_SETUP.md) |
| Release history | [CHANGELOG.md](CHANGELOG.md) |
| Start/update scripts | [scripts/README.md](scripts/README.md) |
| Database migrations | [backend/scripts/README_MIGRATIONS.md](backend/scripts/README_MIGRATIONS.md) |
| Backups | [docs/DATABASE_BACKUP_AND_SYNC.md](docs/DATABASE_BACKUP_AND_SYNC.md) |
| Printing setup | [docs/AUTO_PRINT_SETUP_GUIDE.md](docs/AUTO_PRINT_SETUP_GUIDE.md) |
| Kitchen chits | [docs/ORDER_CHIT_GUIDE.md](docs/ORDER_CHIT_GUIDE.md) |
| Git workflow | [docs/GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md) |
| uv usage | [docs/UV-QUICK-REFERENCE.md](docs/UV-QUICK-REFERENCE.md) |
| Versioning | [docs/VERSION_MANAGEMENT.md](docs/VERSION_MANAGEMENT.md) |
| Project background | [docs/master-project-document.md](docs/master-project-document.md) |

Point-in-time records — release checklists, implementation reports, UX analyses
— live in [docs/history/](docs/history/). They describe the state of the project
on the day they were written and are not maintained.

## Contributing

This is a private project for Lily Cafe. For questions or issues, contact the
development team.

---

Built for Lily Cafe by Mary's Kitchen
