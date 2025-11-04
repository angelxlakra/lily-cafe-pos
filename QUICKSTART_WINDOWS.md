# 🚀 Quick Start Guide - Windows

Get Lily Cafe POS running in 10 minutes!

---

## Step 1: Install Requirements (One-time)

### Install Python 3.11+
- Download: https://www.python.org/downloads/
- **✅ Check "Add Python to PATH"** during install
- Verify: Open PowerShell → `python --version`

### Install UV
Open PowerShell as Administrator:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install Node.js
- Download: https://nodejs.org/ (LTS version)
- Verify: `node --version`

---

## Step 2: Setup Project

```powershell
# Navigate to project
cd C:\lily-cafe-pos

# Install backend dependencies
cd backend
uv sync

# Install frontend dependencies
cd ..\frontend
npm install

# Initialize database
cd ..\backend
uv run python -c "from app.db.session import Base, engine; Base.metadata.create_all(bind=engine)"
```

---

## Step 3: Configure

```powershell
# Copy config file
cd C:\lily-cafe-pos\backend
copy .env.example .env

# Edit with Notepad
notepad .env
```

**Minimum changes:**
- Change `ADMIN_PASSWORD`
- Update `RESTAURANT_NAME`
- Update `RESTAURANT_ADDRESS_LINE1` and `LINE2`
- Update `RESTAURANT_PHONE`, `EMAIL`, `GSTIN`

---

## Step 4: Create Startup Script

Create file: `C:\lily-cafe-pos\START.bat`

```batch
@echo off
echo Starting Lily Cafe POS...

start "Backend" cmd /k "cd C:\lily-cafe-pos\backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak > nul
start "Frontend" cmd /k "cd C:\lily-cafe-pos\frontend && npm run dev -- --host 0.0.0.0"

timeout /t 10 /nobreak > nul
start http://localhost:5173

echo System starting... Wait 15 seconds, then open http://localhost:5173
pause
```

---

## Step 5: Run It!

1. Double-click `START.bat`
2. Wait 15 seconds
3. Browser opens automatically
4. Login with your admin credentials

**Done!** 🎉

---

## Access from Phones/Tablets

### Find Your Laptop's IP:
```powershell
ipconfig
```
Look for "IPv4 Address" (e.g., `192.168.1.100`)

### Update Firewall:
1. Open Windows Defender Firewall
2. Advanced settings → Inbound Rules → New Rule
3. Port → TCP → Ports: `8000,5173`
4. Allow connection → Name: "Lily Cafe POS"

### Update CORS in `.env`:
```env
CORS_ORIGINS=http://localhost:5173,http://192.168.1.100:5173
```
(Replace with YOUR IP)

### Access from Phone:
Open browser → `http://192.168.1.100:5173`

---

## Daily Use

**Start:**
- Double-click `START.bat`
- Wait 15 seconds
- Open `http://localhost:5173`

**Stop:**
- Close both terminal windows
- Or press `Ctrl+C` in each

---

## Backup Database (IMPORTANT!)

Database location: `C:\lily-cafe-pos\backend\restaurant.db`

**Daily backup:**
```batch
copy C:\lily-cafe-pos\backend\restaurant.db C:\lily-cafe-pos\backups\restaurant_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db
```

---

## Troubleshooting

**Backend won't start?**
- Check if port 8000 is free
- Make sure you're in `backend` folder

**Frontend won't start?**
- Check if port 5173 is free
- Run `npm install` again

**Can't access from phone?**
- Check firewall rules
- Verify same WiFi network
- Update CORS in `.env`

---

## Full Documentation

See `/docs/WINDOWS_DEPLOYMENT_GUIDE.md` for:
- Auto-start on boot
- Advanced network setup
- Backup automation
- Complete troubleshooting

---

**Need Help?**
- API Docs: http://localhost:8000/docs
- Check `/docs` folder
- Contact your developer
