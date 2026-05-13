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
fly deploy
```

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

## Printer Detection (USB)

On the cafe PC, find vendor/product IDs:

```bash
cd backend
uv run python detect_printer.py
```

Then set `PRINTER_VENDOR_ID` and `PRINTER_PRODUCT_ID` in `agent/.env`.
