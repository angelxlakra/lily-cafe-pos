# Migration Guide: v0.1.x → v0.2.0

**Last Updated:** 2025-12-30
**Estimated Time:** 15-20 minutes
**Downtime Required:** 5-10 minutes

---

## Overview

Version 0.2.0 introduces inventory management and cash counter systems, requiring database schema changes. This guide provides step-by-step instructions for migrating from any v0.1.x version to v0.2.0.

**What's New:**
- 📦 Inventory management with WhatsApp import
- 📱 Mobile-optimized Daily Count UI
- 💰 Cash counter with variance tracking
- 🔍 Transaction audit trail
- ⚠️ Low stock alerts

**Database Changes:**
- 4 new tables added
- No changes to existing tables
- Fully backward compatible

---

## Pre-Migration Checklist

Before starting, ensure you have:

- [ ] Administrator access to the server
- [ ] Backend running Python 3.11+
- [ ] `uv` package manager installed
- [ ] Node.js 18+ and npm installed
- [ ] Git access to pull latest code
- [ ] **At least 30 minutes** of maintenance time
- [ ] Communication plan for staff during downtime

---

## Step 1: Backup Current System

### 1.1 Backup Database

**Critical:** Always backup before migration!

```bash
# Navigate to project directory
cd /path/to/lily-cafe-pos

# Create backup with timestamp
cp backend/restaurant.db backend/restaurant_pre_v0.2.0_$(date +%Y%m%d_%H%M%S).db

# Verify backup was created
ls -lh backend/restaurant_pre_v0.2.0_*.db
```

**Store backup safely:** Copy to external location if possible.

### 1.2 Backup Configuration Files

```bash
# Backup .env file
cp backend/.env backend/.env.backup

# Backup any custom configs
cp frontend/.env.local frontend/.env.local.backup 2>/dev/null || true
```

### 1.3 Document Current State

```bash
# Check current version
cd backend
uv run python -c "from app.version import __version__; print(f'Current version: {__version__}')"

# Count existing data
uv run python -c "
from app.db.session import SessionLocal
from app.models.models import Order, MenuItem, Category
db = SessionLocal()
print(f'Orders: {db.query(Order).count()}')
print(f'Menu Items: {db.query(MenuItem).count()}')
print(f'Categories: {db.query(Category).count()}')
db.close()
"
```

---

## Step 2: Stop Running Services

### 2.1 Stop Backend

```bash
# If running as a service
sudo systemctl stop lily-cafe-backend

# If running in terminal (Ctrl+C)
# Or find and kill process
ps aux | grep uvicorn
kill <PID>
```

### 2.2 Stop Frontend

```bash
# If running as a service
sudo systemctl stop lily-cafe-frontend

# If running in terminal (Ctrl+C)
# Or if using nginx/apache, no action needed for static files
```

**Downtime starts here** ⏱️

---

## Step 3: Update Code

### 3.1 Fetch Latest Code

```bash
cd /path/to/lily-cafe-pos

# Fetch latest changes
git fetch origin

# Check current branch
git branch

# If on main branch
git checkout main
git pull origin main

# Checkout v0.2.0 tag
git checkout v0.2.0

# Verify version
git log -1 --oneline
```

### 3.2 Review Changes (Optional)

```bash
# See what changed since your current version
git log v0.1.2..v0.2.0 --oneline --graph
```

---

## Step 4: Update Backend

### 4.1 Install Dependencies

```bash
cd backend

# Sync dependencies with uv
uv sync

# Verify installation
uv run python --version  # Should be 3.11+
```

### 4.2 Run Database Migration

**Critical Step:** This creates the new tables.

```bash
# Run migration script
uv run python scripts/migrate_v02_add_inventory_and_cash_tables.py
```

**Expected output:**
```
✅ Migration started: v0.2.0 - Inventory & Cash Counter Tables

Creating tables:
  - inventory_categories
  - inventory_items
  - inventory_transactions
  - daily_cash_counter

✅ All tables created successfully!

Migration completed successfully!
```

**If migration fails:**
- Check error message carefully
- Verify database file path
- Ensure no other process is accessing the database
- Restore from backup and investigate

### 4.3 Verify Database Changes

```bash
# Check that new tables exist
uv run python -c "
from sqlalchemy import inspect
from app.db.session import engine

inspector = inspect(engine)
tables = inspector.get_table_names()

print('Database tables:')
for table in sorted(tables):
    print(f'  - {table}')

# Check for new v0.2.0 tables
expected = ['inventory_categories', 'inventory_items', 'inventory_transactions', 'daily_cash_counter']
for table in expected:
    if table in tables:
        print(f'✅ {table} exists')
    else:
        print(f'❌ {table} MISSING!')
"
```

**Expected output should show all 4 new tables exist.**

---

## Step 5: Update Frontend

### 5.1 Install Dependencies

```bash
cd ../frontend

# Install new dependencies
npm install

# Verify installation
npm list | grep -E "(react-query|phosphor-icons)"
```

### 5.2 Build Frontend

```bash
# Build production bundle
npm run build

# Verify build succeeded
ls -lh dist/
```

**Expected:** `dist/` directory should contain compiled assets.

**If build fails:**
- Check error messages for missing dependencies
- Try `rm -rf node_modules && npm install` to clean install
- Verify Node.js version: `node --version` (should be 18+)

---

## Step 6: Restart Services

### 6.1 Start Backend

```bash
cd ../backend

# If using systemd
sudo systemctl start lily-cafe-backend
sudo systemctl status lily-cafe-backend

# Or start manually
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Verify backend is running:**
```bash
curl http://localhost:8000/api/v1/config
```

Should return JSON with restaurant configuration.

### 6.2 Start Frontend

```bash
# If using nginx/apache, reload configuration
sudo systemctl reload nginx

# If using Vite dev server
cd frontend
npm run dev

# If using systemd
sudo systemctl start lily-cafe-frontend
```

**Downtime ends here** ⏱️ (~5-10 minutes total)

---

## Step 7: Verify Migration

### 7.1 Check Backend API

```bash
# Check version endpoint
curl http://localhost:8000/api/v1/config | grep version

# Check new inventory endpoints
curl http://localhost:8000/api/v1/inventory/categories
curl http://localhost:8000/api/v1/inventory/items

# Check cash counter endpoint
curl http://localhost:8000/api/v1/cash-counter/today
```

All should return valid JSON responses (empty arrays are OK).

### 7.2 Check Frontend

Open browser and navigate to your POS application:

**Test Existing Features (Regression Check):**
- [ ] Admin login works
- [ ] Menu items display correctly
- [ ] Can create a new order
- [ ] Order payment works
- [ ] Receipt prints correctly (if printer configured)
- [ ] Dark mode toggle works

**Test New Features:**
- [ ] Navigate to "Inventory" in admin sidebar
- [ ] Can access Daily Count tab
- [ ] Can access Cash Counter page
- [ ] WhatsApp import modal appears
- [ ] No console errors in browser devtools

### 7.3 Verify Data Integrity

```bash
cd backend

# Check existing data is intact
uv run python -c "
from app.db.session import SessionLocal
from app.models.models import Order, MenuItem, Category
from app.models.inventory_models import InventoryCategory, InventoryItem
from app.models.cash_models import DailyCashCounter

db = SessionLocal()

print('Existing Data (should be unchanged):')
print(f'  Orders: {db.query(Order).count()}')
print(f'  Menu Items: {db.query(MenuItem).count()}')
print(f'  Categories: {db.query(Category).count()}')

print('\\nNew Tables (should be 0):')
print(f'  Inventory Categories: {db.query(InventoryCategory).count()}')
print(f'  Inventory Items: {db.query(InventoryItem).count()}')
print(f'  Cash Counters: {db.query(DailyCashCounter).count()}')

db.close()
"
```

**Expected:** Existing data counts match pre-migration, new tables are empty.

---

## Step 8: Initial Setup (Optional)

### 8.1 Import Inventory from WhatsApp Template

If you have an existing WhatsApp inventory template:

1. Navigate to **Inventory** page in admin panel
2. Click **Import from WhatsApp** button
3. Paste your WhatsApp template text
4. Click **Parse Template**
5. Review parsed items in preview
6. Click **Import X Items**
7. Verify items and categories were created

### 8.2 Set Up Cash Counter

1. Navigate to **Cash Counter** page in admin panel
2. Click **Open Counter**
3. Enter opening balance (e.g., 1000)
4. Click **Open**
5. Verify counter is now open

---

## Rollback Procedure

If you encounter critical issues after migration:

### Quick Rollback

```bash
cd /path/to/lily-cafe-pos

# Stop services
sudo systemctl stop lily-cafe-backend lily-cafe-frontend

# Restore database backup
cp backend/restaurant_pre_v0.2.0_YYYYMMDD_HHMMSS.db backend/restaurant.db

# Checkout previous version
git checkout v0.1.2

# Reinstall dependencies
cd backend && uv sync
cd ../frontend && npm install && npm run build

# Restart services
sudo systemctl start lily-cafe-backend lily-cafe-frontend
```

**Total rollback time:** ~5 minutes

---

## Troubleshooting

### Migration Script Fails

**Problem:** `migrate_v02_add_inventory_and_cash_tables.py` returns error

**Solutions:**
1. Check database file exists: `ls -l backend/restaurant.db`
2. Ensure no other process is using database: `lsof backend/restaurant.db`
3. Verify database isn't corrupted: `sqlite3 backend/restaurant.db "PRAGMA integrity_check;"`
4. Check Python environment: `uv run python --version`

### Backend Won't Start

**Problem:** `uvicorn` crashes on startup

**Solutions:**
1. Check logs: `journalctl -u lily-cafe-backend -n 50`
2. Verify all tables exist (Step 4.3)
3. Check for syntax errors: `uv run python -m app.main`
4. Verify dependencies: `uv sync --verify`

### Frontend Build Fails

**Problem:** `npm run build` returns errors

**Solutions:**
1. Clear node_modules: `rm -rf node_modules package-lock.json && npm install`
2. Check Node version: `node --version` (need 18+)
3. Check for TypeScript errors: `npx tsc --noEmit`
4. Try clean build: `rm -rf dist && npm run build`

### New Tables Don't Appear

**Problem:** Inventory/Cash Counter pages return 404 or errors

**Solutions:**
1. Verify migration ran successfully (Step 4.2)
2. Check backend logs for errors
3. Manually verify tables exist: `sqlite3 backend/restaurant.db ".tables"`
4. Re-run migration script (it's idempotent)

### Data is Missing

**Problem:** Orders or menu items disappeared

**Solutions:**
1. **CRITICAL:** Restore from backup immediately
2. Migration should never delete existing data
3. Report issue with logs before attempting migration again

---

## Post-Migration Tasks

### Update Documentation

- [ ] Update internal wiki with new features
- [ ] Train staff on inventory management
- [ ] Train staff on daily count workflow
- [ ] Document WhatsApp template format for future use

### Configure Settings

- [ ] Set min_threshold for each inventory item
- [ ] Configure cash counter verification password
- [ ] Set up low stock alert preferences
- [ ] Review and adjust GST settings if needed

### Monitor System

**First 24 Hours:**
- Check backend logs hourly: `tail -f /path/to/logs/backend.log`
- Monitor error rates in API
- Collect user feedback on new features
- Watch for any performance issues

**First Week:**
- Track inventory accuracy
- Monitor cash counter variance trends
- Ensure daily counts are completed
- Address any usability issues

---

## Support

### Getting Help

If you encounter issues during migration:

1. **Check logs:**
   ```bash
   # Backend logs
   tail -f backend/logs/*.log

   # System logs (if using systemd)
   journalctl -u lily-cafe-backend -f
   ```

2. **Check browser console:**
   - Open DevTools (F12)
   - Look for errors in Console tab
   - Check Network tab for failed API calls

3. **Create GitHub issue:**
   - Go to: https://github.com/angelxlakra/lily-cafe-pos/issues
   - Include:
     - Migration step where issue occurred
     - Error messages (full text)
     - System information (OS, Python version, Node version)
     - Logs from backend and frontend

### Emergency Rollback

If system is completely broken:

```bash
# IMMEDIATE: Stop services and restore backup
cd /path/to/lily-cafe-pos
sudo systemctl stop lily-cafe-backend lily-cafe-frontend
cp backend/restaurant_pre_v0.2.0_*.db backend/restaurant.db
git checkout v0.1.2
sudo systemctl start lily-cafe-backend lily-cafe-frontend
```

Then investigate the issue before attempting migration again.

---

## Migration Checklist Summary

Use this checklist to track migration progress:

**Pre-Migration:**
- [ ] Database backed up
- [ ] Configuration files backed up
- [ ] Current state documented
- [ ] Services stopped

**Migration:**
- [ ] Code updated to v0.2.0
- [ ] Backend dependencies installed
- [ ] Database migration executed successfully
- [ ] Frontend dependencies installed
- [ ] Frontend build completed

**Post-Migration:**
- [ ] Services restarted
- [ ] Backend API responding
- [ ] Frontend loading correctly
- [ ] Existing features working (regression test)
- [ ] New features accessible
- [ ] Data integrity verified

**Optional:**
- [ ] WhatsApp inventory imported
- [ ] Cash counter initialized
- [ ] Staff trained on new features
- [ ] Documentation updated

---

## Success Criteria

Migration is considered successful when:

✅ All existing features work as before
✅ New inventory endpoints return valid responses
✅ New cash counter endpoints return valid responses
✅ Frontend loads without console errors
✅ WhatsApp import creates categories and items
✅ Daily Count UI displays and functions correctly
✅ No data loss from existing tables
✅ All 4 new database tables exist

---

## Changelog Reference

For complete list of changes in v0.2.0, see [CHANGELOG.md](../CHANGELOG.md#020---2025-12-30)

---

**Migration Guide Version:** 1.0
**Compatible with:** Lily Cafe POS v0.1.x → v0.2.0
**Last Tested:** 2025-12-30
