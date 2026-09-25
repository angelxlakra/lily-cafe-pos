# 🔄 Auto-Update System Setup

Automatically keep your client's POS system up to date without Docker complexity.

> **Which deployment does this apply to?**
> This covers the **on-premises Windows install**, where the backend and
> frontend both run on the cafe PC and are updated from git. On the **cloud
> deployment** (backend on Fly.io, frontend on Vercel) updates ship by
> `fly deploy` and a push to `main` — see [DEPLOYMENT.md](DEPLOYMENT.md).

---

## 📦 What's Included

All of these live in `scripts\windows\`:

- **`setup.bat`** - One-time setup; registers the scheduled update task
- **`update.bat`** - The update script (run by the scheduler, or double-click anytime)
- **`logs.bat`** - View update history and troubleshoot
- **`start.bat`** / **`start-dev.bat`** - Launch the system
- Automatic database backups before each update
- Error handling with rollback capability
- Update logging for remote monitoring

See [scripts/README.md](scripts/README.md) for what each one does.

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Initial Setup on Client's Laptop

1. **Ensure Git is installed:**
   ```powershell
   git --version
   ```
   If not installed: Download from https://git-scm.com/download/win

2. **Test the update script manually:**
   - Double-click `scripts\windows\update.bat`
   - Should show "No updates available" (you're already current)
   - This verifies everything works

### Step 2: Schedule Automatic Updates

Run `scripts\windows\setup.bat` as Administrator (right-click → "Run as
Administrator"). It asks what time updates should run, then registers a daily
Windows scheduled task named **"Lily Cafe POS Auto Update"** that runs
`scripts\windows\update.bat`, waking the computer if needed.

That is the whole setup — the manual Task Scheduler walkthrough that used to be
here is no longer needed.

To change the time later, run `setup.bat` again; it replaces the existing task.

To confirm the task exists:

```powershell
schtasks /query /tn "Lily Cafe POS Auto Update"
```

---

## 📋 How It Works

### Automatic Updates (daily, at the time set during setup)

```
1. Task Scheduler wakes computer at 3 AM
2. Checks for updates from your Git repository
3. If updates found:
   ✓ Backs up database
   ✓ Pulls latest code
   ✓ Updates dependencies
   ✓ Logs everything
4. If anything fails:
   ✓ Rolls back automatically
   ✓ Logs error for troubleshooting
5. Computer can go back to sleep
```

### What Gets Updated

- ✅ Backend code (Python/FastAPI)
- ✅ Frontend code (React)
- ✅ Dependencies (Python packages, npm packages)
- ✅ Configuration files (if changed)
- ❌ Database data (never modified, only backed up)
- ❌ `.env` settings (client's config preserved)

---

## 🛠️ Usage

### For You (Developer)

**To push an update:**
```bash
# Develop and test locally
git add .
git commit -m "fix: improve printer connectivity"
git push origin main

# That's it! Update will install automatically at 3 AM
```

**To force immediate update (via Tailscale):**
```bash
# Connect via Tailscale
ssh user@client-laptop

# Or use Remote Desktop and run:
C:\lily-cafe-pos\scripts\windows\update.bat
```

### For Client

**Manual update (if they ask):**
1. Close POS system (both windows)
2. Double-click `scripts\windows\update.bat`
3. Wait for "Update Successful" message
4. Restart POS with `scripts\windows\start.bat`

**View update history:**
1. Double-click `scripts\windows\logs.bat`
2. Choose log number to view

---

## 📊 Monitoring Updates Remotely

### Via Tailscale + PowerShell

```powershell
# Connect via Tailscale
ssh user@client-laptop

# View latest update log
type C:\lily-cafe-pos\logs\update_*.log | Select-Object -Last 50

# Check last update time
dir C:\lily-cafe-pos\logs\update_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# Trigger update manually
cd C:\lily-cafe-pos
.\scripts\windows\update.bat
```

### Create a Remote Monitoring Script

Save this as `check-client-updates.ps1` on YOUR machine (it is not part of the repository):

```powershell
# Monitor client's update status via Tailscale
param(
    [string]$ClientIP = "100.x.x.x"  # Client's Tailscale IP
)

Write-Host "Checking Lily Cafe POS update status..." -ForegroundColor Cyan
Write-Host "Client: $ClientIP" -ForegroundColor Yellow
Write-Host ""

# Check latest log via SSH (requires SSH setup on client)
ssh user@$ClientIP "type C:\lily-cafe-pos\logs\update_*.log | Select-Object -Last 20"

# Or use PowerShell remoting
# Invoke-Command -ComputerName $ClientIP -ScriptBlock {
#     Get-Content C:\lily-cafe-pos\logs\update_*.log -Tail 20
# }
```

---

## 🔒 Safety Features

### Automatic Rollback
If update fails, automatically reverts to previous version:
```
[ERROR] Backend dependency update failed
[INFO] Rolling back to commit abc123...
[SUCCESS] Rollback completed
```

### Database Backups
Before each update:
- Database copied to `backups/restaurant_pre_update_YYYYMMDD_HHMMSS.db`
- Keeps backups for manual recovery
- Never modifies production database during update

### Error Logging
All operations logged to `logs/update_YYYYMMDD_HHMMSS.log`:
- What was updated
- Any errors encountered
- Timestamps for troubleshooting

---

## 🐛 Troubleshooting

### Update Not Running

**Check Task Scheduler:**
```powershell
# See last run result
Get-ScheduledTask -TaskName "Lily Cafe POS Auto Update" | Get-ScheduledTaskInfo
```

Expected: `LastRunTime` should be recent, `LastTaskResult` = `0` (success)

**Common Issues:**
- Task showing "Disabled" → Right-click task → Enable
- Last result `0x1` → Check logs, likely Git or network error
- Not waking from sleep → Check "Wake to run" is enabled

### Git Errors

```
[ERROR] Failed to fetch updates from remote
```

**Fix:**
1. Verify internet connection
2. Check Git credentials:
   ```bash
   cd C:\lily-cafe-pos
   git fetch origin main
   ```
3. May need to re-authenticate Git

### Dependency Errors

```
[ERROR] Backend dependency update failed
```

**Fix:**
1. Check if `uv` is installed: `uv --version`
2. Reinstall if needed:
   ```powershell
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

### Check Update Logs

```powershell
# View all recent logs
cd C:\lily-cafe-pos
.\scripts\windows\logs.bat

# Or manually
notepad logs\update_20241107_030000.log
```

---

## 🔧 Advanced Configuration

### Change Update Time

Edit the Task Scheduler trigger:
1. Open Task Scheduler
2. Find "Lily Cafe POS Auto Update"
3. Right-click → Properties
4. Triggers tab → Edit
5. Change Start time

### Disable Auto-Updates Temporarily

```powershell
# Disable
Disable-ScheduledTask -TaskName "Lily Cafe POS Auto Update"

# Re-enable later
Enable-ScheduledTask -TaskName "Lily Cafe POS Auto Update"
```

### Update Multiple Times Per Day

Add additional triggers in Task Scheduler:
- Morning: 6:00 AM (before opening)
- Evening: 3:00 AM (after closing)

---

## 🎯 Best Practices

### For You (Developer)

1. **Test updates locally first:**
   ```bash
   git checkout -b test-update
   # Make changes
   # Test thoroughly
   git checkout main
   git merge test-update
   git push
   ```

2. **Tag stable releases:**
   ```bash
   git tag -a v1.2.3 -m "Stable release with printer fixes"
   git push --tags
   ```

3. **Monitor after pushing:**
   - Check logs next day via Tailscale
   - Verify update installed successfully

4. **Communicate breaking changes:**
   - If update needs manual intervention, call client first
   - Create rollback instructions

### For Client

1. **Keep laptop plugged in at night** (for wake-to-update)
2. **Don't panic if "Update Successful" message appears** (it's automatic)
3. **Call you if update seems broken** (rollback is easy)

---

## 📱 Integration with Tailscale

### Setup Remote Access

1. **Install Tailscale on client laptop:**
   - Download: https://tailscale.com/download
   - Login with your account
   - Note the Tailscale IP (e.g., `100.x.x.x`)

2. **Enable SSH (optional):**
   ```powershell
   # On client laptop
   Add-WindowsCapability -Online -Name OpenSSH.Server
   Start-Service sshd
   Set-Service -Name sshd -StartupType 'Automatic'
   ```

3. **Monitor from anywhere:**
   ```bash
   # From your machine
   ssh user@100.x.x.x "type C:\lily-cafe-pos\logs\update_*.log"
   ```

---

## 🎉 Benefits Over Docker

| Feature | Auto-Update Script | Docker |
|---------|-------------------|--------|
| RAM Usage | ~50MB | ~2-3GB |
| Startup Time | 5 seconds | 30-60 seconds |
| Update Time | 1-2 minutes | 5-10 minutes |
| Printer Access | Native, works | Complex setup |
| Complexity | Simple batch files | Docker Desktop + WSL2 |
| Client Confusion | None (invisible) | "What's Docker?" |
| Your Control | Full via Tailscale | Same via Tailscale |

---

## 📞 Support

### For Clients

- **Update failed?** → Call your developer
- **Need immediate update?** → Double-click `scripts\windows\update.bat`
- **Something broke?** → Restart POS system first, then call

### For You

- **Update not deploying?** → Check Task Scheduler last run
- **Client reports issue?** → Check logs via Tailscale
- **Need to rollback?** → SSH in and run:
  ```bash
  cd C:\lily-cafe-pos
  git reset --hard <previous-commit>
  .\scripts\windows\start.bat
  ```

---

## 🔄 Next Steps

1. ✅ Scripts created
2. ⬜ Test manual update on client's laptop
3. ⬜ Setup Task Scheduler
4. ⬜ Install Tailscale for remote access
5. ⬜ Push a test update and verify it works
6. ⬜ Document client's Tailscale IP for your records

---

**Questions?** Check logs first, then troubleshoot via Tailscale!
