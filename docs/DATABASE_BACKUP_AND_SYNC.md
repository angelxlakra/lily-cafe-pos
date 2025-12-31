# Database Backup and Remote Access Guide

This guide covers how to backup your `restaurant.db` file and access it from multiple locations (cafe laptop, home computer, etc.).

---

## 🎯 Quick Recommendations

**Your situation:** Access database from cafe laptop AND home server

**Best approach:** **Option 2 (Automated Cloud Backups)** or **Option 4 (Litestream)**

**Why NOT simple cloud sync (Dropbox/Google Drive):**
- ⚠️ SQLite doesn't handle concurrent writes well
- ⚠️ Risk of database corruption if both locations modify simultaneously
- ⚠️ File locking issues

---

## 📦 Solution Options

### **Option 1: Manual Cloud Storage** (Simplest but not ideal)

**How it works:**
1. After closing cafe for the day, manually upload `restaurant.db` to cloud
2. At home, download to work on it
3. **CRITICAL:** Never have both locations accessing simultaneously

**Setup:**

```bash
# At cafe (end of day)
cp backend/restaurant.db ~/Dropbox/lily-cafe-backups/restaurant_$(date +%Y%m%d).db

# At home (download latest)
cp ~/Dropbox/lily-cafe-backups/restaurant_20250131.db backend/restaurant.db
```

**Pros:**
- ✅ Simple, no tools needed
- ✅ Free (using existing Dropbox/Drive account)

**Cons:**
- ❌ Manual process (easy to forget)
- ❌ Risk of confusion about which is latest
- ❌ No automatic backups
- ❌ Risk of corruption if you forget and access both

**Verdict:** ⚠️ Only use if you're very disciplined about the workflow

---

### **Option 2: Automated Cloud Backups with rclone** ⭐ **RECOMMENDED**

**How it works:**
1. Cafe laptop automatically backs up to cloud every 6 hours
2. At home, download latest backup when needed
3. Work on home copy
4. **DON'T sync back** - treat home as read-only or testing environment

**Setup:**

#### Step 1: Install rclone

```bash
# macOS
brew install rclone

# Linux
curl https://rclone.org/install.sh | sudo bash

# Windows
# Download from https://rclone.org/downloads/
```

#### Step 2: Configure cloud storage

```bash
rclone config

# Choose your cloud provider:
# - Google Drive (unlimited if you have workspace)
# - Dropbox
# - OneDrive
# - Any other cloud storage

# Give it a name: "gdrive" or "dropbox"
# Follow the authentication steps
```

#### Step 3: Enable cloud backup in backup script

Edit `backend/scripts/backup_database.py`:

```python
# Change these lines:
CLOUD_ENABLED = True  # Set to True
RCLONE_REMOTE = "gdrive"  # Your remote name from rclone config
RCLONE_PATH = "lily-cafe-backups"  # Folder in cloud
```

#### Step 4: Test backup

```bash
cd backend
uv run python scripts/backup_database.py --upload
```

#### Step 5: Automate with cron (macOS/Linux)

```bash
# Edit crontab
crontab -e

# Add this line (backup every 6 hours):
0 */6 * * * cd /Users/angelxlakra/dev/lily-cafe-pos/backend && /usr/local/bin/uv run python scripts/backup_database.py --upload

# Or daily at 2 AM:
0 2 * * * cd /Users/angelxlakra/dev/lily-cafe-pos/backend && /usr/local/bin/uv run python scripts/backup_database.py --upload
```

**For Windows Task Scheduler:**

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 2 AM
4. Action: Start a program
5. Program: `C:\path\to\uv.exe`
6. Arguments: `run python scripts/backup_database.py --upload`
7. Start in: `C:\path\to\lily-cafe-pos\backend`

#### Step 6: Download at home

```bash
# List available backups
rclone ls gdrive:lily-cafe-backups

# Download latest backup
rclone copy gdrive:lily-cafe-backups/restaurant_backup_20250131_140000.db backend/

# Use it
cp restaurant_backup_20250131_140000.db restaurant.db
```

**Pros:**
- ✅ Fully automated backups
- ✅ Cloud accessible from anywhere
- ✅ Free (Google Drive has generous limits)
- ✅ Version history (keeps multiple backups)
- ✅ Safe (no concurrent access issues)

**Cons:**
- ❌ Not real-time sync
- ❌ Home copy is for read-only/testing (don't sync changes back)

**Verdict:** ⭐ **Best for most use cases**

---

### **Option 3: VPN + Remote Access**

**How it works:**
1. Set up VPN or remote access to cafe laptop
2. Access cafe laptop remotely from home
3. All changes happen on cafe laptop directly

**Setup Options:**

**A. Tailscale (Easiest):**

```bash
# Install on both machines
brew install tailscale  # macOS
# Or download from https://tailscale.com/download

# Start Tailscale
sudo tailscale up

# Get IP address
tailscale ip -4
```

Access from home:
```bash
# SSH to cafe laptop
ssh user@100.x.x.x  # Tailscale IP

# Or access via browser
http://100.x.x.x:5173  # Frontend
http://100.x.x.x:8000  # Backend API
```

**B. ngrok (Temporary access):**

```bash
# Install ngrok
brew install ngrok  # macOS

# Expose backend
ngrok http 8000

# You get a public URL: https://abc123.ngrok.io
```

**Pros:**
- ✅ Real-time access to cafe database
- ✅ No sync issues (single source of truth)
- ✅ Can manage cafe system remotely

**Cons:**
- ❌ Cafe laptop must be on and connected
- ❌ Requires network stability
- ❌ Security considerations (VPN setup needed)

**Verdict:** 👍 Good if you need to check/modify cafe system remotely occasionally

---

### **Option 4: Litestream (SQLite Replication)** ⭐ **BEST FOR PRODUCTION**

**How it works:**
1. Litestream continuously replicates SQLite database to cloud (S3, GCS, Azure)
2. Near real-time backup (seconds delay)
3. Can restore instantly from cloud
4. Works in background, no interruption

**Setup:**

#### Step 1: Install Litestream

```bash
# macOS
brew install litestream

# Linux
wget https://github.com/benbjohnson/litestream/releases/download/v0.3.13/litestream-v0.3.13-linux-amd64.tar.gz
tar -xzf litestream-v0.3.13-linux-amd64.tar.gz
sudo mv litestream /usr/local/bin/
```

#### Step 2: Configure Litestream

Create `backend/litestream.yml`:

```yaml
dbs:
  - path: /Users/angelxlakra/dev/lily-cafe-pos/backend/restaurant.db
    replicas:
      - type: s3
        bucket: lily-cafe-backups
        path: restaurant-db
        region: us-east-1
        # Or use Google Cloud Storage:
      # - type: gcs
      #   bucket: lily-cafe-backups
      #   path: restaurant-db
```

#### Step 3: Set up cloud credentials

```bash
# For AWS S3
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

# Or for Google Cloud
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

#### Step 4: Run Litestream

```bash
# Test replication
litestream replicate -config litestream.yml

# Run as background service (macOS)
brew services start litestream

# Or create systemd service (Linux)
```

#### Step 5: Restore at home

```bash
# Download and restore database from cloud
litestream restore -config litestream.yml -o restaurant.db s3://lily-cafe-backups/restaurant-db
```

**Pros:**
- ✅ Continuous replication (near real-time)
- ✅ Point-in-time recovery
- ✅ Very lightweight
- ✅ Designed specifically for SQLite
- ✅ No performance impact
- ✅ Automatic disaster recovery

**Cons:**
- ❌ Requires cloud storage (AWS S3, Google Cloud Storage) - small cost
- ❌ More complex setup
- ❌ Still need to be careful about concurrent writes

**Cost:** ~$0.50-2/month for S3 storage

**Verdict:** ⭐ **Best for production/serious use**

---

### **Option 5: Upgrade to PostgreSQL + Cloud Database**

**How it works:**
1. Migrate from SQLite to PostgreSQL
2. Host PostgreSQL on cloud (AWS RDS, Google Cloud SQL, DigitalOcean)
3. Both cafe and home connect to same database

**Setup:**

This requires significant code changes (SQLAlchemy already supports it, but need to migrate data).

**Pros:**
- ✅ True multi-location access
- ✅ Proper concurrent access
- ✅ Automatic backups
- ✅ Scalable (can add more cafes)
- ✅ Professional solution

**Cons:**
- ❌ Monthly cost ($15-50/month)
- ❌ Requires migration
- ❌ Internet dependency
- ❌ More complexity

**Verdict:** 🚀 Consider this when you're ready to scale or open multiple locations

---

## 🛡️ Backup Best Practices

### **1. 3-2-1 Backup Rule**

- **3** copies of your data
- **2** different storage types (local + cloud)
- **1** off-site backup (cloud)

### **2. Automated Backups**

Never rely on manual backups. Set up automation:

```bash
# Daily automated backup
0 2 * * * cd /path/to/backend && uv run python scripts/backup_database.py --upload
```

### **3. Test Restores**

Regularly test that your backups actually work:

```bash
# Test restore
cp backups/restaurant_backup_20250131_020000.db restaurant_test.db
uv run python -c "import sqlite3; conn = sqlite3.connect('restaurant_test.db'); print(conn.execute('SELECT COUNT(*) FROM orders').fetchone())"
```

### **4. Backup Before Major Changes**

Before any migration or major update:

```bash
uv run python scripts/backup_database.py
```

### **5. Keep Multiple Versions**

The backup script keeps 30 days of backups by default. Adjust `MAX_LOCAL_BACKUPS` if needed.

---

## 📋 Recommended Workflow

### **For Your Use Case (Cafe + Home):**

**At Cafe (Production):**
1. Use **Option 2 (rclone)** or **Option 4 (Litestream)**
2. Automatic backups every 6 hours to Google Drive
3. This is your **source of truth**

**At Home (Development/Testing):**
1. Download latest backup from cloud
2. Work on copy for testing/development
3. **Never push changes back** to production directly
4. If you make improvements at home:
   - Test thoroughly
   - Deploy code changes to cafe
   - Let cafe database evolve naturally with new code

### **Workflow Example:**

```bash
# ── AT CAFE ────────────────────────────────────────────
# Automated every 6 hours via cron:
uv run python scripts/backup_database.py --upload

# ── AT HOME ────────────────────────────────────────────
# Download latest backup (when you want to check something)
rclone copy gdrive:lily-cafe-backups backend/backups/

# Use latest backup
cp backups/restaurant_backup_20250131_200000.db restaurant.db

# Check reports, test features, etc.
uv run uvicorn app.main:app --reload

# ── DEPLOYING CHANGES ───────────────────────────────────
# If you made code changes at home:
git push origin main

# At cafe: pull changes
git pull origin main
uv sync
npm install && npm run build

# Cafe database evolves with new code
# No manual database sync needed!
```

---

## 🚨 Important Warnings

### **❌ DON'T Do This:**

1. **DON'T** use Dropbox/Google Drive sync on `restaurant.db` directly
   - High risk of corruption if both locations access simultaneously

2. **DON'T** manually edit production database from home
   - Always work on a copy

3. **DON'T** assume cloud sync services handle SQLite well
   - They're designed for documents, not databases

### **✅ DO This:**

1. **DO** use automated backups
2. **DO** treat cafe as production (source of truth)
3. **DO** treat home as development (work on copies)
4. **DO** test restores regularly
5. **DO** have multiple backup layers

---

## 💰 Cost Comparison

| Solution | Monthly Cost | Setup Time | Maintenance |
|----------|--------------|------------|-------------|
| Option 1: Manual Cloud | Free | 5 min | High (manual) |
| Option 2: rclone | Free | 30 min | Low (automated) |
| Option 3: VPN (Tailscale) | Free | 15 min | Low |
| Option 4: Litestream | ~$1-2 | 1 hour | Very low |
| Option 5: PostgreSQL Cloud | $15-50 | 4-8 hours | Low |

---

## 🎯 My Recommendation for You

Based on your setup (cafe + home), I recommend:

**Immediate (This Week):**
- Set up **Option 2 (rclone + Google Drive)**
- Automated backups every 6 hours
- Cost: Free
- Time: 30 minutes

**When You Have Time (Next Month):**
- Consider **Option 4 (Litestream)**
- More robust, continuous replication
- Cost: ~$2/month
- Time: 1-2 hours

**Future (If You Expand):**
- Migrate to **Option 5 (PostgreSQL)**
- When you open second location or need real multi-user access
- Cost: $15-50/month
- Time: Weekend project

---

## 📞 Quick Setup Guide (Option 2 - Recommended)

Here's the fastest way to get started:

```bash
# 1. Install rclone
brew install rclone  # macOS
# or: curl https://rclone.org/install.sh | sudo bash  # Linux

# 2. Configure Google Drive
rclone config
# Choose: n (new remote)
# Name: gdrive
# Storage: drive (Google Drive)
# Follow authentication steps

# 3. Enable cloud backup
# Edit backend/scripts/backup_database.py:
#   CLOUD_ENABLED = True
#   RCLONE_REMOTE = "gdrive"

# 4. Test backup
cd backend
uv run python scripts/backup_database.py --upload

# 5. Set up automatic backups (every 6 hours)
crontab -e
# Add: 0 */6 * * * cd /Users/angelxlakra/dev/lily-cafe-pos/backend && /usr/local/bin/uv run python scripts/backup_database.py --upload

# DONE! Your database now backs up automatically every 6 hours to Google Drive
```

---

## 📚 Additional Resources

- [rclone Documentation](https://rclone.org/docs/)
- [Litestream Documentation](https://litestream.io/guides/)
- [SQLite Backup API](https://www.sqlite.org/backup.html)
- [Tailscale Setup Guide](https://tailscale.com/kb/1017/install/)

---

## ❓ FAQ

**Q: Can I use iCloud/OneDrive instead of Google Drive?**
A: Yes! rclone supports 40+ cloud providers. Just choose your provider during `rclone config`.

**Q: What if I forget and modify database in both places?**
A: SQLite will likely corrupt. This is why automated backups are critical - you can restore from the last good backup.

**Q: How do I restore from a backup?**
A: `cp backups/restaurant_backup_YYYYMMDD_HHMMSS.db restaurant.db`

**Q: Can I access cafe database in real-time from home?**
A: Yes, use **Option 3 (VPN)** or **Option 5 (PostgreSQL)**. But for your use case, working on backups is safer.

**Q: Is Google Drive really free for this?**
A: Yes, 15GB free. Your database is probably <10MB, so you can keep hundreds of backups.

**Q: What about security?**
A: Backups contain customer data. Use encrypted cloud storage or encrypt backups before upload (rclone supports encryption).

---

**Need help setting up? Let me know which option you want to pursue!**
