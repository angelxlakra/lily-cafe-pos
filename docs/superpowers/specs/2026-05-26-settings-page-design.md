# Settings Page Design
**Date:** 2026-05-26  
**Status:** Approved

## Problem

Many non-secret environment variables were never set on Fly.io, leaving the deployed backend running on defaults (wrong restaurant name, GST rate, etc.). Managing config through Fly.io secrets is error-prone and requires a redeploy to change a value. The solution is to move all non-secret, operator-tunable settings into the database and expose them through an owner-only settings page in the admin UI.

## Scope

**In scope:**
- Backend: new `app_settings` DB table, in-memory cache, CRUD API endpoints
- Backend: slim down `config.py` to secrets only
- Frontend: new Settings page at `/admin/settings` (owner-only)
- Frontend: sidebar nav entry for Settings
- Migration script to create table and seed defaults from current env vars

**Out of scope:**
- Print agent config (stays in agent's local `.env`)
- CORS_ORIGINS (needed at startup before DB is accessible — stays as env var)
- Any secret values (SECRET_KEY, DATABASE_URL, credentials, API keys, SMTP_PASSWORD)

---

## Settings Inventory

### Stay as env vars (secrets / bootstrap)
| Key | Reason |
|-----|--------|
| `SECRET_KEY` | JWT signing — needed before DB is accessible |
| `DATABASE_URL` | Needed to connect to DB |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Used for auth itself |
| `OWNER_USERNAME`, `OWNER_PASSWORD`, `OWNER_PASSWORD_HASH` | Used for auth itself |
| `PRINT_AGENT_API_KEY` | Shared secret |
| `THESYS_API_KEY` | External API key |
| `SMTP_PASSWORD` | Password |
| `CORS_ORIGINS` | Needed at startup before DB is accessible |
| `RESTAURANT_LOGO_PATH` | Local filesystem path — meaningless in a containerised Fly.io deployment; excluded from DB settings |

### Move to DB (non-secrets)
| Key | Type | Default |
|-----|------|---------|
| `restaurant.name` | string | `Lily Cafe by Mary's Kitchen` |
| `restaurant.address_line1` | string | `Shop 123, Main Street` |
| `restaurant.address_line2` | string | `City, State - 123456` |
| `restaurant.phone` | string | `+91-1234567890` |
| `restaurant.email` | string | `info@lilycafe.com` |
| `restaurant.gstin` | string | `29ABCDE1234F1Z5` |
| `restaurant.fssai` | string | `29ABCDE1234F1Z5` |
| `app.max_tables` | int | `15` |
| `app.gst_rate` | float | `5` |
| `app.timezone` | string | `Asia/Kolkata` |
| `app.token_expiry_hours` | int | `24` |
| `receipt.paper_size` | string | `80mm` |
| `receipt.google_review_url` | string | `https://g.page/r/your-business-review` |
| `receipt.feedback_form_url` | string | `https://forms.gle/your-feedback-form` |
| `smtp.enabled` | bool | `false` |
| `smtp.host` | string | `smtp.gmail.com` |
| `smtp.port` | int | `587` |
| `smtp.username` | string | `` |
| `smtp.sender_email` | string | `` |
| `smtp.report_emails` | string | `` (comma-separated) |

---

## Architecture

### Data Layer

**New SQLAlchemy model: `AppSetting`** in `backend/app/models/models.py`

```
app_settings table:
  key        String  PRIMARY KEY   e.g. "restaurant.name"
  value      String  NULLABLE      always stored as text
  updated_at DateTime              auto-updated on write
```

**Migration script:** `backend/scripts/migrate_add_app_settings.py`
- Creates `app_settings` table if it doesn't exist
- Seeds all keys with their current env var values (or hardcoded defaults if env var is unset)
- Idempotent: skips keys that already exist

### Settings Store (Backend)

**New file: `backend/app/core/settings_store.py`**

Module-level cache dict `_cache: dict[str, str]`. Public interface:

```python
def load(db: Session) -> None          # load all rows from DB into _cache
def get(key: str, default: str = "") -> str
def get_int(key: str, default: int) -> int
def get_float(key: str, default: float) -> float
def get_bool(key: str, default: bool) -> bool
def set_many(updates: dict[str, str], db: Session) -> None  # write + reload cache
```

**Startup:** `main.py` lifespan calls `settings_store.load(db)` after DB init. This is the only DB read at boot for settings.

**Per-request reads:** `settings_store.get(...)` reads from the in-memory dict — zero DB queries.

**On save:** `set_many` writes changed rows to `app_settings` then immediately calls `load` to refresh the cache. Changes take effect for all subsequent requests. This works correctly because the Fly.io deployment runs a single backend process with SQLite — no cross-process cache invalidation needed.

### Config.py Changes

`backend/app/core/config.py` is slimmed to secrets and bootstrap values only. All non-secret fields are removed and accessed via `settings_store` instead throughout the codebase.

### API Endpoints

**Router:** added to `backend/app/api/v1/router.py` as `/settings`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/settings` | owner | Returns `{ key: value }` dict for all settings |
| `PUT` | `/api/v1/settings` | owner | Accepts partial `{ key: value }` dict, validates that all keys are known (rejects unknown keys with 400), writes to DB, refreshes cache |

The existing `GET /api/v1/config` (public, used by the frontend for restaurant_name/max_tables/gst_rate) is updated to read from `settings_store` instead of `config.settings`.

### Access Control

- API endpoints check for `owner` role in the JWT (same pattern as analytics endpoint)
- Frontend route uses `<ProtectedRoute requiredRole="owner">`

---

## Frontend

### New Files
- `frontend/src/pages/SettingsPage.tsx` — main settings page
- `frontend/src/api/settings.ts` — TanStack Query hooks (`useSettings`, `useUpdateSettings`)

### Settings Page Layout

Route: `/admin/settings`

Four sections, each with its own Save button (partial updates — touching one section doesn't risk overwriting another):

**Restaurant Info**
- Restaurant name (text)
- Address line 1 (text)
- Address line 2 (text)
- Phone (text)
- Email (text)
- GSTIN (text)
- FSSAI (text)

**App Config**
- Max tables (number input)
- GST rate % (number input, step 0.5)
- Timezone (dropdown — common IANA zones: Asia/Kolkata, America/New_York, Europe/London, UTC, etc.)
- Token expiry hours (number input)

**Receipt**
- Paper size (segmented control: 58mm / 80mm)
- Google review URL (text)
- Feedback form URL (text)

**Email / SMTP**
- Enabled (toggle)
- Host (text)
- Port (number)
- Username (text)
- Sender email (text)
- Report recipients (text, comma-separated, with helper note)

### UX Behaviour
- Page loads all settings via `useSettings()` query on mount
- Each section is a controlled form initialized from the fetched values
- Save button per section calls `PUT /api/v1/settings` with only that section's keys
- `sonner` toast on success ("Settings saved") and on error ("Failed to save")
- Save button shows loading state during mutation
- No optimistic update — wait for server confirmation before showing success

### Sidebar Nav

`frontend/src/components/Sidebar.tsx` — "Settings" nav item added, visible only when user role is `owner`. Placed below Analytics (the other owner-only item).

---

## Migration & Deployment

1. Run migration script on Fly.io: `fly ssh console -C "cd /app && uv run python backend/scripts/migrate_add_app_settings.py"`
2. On first boot with new code, the lifespan hook loads the seeded values from DB
3. Owner logs in → goes to Settings → updates restaurant details, GST rate, etc.
4. Old non-secret env vars can be retired from Fly.io secrets after verifying settings are correct in the DB

---

## Files Changed

### New Files
- `backend/app/models/settings_model.py` — `AppSetting` SQLAlchemy model
- `backend/app/core/settings_store.py` — in-memory cache + DB read/write
- `backend/app/api/v1/endpoints/settings.py` — GET/PUT endpoints
- `backend/scripts/migrate_add_app_settings.py` — migration + seed script
- `frontend/src/pages/SettingsPage.tsx` — settings UI page
- `frontend/src/api/settings.ts` — TanStack Query hooks

### Modified Files
- `backend/app/core/config.py` — remove non-secret fields
- `backend/app/models/models.py` — import `AppSetting` so Base picks it up
- `backend/app/main.py` — call `settings_store.load(db)` in lifespan
- `backend/app/api/v1/router.py` — register `/settings` router
- `backend/app/api/v1/endpoints/config.py` — read from `settings_store`
- `backend/app/schemas/schemas.py` — add settings schemas
- All backend files that currently reference `settings.RESTAURANT_NAME`, `settings.GST_RATE`, etc. — updated to use `settings_store.get(...)`
- `frontend/src/main.tsx` — add `/admin/settings` route
- `frontend/src/components/Sidebar.tsx` — add Settings nav item (owner only)
