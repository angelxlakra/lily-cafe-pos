# Quick Start Guide - v0.2 Development

## ✅ Current Status

You're all set! Here's what was just completed:

- ✅ v0.1.0 tagged and released
- ✅ Version management system in place
- ✅ Git workflow documented
- ✅ `v0.2-dev` branch created and pushed
- ✅ Currently on `v0.2-dev` branch
- ✅ Ready to start development

---

## 🚀 Starting v0.2 Development - RIGHT NOW

### Current Branch
```bash
# You are on: v0.2-dev
git branch
# * v0.2-dev

# Verify
git status
# On branch v0.2-dev
```

---

## 📝 Quick Command Reference

### Daily Workflow

```bash
# Morning - Start working
git checkout v0.2-dev
git pull origin v0.2-dev

# Create feature branch
git checkout -b feature/dark-mode

# Work on feature...
# Make changes, test, repeat

# Commit your work
git add .
git commit -m "feat: add dark mode context provider"

# Push for backup
git push -u origin feature/dark-mode

# When feature complete
git checkout v0.2-dev
git merge feature/dark-mode
git push origin v0.2-dev

# Delete feature branch
git branch -d feature/dark-mode
git push origin --delete feature/dark-mode
```

---

## 🎯 v0.2 Development Order

### Phase 1: Dark Mode (Days 1-2)
```bash
# 1. Create feature branch
git checkout v0.2-dev
git checkout -b feature/dark-mode

# 2. Implement dark mode
# - Create ThemeContext
# - Add CSS variables
# - Create toggle component
# - Test on all pages

# 3. Commit and merge
git add .
git commit -m "feat: complete dark mode implementation"
git checkout v0.2-dev
git merge feature/dark-mode
git branch -d feature/dark-mode
```

### Phase 2: Inventory System (Days 3-10)

#### 2a. Database & Models
```bash
git checkout -b feature/inventory-database

# Create:
# - backend/app/models/inventory.py (4 new tables)
# - Database migration script
# - Test with sample data

git add .
git commit -m "feat: add inventory database models and migrations"
git checkout v0.2-dev
git merge feature/inventory-database
git branch -d feature/inventory-database
```

#### 2b. API Endpoints
```bash
git checkout -b feature/inventory-api

# Create:
# - backend/app/api/v1/endpoints/inventory.py
# - CRUD operations for categories
# - CRUD operations for items
# - Transaction recording endpoints

git add .
git commit -m "feat: add inventory management API endpoints"
git checkout v0.2-dev
git merge feature/inventory-api
git branch -d feature/inventory-api
```

#### 2c. Frontend Pages
```bash
git checkout -b feature/inventory-ui

# Create:
# - frontend/src/pages/InventoryManagementPage.tsx
# - frontend/src/components/InventoryItemForm.tsx
# - frontend/src/components/StockAdjustmentModal.tsx
# - frontend/src/components/TransactionHistory.tsx

git add .
git commit -m "feat: add inventory management UI"
git checkout v0.2-dev
git merge feature/inventory-ui
git branch -d feature/inventory-ui
```

#### 2d. Mobile Usage Form
```bash
git checkout -b feature/usage-recording

# Create:
# - Mobile-optimized usage recording form
# - Quick input interface
# - Bulk submit

git add .
git commit -m "feat: add mobile usage recording interface"
git checkout v0.2-dev
git merge feature/usage-recording
git branch -d feature/usage-recording
```

### Phase 3: Cash Counter (Days 11-13)
```bash
git checkout -b feature/cash-counter

# Create:
# - backend/app/models/cash_counter.py
# - API endpoints for opening/closing/verification
# - Frontend CashCounterPage.tsx
# - Owner verification modal

git add .
git commit -m "feat: implement daily cash counter with verification"
git checkout v0.2-dev
git merge feature/cash-counter
git branch -d feature/cash-counter
```

### Phase 4: Polish & Testing (Days 14-15)
```bash
git checkout -b feature/v02-polish

# - Integration testing
# - Bug fixes
# - Documentation updates
# - UI polish

git add .
git commit -m "feat: polish v0.2 features and fix bugs"
git checkout v0.2-dev
git merge feature/v02-polish
git branch -d feature/v02-polish
```

---

## 🏁 When v0.2 is Complete

```bash
# 1. Final testing on v0.2-dev
git checkout v0.2-dev
# Run all tests, manual testing, etc.

# 2. Update CHANGELOG.md
# Move [Unreleased] to [0.2.0] with today's date

# 3. Bump version in all files
# - backend/pyproject.toml
# - frontend/package.json
# - backend/app/version.py
# - frontend/src/version.ts

git add .
git commit -m "chore: bump version to 0.2.0"
git push origin v0.2-dev

# 4. Merge to main
git checkout main
git merge v0.2-dev --no-ff

# 5. Tag release
git tag -a v0.2.0 -m "Release v0.2.0: Inventory Tracker & Cash Counter"

# 6. Push everything
git push origin main
git push origin v0.2.0
```

---

## 🆘 Common Commands

### Check where you are
```bash
git branch  # Show current branch
git status  # Show changes
```

### Switch branches
```bash
git checkout v0.2-dev        # Switch to dev
git checkout feature/dark-mode  # Switch to feature
```

### Save work temporarily
```bash
git stash              # Save current changes
git checkout other-branch
git checkout back
git stash pop          # Restore saved changes
```

### Undo mistakes
```bash
git restore <file>           # Discard changes in file
git restore --staged <file>  # Unstage file
git reset --soft HEAD~1      # Undo last commit (keep changes)
```

### View history
```bash
git log --oneline -10              # Last 10 commits
git log --graph --oneline --all    # Visual graph
```

---

## 📚 Full Documentation

- **Git Workflow:** [docs/GIT_WORKFLOW.md](GIT_WORKFLOW.md) - Complete workflow guide
- **Version Management:** [docs/VERSION_MANAGEMENT.md](VERSION_MANAGEMENT.md) - How to bump versions
- **v0.2 Spec:** [docs/v0.2-technical-spec.md](v0.2-technical-spec.md) - What to build
- **CHANGELOG:** [CHANGELOG.md](../CHANGELOG.md) - Version history

---

## 🎯 Your Next Steps

### Option 1: Start with Dark Mode (Recommended)
```bash
# You're already on v0.2-dev
git checkout -b feature/dark-mode

# Now start coding!
# Create: frontend/src/contexts/ThemeContext.tsx
```

### Option 2: Plan v0.2 in Detail
```bash
# Read the full spec
cat docs/v0.2-technical-spec.md | less

# Break down into smaller tasks
# Create detailed todo list
```

### Option 3: Set up Development Environment
```bash
# Start backend
cd backend
uv run uvicorn app.main:app --reload

# Start frontend (new terminal)
cd frontend
npm run dev

# Verify version endpoint
curl http://localhost:8000/version
# Should return: {"version": "0.1.0", ...}
```

---

## ✅ Checklist for Each Feature

- [ ] Create feature branch from v0.2-dev
- [ ] Implement feature with tests
- [ ] Update CHANGELOG.md (in [Unreleased] section)
- [ ] Test thoroughly
- [ ] Commit with conventional commit message
- [ ] Merge to v0.2-dev
- [ ] Delete feature branch
- [ ] Push to origin

---

## 🚨 Remember

1. **Never commit directly to main** - Use v0.2-dev
2. **Version stays at 0.1.0** - Until v0.2 release
3. **Update CHANGELOG as you go** - Don't wait till end
4. **Test before merging** - Broken code breaks others
5. **Small commits** - Easier to review and revert
6. **Push frequently** - Don't lose work

---

## 🎉 You're Ready!

The workflow is set up. Time to build v0.2!

**Start Here:**
```bash
# Confirm you're on v0.2-dev
git branch
# * v0.2-dev

# Create your first feature
git checkout -b feature/dark-mode

# Start coding! 🚀
```

---

**Questions?** Refer to [GIT_WORKFLOW.md](GIT_WORKFLOW.md) for detailed explanations.

**Last Updated:** November 12, 2025
