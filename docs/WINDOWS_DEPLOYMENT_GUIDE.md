# Windows Deployment Guide - Lily Cafe POS System

Complete guide to deploy and run the POS system on a Windows laptop in your cafe.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [One-Time Setup](#one-time-setup)
3. [Configuration](#configuration)
4. [Running the System](#running-the-system)
5. [Network Setup for Multiple Devices](#network-setup-for-multiple-devices)
6. [Auto-Start on Windows Boot](#auto-start-on-windows-boot)
7. [Daily Operations](#daily-operations)
8. [Backup & Maintenance](#backup--maintenance)
9. [Troubleshooting](#troubleshooting)

---

## 🖥️ System Requirements

### Minimum Hardware
- **OS:** Windows 10/11 (64-bit)
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 10GB free space
- **Network:** WiFi or Ethernet for local network access
- **Display:** 1366x768 or higher

### Software Prerequisites
- Python 3.11 or higher
- Node.js 18+ (for frontend)
- UV package manager
- Git (optional, for updates)

---

## 🚀 One-Time Setup

### Step 1: Install Required Software

#### 1.1 Install Python
1. Download Python 3.11+ from https://www.python.org/downloads/
2. **IMPORTANT:** Check "Add Python to PATH" during installation
3. Verify installation:
   ```powershell
   python --version
   ```

#### 1.2 Install UV Package Manager
Open PowerShell as Administrator and run:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify:
```powershell
uv --version
```

#### 1.3 Install Node.js
1. Download from https://nodejs.org/ (LTS version)
2. Install with default settings
3. Verify:
   ```powershell
   node --version
   npm --version
   ```

### Step 2: Get the Project Files

#### Option A: Using Git (Recommended)
```powershell
cd C:\
git clone https://github.com/yourusername/lily-cafe-pos.git
cd lily-cafe-pos
```

#### Option B: Download ZIP
1. Download the project ZIP file
2. Extract to `C:\lily-cafe-pos`
3. Open PowerShell in that folder

### Step 3: Install Dependencies

#### 3.1 Backend Setup
```powershell
cd C:\lily-cafe-pos\backend
uv sync
```

This will:
- Create a virtual environment (`.venv`)
- Install all Python dependencies
- Take 1-2 minutes first time

#### 3.2 Frontend Setup
```powershell
cd C:\lily-cafe-pos\frontend
npm install
```

This will:
- Install all JavaScript dependencies
- Take 2-3 minutes first time

### Step 4: Initialize Database

```powershell
cd C:\lily-cafe-pos\backend

# Create database and tables
uv run python -c "from app.db.session import Base, engine; Base.metadata.create_all(bind=engine)"

# Add sample menu data (optional)
uv run python scripts/seed_data.py
```

✅ **Setup Complete!** Now let's configure it for your cafe.

---

## ⚙️ Configuration

### Step 1: Create Your Configuration File

```powershell
cd C:\lily-cafe-pos\backend
copy .env.example .env
notepad .env
```

### Step 2: Edit Configuration

Edit the `.env` file with your cafe details:

```env
# ============================================================================
# App Configuration
# ============================================================================
SECRET_KEY=your-super-secret-key-change-this-to-random-string
TOKEN_EXPIRY_HOURS=24
MAX_TABLES=15
GST_RATE=18
TIMEZONE=Asia/Kolkata

# ============================================================================
# Restaurant Details (IMPORTANT: Update these!)
# ============================================================================
RESTAURANT_NAME=Lily Cafe by Mary's Kitchen
RESTAURANT_ADDRESS_LINE1=Shop 123, Main Street
RESTAURANT_ADDRESS_LINE2=City, State - 123456
RESTAURANT_PHONE=+91-1234567890
RESTAURANT_EMAIL=info@lilycafe.com
RESTAURANT_GSTIN=29ABCDE1234F1Z5

# Logo path (optional)
RESTAURANT_LOGO_PATH=C:\lily-cafe-pos\backend\public\logos\logo.png

# ============================================================================
# Receipt Configuration
# ============================================================================
RECEIPT_PAPER_SIZE=80mm
GOOGLE_REVIEW_URL=https://g.page/r/your-business-review
FEEDBACK_FORM_URL=https://forms.gle/your-feedback-form

# ============================================================================
# Admin Credentials (CHANGE THESE!)
# ============================================================================
ADMIN_USERNAME=admin
ADMIN_PASSWORD=ChangeMe@2025

# ============================================================================
# Database
# ============================================================================
DATABASE_URL=sqlite:///./restaurant.db

# ============================================================================
# CORS Origins (Add your network IPs here - see next section)
# ============================================================================
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://192.168.1.100:5173
```

**Important Changes:**
1. Change `SECRET_KEY` to a random string
2. Update all restaurant details
3. Change admin password
4. Add your logo path if you have one
5. Update CORS origins (see network setup section)

---

## 🏃 Running the System

### Method 1: Manual Start (For Testing)

#### Terminal 1: Start Backend
```powershell
cd C:\lily-cafe-pos\backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Terminal 2: Start Frontend
```powershell
cd C:\lily-cafe-pos\frontend
npm run dev -- --host 0.0.0.0
```

**Access Points:**
- **Admin Dashboard:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Method 2: Simple Startup Scripts (Recommended)

#### Create Backend Startup Script
1. Create file: `C:\lily-cafe-pos\start-backend.bat`
2. Add content:
```batch
@echo off
cd C:\lily-cafe-pos\backend
echo Starting Lily Cafe Backend...
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
```

#### Create Frontend Startup Script
1. Create file: `C:\lily-cafe-pos\start-frontend.bat`
2. Add content:
```batch
@echo off
cd C:\lily-cafe-pos\frontend
echo Starting Lily Cafe Frontend...
npm run dev -- --host 0.0.0.0
pause
```

#### Create Combined Startup Script
1. Create file: `C:\lily-cafe-pos\start-cafe-pos.bat`
2. Add content:
```batch
@echo off
echo ====================================
echo Starting Lily Cafe POS System
echo ====================================
echo.

echo Starting Backend...
start "Lily Cafe Backend" cmd /k "cd C:\lily-cafe-pos\backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak > nul

echo Starting Frontend...
start "Lily Cafe Frontend" cmd /k "cd C:\lily-cafe-pos\frontend && npm run dev -- --host 0.0.0.0"

echo.
echo ====================================
echo System is starting...
echo.
echo Backend will be at: http://localhost:8000
echo Frontend will be at: http://localhost:5173
echo.
echo Wait 10 seconds, then open: http://localhost:5173
echo ====================================
pause
```

3. **Create a desktop shortcut** to this file for easy access!

---

## 🌐 Network Setup for Multiple Devices

To access from tablets, phones, and other computers on your cafe network:

### Step 1: Find Your Laptop's IP Address

```powershell
ipconfig
```

Look for "IPv4 Address" under your active network adapter.
Example: `192.168.1.100`

### Step 2: Update CORS Configuration

Edit `C:\lily-cafe-pos\backend\.env`:

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://192.168.1.100:5173,http://192.168.1.100:8000
```

Replace `192.168.1.100` with YOUR laptop's IP address.

### Step 3: Configure Windows Firewall

1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Click "Inbound Rules" → "New Rule"
4. Choose "Port" → Click Next
5. Select "TCP" and enter ports: `8000,5173`
6. Select "Allow the connection"
7. Check all profiles (Domain, Private, Public)
8. Name it "Lily Cafe POS"
9. Click Finish

### Step 4: Access from Other Devices

**On Waiter's Phone/Tablet:**
- Open browser
- Go to: `http://192.168.1.100:5173`
  (Replace with your laptop's IP)

**On Reception Computer:**
- Same URL: `http://192.168.1.100:5173`

### Step 5: Create QR Code for Easy Access

1. Visit: https://www.qr-code-generator.com/
2. Enter your URL: `http://192.168.1.100:5173`
3. Download QR code
4. Print and post in staff area
5. Staff can scan to access POS

---

## 🔄 Auto-Start on Windows Boot

To make the system start automatically when Windows boots:

### Step 1: Create PowerShell Startup Script

Create file: `C:\lily-cafe-pos\auto-start.ps1`

```powershell
# Lily Cafe POS Auto-Start Script
# Wait for network to be ready
Start-Sleep -Seconds 10

# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\lily-cafe-pos\backend; uv run uvicorn app.main:app --host 0.0.0.0 --port 8000" -WindowStyle Minimized

# Wait a bit
Start-Sleep -Seconds 5

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\lily-cafe-pos\frontend; npm run dev -- --host 0.0.0.0" -WindowStyle Minimized

# Open browser after 15 seconds
Start-Sleep -Seconds 15
Start-Process "http://localhost:5173"
```

### Step 2: Add to Windows Startup

#### Option A: Task Scheduler (Recommended)
1. Open "Task Scheduler"
2. Click "Create Task" (not Basic Task)
3. **General tab:**
   - Name: "Lily Cafe POS Auto-Start"
   - Run whether user is logged on or not: No
   - Run with highest privileges: Yes
4. **Triggers tab:**
   - New → Begin the task: At log on
   - Specific user: (your user account)
5. **Actions tab:**
   - New → Action: Start a program
   - Program: `powershell.exe`
   - Arguments: `-ExecutionPolicy Bypass -File "C:\lily-cafe-pos\auto-start.ps1"`
   - Start in: `C:\lily-cafe-pos`
6. Click OK

#### Option B: Startup Folder (Simpler)
1. Press `Win + R`
2. Type: `shell:startup`
3. Create shortcut to `C:\lily-cafe-pos\start-cafe-pos.bat`

---

## 📅 Daily Operations

### Starting Your Day

**If Auto-Start is Enabled:**
1. Turn on laptop
2. Log in to Windows
3. Wait 30 seconds for system to start
4. Open browser to `http://localhost:5173`
5. Log in with admin credentials

**If Manual Start:**
1. Double-click `start-cafe-pos.bat` on desktop
2. Wait 15 seconds
3. Open `http://localhost:5173` in browser
4. Log in

### During Service

- **Waiters:** Use phones/tablets at `http://YOUR-IP:5173`
- **Reception:** Use admin panel on laptop
- Leave both terminal windows open (don't close them!)

### Ending Your Day

1. Complete all orders
2. Generate end-of-day reports (if needed)
3. Close browser
4. Close both terminal windows (Backend & Frontend)
   - Or press `Ctrl+C` in each terminal
5. Shut down laptop normally

---

## 💾 Backup & Maintenance

### Daily Backup (IMPORTANT!)

Your database is at: `C:\lily-cafe-pos\backend\restaurant.db`

**Automated Backup Script:**

Create file: `C:\lily-cafe-pos\backup-database.bat`

```batch
@echo off
echo Creating daily backup...

set BACKUP_DIR=C:\lily-cafe-pos\backups
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%
set DB_FILE=C:\lily-cafe-pos\backend\restaurant.db

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

copy "%DB_FILE%" "%BACKUP_DIR%\restaurant_%TIMESTAMP%.db"

echo Backup created: restaurant_%TIMESTAMP%.db
echo.

REM Keep only last 30 days of backups
forfiles /P "%BACKUP_DIR%" /M *.db /D -30 /C "cmd /c del @path" 2>nul

echo Old backups cleaned up.
pause
```

**Schedule this to run daily:**
1. Use Task Scheduler
2. Trigger: Daily at 11:59 PM
3. Action: Run `backup-database.bat`

### Weekly Maintenance

1. Check disk space
2. Review order history
3. Test backups (restore to test folder)
4. Update menu prices if needed

### Monthly Tasks

1. Update software (if available)
2. Check for Windows updates
3. Review system performance
4. Archive old backups to external drive

---

## 🔧 Troubleshooting

### Backend Won't Start

**Error: "uv: command not found"**
- UV not installed or not in PATH
- Solution: Reinstall UV using PowerShell as Admin

**Error: "Port 8000 is already in use"**
- Another process is using port 8000
- Solution:
  ```powershell
  netstat -ano | findstr :8000
  taskkill /PID <PID_NUMBER> /F
  ```

**Error: "No module named 'app'"**
- Not in correct directory
- Solution: `cd C:\lily-cafe-pos\backend`

### Frontend Won't Start

**Error: "Port 5173 is already in use"**
- Frontend already running
- Solution: Close other terminal or use different port:
  ```powershell
  npm run dev -- --host 0.0.0.0 --port 5174
  ```

**Error: "npm: command not found"**
- Node.js not installed
- Solution: Install Node.js from nodejs.org

### Can't Access from Phone/Tablet

1. **Check laptop's IP address:**
   ```powershell
   ipconfig
   ```

2. **Verify firewall rules** (see Network Setup section)

3. **Ensure devices are on same network**

4. **Test connection:**
   - On phone, ping laptop: Use "Network Analyzer" app
   - Or try: `http://YOUR-LAPTOP-IP:8000/docs`

5. **Check CORS settings** in `.env` file

### Database Issues

**Error: "database is locked"**
- Multiple processes accessing database
- Solution: Close all apps, restart system

**Corrupted database**
- Restore from backup:
  ```powershell
  copy C:\lily-cafe-pos\backups\restaurant_YYYYMMDD.db C:\lily-cafe-pos\backend\restaurant.db
  ```

### Performance Issues

1. **Check CPU/Memory usage** (Task Manager)
2. **Close unnecessary applications**
3. **Restart the system**
4. **Check disk space** (need 2GB minimum free)

### System Crashes

1. Check Windows Event Viewer for errors
2. Review terminal output for error messages
3. Restore database from backup
4. Contact support with error logs

---

## 📞 Quick Reference

### Important Files

| File | Location |
|------|----------|
| Main Config | `C:\lily-cafe-pos\backend\.env` |
| Database | `C:\lily-cafe-pos\backend\restaurant.db` |
| Backups | `C:\lily-cafe-pos\backups\` |
| Logs | Check terminal windows |

### Important Commands

```powershell
# Start backend
cd C:\lily-cafe-pos\backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start frontend
cd C:\lily-cafe-pos\frontend
npm run dev -- --host 0.0.0.0

# Check Python version
python --version

# Check UV version
uv --version

# Check Node version
node --version

# Find your IP
ipconfig

# Backup database
copy C:\lily-cafe-pos\backend\restaurant.db C:\lily-cafe-pos\backups\
```

### Default Login

- **Username:** admin (or whatever you set in `.env`)
- **Password:** (whatever you set in `.env`)

### Support

- Documentation: `C:\lily-cafe-pos\docs\`
- API Docs: http://localhost:8000/docs
- Issues: Contact your developer

---

## ✅ Deployment Checklist

Before going live:

- [ ] Python 3.11+ installed
- [ ] UV installed and working
- [ ] Node.js installed
- [ ] All dependencies installed (`uv sync`, `npm install`)
- [ ] Database initialized
- [ ] `.env` file configured with cafe details
- [ ] Admin password changed
- [ ] Logo added (optional)
- [ ] Firewall configured
- [ ] CORS origins updated with your IP
- [ ] Tested from waiter's phone/tablet
- [ ] Backup script created and tested
- [ ] Auto-start configured (optional)
- [ ] Staff trained on system
- [ ] Emergency contact info ready

---

**You're ready to go! 🎉**

For additional help, refer to other docs in the `/docs` folder or contact your developer.
