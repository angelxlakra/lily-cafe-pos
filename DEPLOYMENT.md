# Deployment Guide

## Architecture

```
[Vercel]  — React frontend (static build)
    ↓ VITE_API_BASE_URL
[Fly.io]  — FastAPI backend + SQLite on persistent volume
    ↑ polls every 1s during cafe hours
[agent.py] — Windows PC at cafe → thermal printer
```

---

## 1. Deploy Backend to Fly.io

### First time

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Create app (choose Singapore region: sin)
fly launch --name lily-cafe-pos --region sin --no-deploy

# Create persistent volume for SQLite (1 GB, stays free tier)
fly volumes create lily_cafe_data --size 1 --region sin

# Set secrets — generate strong random values for the keys
fly secrets set \
  SECRET_KEY="$(openssl rand -hex 32)" \
  PRINT_AGENT_API_KEY="$(openssl rand -hex 32)" \
  ADMIN_PASSWORD="your-admin-password" \
  OWNER_PASSWORD="your-owner-password" \
  CORS_ORIGINS="https://your-app.vercel.app"

# Deploy
fly deploy
```

### Subsequent deploys

```bash
# Refuses unless HEAD is a clean origin/main, then verifies the live commit.
./scripts/deploy-backend.sh
```

Don't run a bare `fly deploy` here: it builds from the working directory, so a
stale checkout ships a stale image. See the README's *Deploying the backend*.

### Useful commands

```bash
fly logs                        # Stream live logs
fly ssh console                 # SSH into the machine
fly status                      # App health
```

---

## 2. Deploy Frontend to Vercel

1. Push this repo to GitHub (if not already)
2. Go to [vercel.com](https://vercel.com) → **New Project** → import repo
3. Set **Root Directory** to `frontend`
4. Add environment variable:
   - Key: `VITE_API_BASE_URL`
   - Value: `https://lily-cafe-pos.fly.dev`
5. Click **Deploy**

Every push to `main` will auto-deploy.

---

## 3. Set Up Print Agent (Windows PC at cafe)

```
# 1. Copy the agent/ folder to the cafe PC (USB drive or git clone)

# 2. Run setup — creates virtualenv and installs deps
agent\install-windows.bat

# 3. Edit agent\.env
#    BACKEND_URL=https://lily-cafe-pos.fly.dev
#    AGENT_API_KEY=<same value as PRINT_AGENT_API_KEY on Fly.io>
#    PRINTER_TYPE=usb  (or serial / network / win32)
#    PRINTER_VENDOR_ID / PRINTER_PRODUCT_ID  (run detect_printer.py to find)

# 4. Start
agent\run-agent.bat
```

### Auto-start on Windows boot

1. Press `Win + R` → type `shell:startup` → Enter
2. Create a shortcut to `run-agent.bat` in that folder

The agent will start automatically whenever the PC boots.

### Polling behaviour

| Time | Poll interval | Chit latency |
|------|--------------|--------------|
| 6am – 4pm (cafe hours) | 1 second | < 1 s average |
| 4pm – 6am (overnight) | 30 seconds | — |

Adjust `CAFE_OPEN_HOUR` / `CAFE_CLOSE_HOUR` in `agent/.env` to match your actual hours.

---

## 4. Verify Everything Works

```bash
# Backend health
curl https://lily-cafe-pos.fly.dev/

# Print queue status
curl -H "X-Agent-Key: YOUR_PRINT_AGENT_API_KEY" \
     https://lily-cafe-pos.fly.dev/api/v1/print-jobs/status
```

Place a test order from the tablet — the chit should print within 1–2 seconds.

---

## 5. Connect an AI Assistant (optional)

Lets the owner ask ChatGPT or Gemini questions about the cafe ("what sold
best last week?", "is anything low on stock?"). The backend exposes a
read-only MCP server behind OAuth. It is **off by default** — nothing below
is reachable until you enable it.

What the assistant can do: read sales, menu performance, stock levels and
cash counter records. What it cannot do: change anything. Only the **owner**
login can approve a connection; the admin login is refused.

### 5.1 Enable it on Fly.io

```bash
fly secrets set \
  MCP_ENABLED=true \
  MCP_PUBLIC_URL=https://lily-cafe-pos.fly.dev
```

`MCP_PUBLIC_URL` must be the exact public origin (scheme + host, no path, no
trailing slash). It is the OAuth issuer identifier; requests to any other
hostname are rejected. The backend creates the OAuth tables on next start.

Confirm it is up:

```bash
# OAuth discovery — should return JSON with authorization_endpoint etc.
curl https://lily-cafe-pos.fly.dev/.well-known/oauth-authorization-server

# The data endpoint must refuse anonymous calls (expect HTTP 401)
curl -i -X POST https://lily-cafe-pos.fly.dev/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" -d '{}'
```

### 5.2 ChatGPT

Requires ChatGPT **Pro, Team, Enterprise or Edu** — Developer Mode is not on
Free or Plus. On Team/Enterprise an admin may need to allow it first.

1. ChatGPT → **Settings → Apps & Connectors** → turn on **Developer Mode**
2. **Create** a connector:
   - Name: the cafe's name
   - Server URL: `https://lily-cafe-pos.fly.dev/mcp` — the `/mcp` path is
     required
   - Authentication: **OAuth**
3. ChatGPT registers itself and opens the sign-in page. Sign in with the
   **owner** username and password and click **Approve**.

No client ID or secret is needed; ChatGPT registers automatically.

### 5.3 Gemini

Requires **Gemini Enterprise – Business Edition**, and only a **team
administrator** can add a server (Manage team → Connected apps → Add MCP
Server). Gemini does not register itself: it asks for a client ID and secret
up front, so create one for it first.

**a) Create Gemini's client (once per cafe).** Gemini's fixed callback URL is
`https://vertexaisearch.cloud.google.com/oauth-redirect`:

```bash
curl -s -X POST https://lily-cafe-pos.fly.dev/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Gemini",
    "redirect_uris": ["https://vertexaisearch.cloud.google.com/oauth-redirect"],
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "client_secret_post",
    "scope": "cafe:read"
  }'
```

Copy `client_id` and `client_secret` from the response. The secret is shown
once; treat it like a password.

**b) In Gemini, fill in:**

| Field | Value |
|-------|-------|
| Server URL | `https://lily-cafe-pos.fly.dev/mcp` |
| Name | the cafe's name |
| Authorization URL | `https://lily-cafe-pos.fly.dev/authorize` |
| Token URL | `https://lily-cafe-pos.fly.dev/token` |
| Client ID | from step a |
| Client Secret | from step a |
| Scopes | `cafe:read` |

Then connect: the owner signs in on the consent page and approves.

**Known unknown:** the server requires PKCE (`code_challenge`, S256), which
OAuth 2.1 mandates and ChatGPT sends. Google's documentation does not say
whether Gemini sends it. If Gemini's connection fails at the sign-in step
with `invalid_request`, that is the cause — report it before changing
anything, as relaxing PKCE weakens the flow for every client.

### 5.4 Disconnecting an assistant

Revoke from the assistant's own connector settings, or disable everything
at once:

```bash
fly secrets set MCP_ENABLED=false
```

Existing tokens stop working immediately because the endpoints disappear.
Registrations and tokens stay in the database and resume if re-enabled.

### 5.5 Rotating the owner password

Changing `OWNER_PASSWORD` does **not** disconnect assistants that were already
approved — the password is only checked at approval time, and their tokens
stay valid for up to 30 days (refreshing without a sign-in). To force every
assistant to re-approve, clear the issued tokens:

```bash
fly ssh console -C "python -c \"import sqlite3; c=sqlite3.connect('/data/restaurant.db'); c.execute('DELETE FROM oauth_tokens'); c.commit()\""
```

(`/data/restaurant.db` is the `DATABASE_URL` set in the Dockerfile.)

---

## Printer Detection (USB)

On the cafe PC, find vendor/product IDs:

```bash
cd backend
uv run python detect_printer.py
```

Then set `PRINTER_VENDOR_ID` and `PRINTER_PRODUCT_ID` in `agent/.env`.
