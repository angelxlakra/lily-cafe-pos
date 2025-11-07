# 📱 Lily Cafe POS - Quick Reference Card
**Keep this near your POS station**

---

## 🚀 Starting the System

1. **Double-click:** `start-both.bat`
2. **Wait:** 15 seconds
3. **Browser opens automatically:** `http://localhost:5173`
4. **Login** with your credentials

**Both terminal windows must stay open!**

---

## 🛑 Stopping the System

**At closing time:**
- Close both terminal windows, OR
- Press `Ctrl+C` in each window

---

## 🔄 Updates (Automatic)

**Your system updates automatically every night at 3 AM**

### What You'll See:
- Nothing! Updates happen while you sleep
- System is ready when you open next day

### If Update Installed:
Just restart the system normally (same as every day)

---

## 🔧 Manual Update (if needed)

**Only if your developer asks you to update immediately:**

1. **Stop the POS** (close both windows)
2. **Double-click:** `update-now.bat`
3. **Wait** for "Update Successful"
4. **Restart:** Double-click `start-both.bat`

---

## 🏥 Troubleshooting

### System won't start?
1. Close all POS windows
2. Restart computer
3. Try `start-both.bat` again
4. If still broken → Call developer

### Printer not working?
1. Check printer power and paper
2. Check USB cable
3. Restart POS system
4. If still broken → Call developer

### Internet/Network issues?
1. Check WiFi connection
2. Restart router if needed
3. POS works offline (except online orders)

### Something looks wrong after update?
1. Restart POS system first
2. Check if it fixes itself
3. Call developer if still broken

---

## 📞 Get Help

**Your Developer:**
- Can access system remotely via Tailscale
- Can check logs to see what's wrong
- Can push fixes automatically

**Before calling:**
1. Try restarting the POS
2. Try restarting the computer
3. Note what error message you saw
4. Note what you were doing when it broke

---

## 💾 Your Data is Safe

- **Database backed up** before every update
- **Your settings never change** (in `.env` file)
- **Update failed?** System rolls back automatically
- **Computer crash?** Database saved to disk

---

## 📍 Important Files

**DON'T DELETE THESE:**
- `backend/restaurant.db` - Your database
- `backend/.env` - Your settings
- `backups/` folder - Database backups

**SAFE TO IGNORE:**
- `logs/` folder - Update logs (for developer)
- Terminal windows with scrolling text

---

## 🌙 Overnight Routine

**Before closing:**
1. Stop POS system (close windows)
2. Leave computer **plugged in**
3. Leave computer **turned on** or in sleep mode
4. Computer will wake at 3 AM
5. Check for updates
6. Go back to sleep

**Next morning:**
Just start POS normally!

---

## ✅ Daily Checklist

**Opening:**
- [ ] Turn on computer (if off)
- [ ] Double-click `start-both.bat`
- [ ] Wait for browser to open
- [ ] Test printer
- [ ] Ready for orders!

**Closing:**
- [ ] Close all orders
- [ ] Print end-of-day reports
- [ ] Close POS (both windows)
- [ ] Leave computer **plugged in**
- [ ] Leave computer **on** or **sleep mode**

---

## 🎯 Best Practices

**DO:**
- ✅ Keep computer plugged in at night
- ✅ Restart POS if something seems odd
- ✅ Call developer for any persistent issues
- ✅ Keep backup database files

**DON'T:**
- ❌ Shutdown computer every night (sleep is fine)
- ❌ Unplug at night (updates need power)
- ❌ Delete `restaurant.db` file
- ❌ Edit `.env` file without guidance

---

## 🆘 Emergency Contacts

**Developer:** [YOUR CONTACT INFO HERE]
**Tailscale Remote Access:** Enabled

---

**Questions?** Call your developer!
**System broken?** Developer can fix remotely via Tailscale!
**Lost data?** Check `backups/` folder - daily backups available!

---

*Print this page and keep near your POS station*
