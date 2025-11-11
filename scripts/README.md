# Lily Cafe POS - Scripts Directory

This directory contains all the scripts needed to run, update, and maintain the Lily Cafe POS system.

## Quick Start

### For Windows Users

**First Time Setup:**
1. Right-click `windows/setup.bat` and select **"Run as Administrator"**
2. Follow the prompts to configure automatic updates
3. Start the system: Double-click `windows/start.bat`

**Daily Use:**
- **Start POS System:** Double-click `windows/start.bat`
- **Manual Update:** Double-click `windows/update.bat`
- **View Logs:** Double-click `windows/logs.bat`

### For macOS/Linux Users

**First Time Setup:**
```bash
cd scripts/macos
./update.sh
```

**Daily Use:**
```bash
# Start production system
./scripts/macos/start.sh

# Update system
./scripts/macos/update.sh
```

---

## Windows Scripts (`windows/`)

### `start.bat` - Production Launcher
**What it does:**
- Runs pre-flight checks (frontend built, pywin32 installed, database exists)
- Starts backend server on port 8000
- Serves production-built frontend on port 4173
- Opens two terminal windows for easy monitoring

**When to use:** Daily operation after updates are installed

**Requirements:**
- Frontend must be built (run `update.bat` first)
- Backend dependencies installed
- pywin32 installed for printing

---

### `start-dev.bat` - Development Launcher
**What it does:**
- Checks and installs dependencies if missing
- Starts backend with hot-reload
- Starts frontend dev server with hot-reload
- Development mode with detailed errors

**When to use:** Only for developers making code changes

**Features:**
- Auto-installs missing dependencies
- Hot-reload on file changes
- Source maps enabled
- Detailed error messages

---

### `update.bat` - Update System
**What it does:**
1. Checks for updates from GitHub
2. Backs up database before updating
3. Pulls latest code changes
4. Updates backend dependencies
5. **Installs pywin32 for printer support**
6. Updates frontend dependencies
7. **Builds frontend for production**
8. Logs everything to `logs/` folder

**When to use:**
- After developer pushes updates
- When printing stops working (reinstalls pywin32)
- When you see "frontend not built" errors

**Can run:**
- Manually (double-click)
- Automatically via Task Scheduler (configured by `setup.bat`)

---

### `setup.bat` - Initial Setup & Auto-Update Configuration
**What it does:**
1. Configures Windows Task Scheduler for automatic updates
2. Runs initial update to ensure everything works
3. Sets update time (default: 3:00 AM daily)

**When to use:**
- First time setting up on a new computer
- When reinstalling the system
- To change the automatic update time

**Requirements:**
- Must run as Administrator
- Computer should be plugged in at night

---

### `logs.bat` - Log Viewer
**What it does:**
- Shows recent update logs
- Lets you view specific log files
- Helps troubleshoot update issues

**When to use:**
- After an update to verify success
- When debugging update problems
- To check what changed in last update

---

## macOS/Linux Scripts (`macos/`)

### `start.sh` - Production Launcher
Same as Windows `start.bat` but for macOS/Linux

```bash
./scripts/macos/start.sh
```

### `start-dev.sh` - Development Launcher
Same as Windows `start-dev.bat` but for macOS/Linux

```bash
./scripts/macos/start-dev.sh
```

### `update.sh` - Update System
Same as Windows `update.bat` but for macOS/Linux

```bash
./scripts/macos/update.sh
```

**Note:** macOS doesn't have built-in auto-update scheduling. You can set up a cron job if needed.

---

## What Gets Fixed

### Problem 1: Frontend Not Built
**Old behavior:** After pulling updates, frontend runs in dev mode or doesn't work
**New behavior:** `update.bat`/`update.sh` automatically builds frontend for production

### Problem 2: pywin32 Not Installed
**Old behavior:** Had to manually install pywin32 after every update for printing
**New behavior:** `update.bat`/`update.sh` automatically installs pywin32 via `uv sync --extra printer`

### Problem 3: No Pre-flight Checks
**Old behavior:** System starts but fails at runtime
**New behavior:** `start.bat`/`start.sh` checks everything before starting

---

## Deployment Workflow

### For Developers (You):
1. Make code changes
2. Test locally with `start-dev.bat`
3. Commit and push to GitHub
4. Notify clients that update is available

### For Clients:
**Option A - Automatic (Recommended):**
- Nothing! Computer auto-updates at configured time (default 3:00 AM)
- Restart POS system in the morning

**Option B - Manual:**
1. Close POS system
2. Run `scripts/windows/update.bat`
3. Wait for completion
4. Run `scripts/windows/start.bat`

---

## Logs

All update logs are saved to `/logs/` folder:
- Format: `update_YYYYMMDD_HHMMSS.log`
- Keeps last 30 logs automatically
- View with `logs.bat` or any text editor

---

## Troubleshooting

### "Frontend not built" error
**Solution:** Run `update.bat`

### "pywin32 not installed" warning
**Solution:** Run `update.bat` or manually: `cd backend && uv sync --extra printer`

### Update failed
**Solution:**
1. Check `logs/` folder for error details
2. Ensure internet connection is working
3. Ensure Git is installed
4. Check logs with `logs.bat`

### Auto-update not working
**Solution:**
1. Open Task Scheduler (`taskschd.msc`)
2. Look for "Lily Cafe POS Auto Update"
3. Re-run `setup.bat` as Administrator

---

## Directory Structure

```
scripts/
├── README.md (this file)
├── windows/
│   ├── start.bat         # Production launcher
│   ├── start-dev.bat     # Development launcher
│   ├── update.bat        # Update system
│   ├── setup.bat         # Initial setup
│   └── logs.bat          # Log viewer
└── macos/
    ├── start.sh          # Production launcher
    ├── start-dev.sh      # Development launcher
    └── update.sh         # Update system
```

---

## Support

If you encounter issues:
1. Check the logs: `logs.bat` or `logs/` folder
2. Try running update again: `update.bat`
3. Contact your developer with the log file
