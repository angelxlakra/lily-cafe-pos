# Git Workflow Guide - Lily Cafe POS

## 🌳 Branch Strategy

We use a **modified Git Flow** strategy optimized for continuous development with versions.

### Branch Types

```
main (production-ready)
├── v0.2-dev (version development)
│   ├── feature/dark-mode
│   ├── feature/inventory-system
│   └── feature/cash-counter
├── v0.3-dev (future version)
└── hotfix/0.1.1-payment-bug (emergency fixes)
```

---

## 📊 Branch Overview

| Branch Type | Naming | Purpose | Lifetime | Protected |
|-------------|--------|---------|----------|-----------|
| **main** | `main` | Production-ready code, stable releases | Permanent | YES |
| **version-dev** | `v0.2-dev`, `v0.3-dev` | Version development branch | Until release | YES |
| **feature** | `feature/dark-mode` | Individual features | Until merged | NO |
| **hotfix** | `hotfix/0.1.1-bug-name` | Emergency production fixes | Until merged | NO |
| **experiment** | `experiment/new-idea` | Experiments, POCs | Until decision | NO |

---

## 🎯 The Workflow

### 1. Main Branch (Production)

**Purpose:** Contains only stable, tested, released code

**Rules:**
- ✅ Only merge from version-dev or hotfix branches
- ✅ Every commit should have a git tag (v0.1.0, v0.2.0)
- ✅ Never commit directly to main
- ✅ All merges require testing
- ✅ CI/CD should pass before merge

**Protected Settings:**
- Require pull request reviews
- Require status checks
- No force push
- No deletion

---

### 2. Version Development Branch (v0.2-dev)

**Purpose:** Integration branch for all v0.2 features

**Rules:**
- ✅ Branch from: `main`
- ✅ Merge to: `main` (when v0.2 complete)
- ✅ Receives: Feature branches
- ✅ Version stays at previous (0.1.0) until release
- ✅ Can be tested as a whole

**Lifecycle:**
```bash
# Created at start of v0.2 development
git checkout main
git checkout -b v0.2-dev
git push -u origin v0.2-dev

# Receives feature branches during development
git merge feature/dark-mode
git merge feature/inventory-system

# Merged to main when v0.2 is complete
git checkout main
git merge v0.2-dev
git tag v0.2.0
```

---

### 3. Feature Branches

**Purpose:** Develop individual features in isolation

**Naming Convention:**
- `feature/dark-mode`
- `feature/inventory-categories`
- `feature/cash-counter`
- `feature/low-stock-alerts`

**Rules:**
- ✅ Branch from: `v0.2-dev`
- ✅ Merge to: `v0.2-dev`
- ✅ Delete after merge
- ✅ Keep small and focused
- ✅ Commit frequently

**Lifecycle:**
```bash
# Create feature branch
git checkout v0.2-dev
git checkout -b feature/dark-mode

# Work on feature
git add .
git commit -m "feat: add dark mode toggle"
git commit -m "feat: add dark mode CSS variables"

# Push to remote
git push -u origin feature/dark-mode

# When complete, merge to v0.2-dev
git checkout v0.2-dev
git merge feature/dark-mode

# Delete feature branch
git branch -d feature/dark-mode
git push origin --delete feature/dark-mode
```

---

### 4. Hotfix Branches

**Purpose:** Emergency fixes for production issues

**Naming Convention:**
- `hotfix/0.1.1-payment-calculation`
- `hotfix/0.1.2-receipt-printer`

**Rules:**
- ✅ Branch from: `main`
- ✅ Merge to: `main` AND `v0.2-dev`
- ✅ Bump PATCH version (0.1.0 → 0.1.1)
- ✅ Create git tag immediately
- ✅ Highest priority

**Lifecycle:**
```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/0.1.1-payment-bug

# Fix the bug
git add .
git commit -m "fix: correct payment calculation rounding"

# Update version to 0.1.1
# (Edit pyproject.toml, package.json, version.py, version.ts)
git commit -m "chore: bump version to 0.1.1"

# Merge to main
git checkout main
git merge hotfix/0.1.1-payment-bug
git tag -a v0.1.1 -m "Hotfix: Payment calculation bug"
git push origin main --tags

# Merge to v0.2-dev (keep it updated)
git checkout v0.2-dev
git merge hotfix/0.1.1-payment-bug
git push origin v0.2-dev

# Delete hotfix branch
git branch -d hotfix/0.1.1-payment-bug
git push origin --delete hotfix/0.1.1-payment-bug
```

---

## 🚀 Complete v0.2 Development Workflow

### Phase 1: Setup (Day 1)

```bash
# 1. Ensure main is clean and up to date
git checkout main
git pull origin main

# 2. Commit any pending work (version management files)
git add CHANGELOG.md docs/VERSION_MANAGEMENT.md docs/GIT_WORKFLOW.md
git add backend/app/version.py frontend/src/version.ts backend/app/main.py
git add docs/v0.1-completion-report.md docs/v0.2-technical-spec.md
git commit -m "docs: add version management system and v0.1 completion report"
git push origin main

# 3. Tag v0.1.0 (if not already done)
git tag -a v0.1.0 -m "Release v0.1.0: Initial MVP

Features:
- Core POS functionality
- Menu and order management
- Payment processing
- Receipt printing
- Kitchen chit system

See CHANGELOG.md for details."
git push origin v0.1.0

# 4. Create v0.2-dev branch
git checkout -b v0.2-dev
git push -u origin v0.2-dev

# 5. Protect branches on GitHub (manual step)
# Go to Settings → Branches → Add rule
```

---

### Phase 2: Feature Development (Day 2-14)

```bash
# For each feature (example: dark mode)

# 1. Create feature branch from v0.2-dev
git checkout v0.2-dev
git pull origin v0.2-dev  # Get latest changes
git checkout -b feature/dark-mode

# 2. Develop the feature
# Make changes...
git add .
git commit -m "feat: add dark mode context and provider"

# More changes...
git add .
git commit -m "feat: add dark mode toggle component"

# More changes...
git add .
git commit -m "feat: add dark mode CSS variables"

# Update CHANGELOG.md as you go
git add CHANGELOG.md
git commit -m "docs: update changelog with dark mode feature"

# 3. Push feature branch (for backup or PR)
git push -u origin feature/dark-mode

# 4. When feature is complete and tested
git checkout v0.2-dev
git pull origin v0.2-dev  # Get latest
git merge feature/dark-mode --no-ff  # Preserve feature branch history
git push origin v0.2-dev

# 5. Delete feature branch
git branch -d feature/dark-mode
git push origin --delete feature/dark-mode

# 6. Repeat for next feature
git checkout -b feature/inventory-system
# ... develop ...
```

---

### Phase 3: Testing & Integration (Day 13-14)

```bash
# On v0.2-dev branch

# 1. Run full test suite
npm run test  # Frontend tests
pytest  # Backend tests

# 2. Manual testing with test plan
# Follow docs/MANUAL_TESTING_GUIDE.md

# 3. Fix any bugs found
git checkout -b bugfix/inventory-validation
# Fix bug...
git commit -m "fix: validate inventory quantities properly"
git checkout v0.2-dev
git merge bugfix/inventory-validation
git branch -d bugfix/inventory-validation

# 4. Final integration testing
# Test all features together

# 5. Update documentation
git add docs/
git commit -m "docs: update guides for v0.2 features"
```

---

### Phase 4: Release (Day 15)

```bash
# 1. Finalize CHANGELOG.md
git checkout v0.2-dev
# Edit CHANGELOG.md - move [Unreleased] to [0.2.0] with date
git add CHANGELOG.md
git commit -m "docs: finalize v0.2.0 changelog"

# 2. Bump version in all files
# Edit these files:
# - backend/pyproject.toml: version = "0.2.0"
# - frontend/package.json: "version": "0.2.0"
# - backend/app/version.py: __version__ = "0.2.0"
# - frontend/src/version.ts: VERSION = '0.2.0'

git add backend/pyproject.toml frontend/package.json
git add backend/app/version.py frontend/src/version.ts
git commit -m "chore: bump version to 0.2.0"

# 3. Push final v0.2-dev
git push origin v0.2-dev

# 4. Create Pull Request on GitHub
# Title: "Release v0.2.0: Inventory Tracker & Cash Counter"
# Base: main
# Compare: v0.2-dev
# Review and approve

# 5. Merge to main (via PR or command line)
git checkout main
git pull origin main
git merge v0.2-dev --no-ff -m "Release v0.2.0: Inventory Tracker & Cash Counter"

# 6. Create release tag
git tag -a v0.2.0 -m "Release v0.2.0: Inventory Tracker & Cash Counter

Features:
- Dark mode theme toggle
- Inventory management system
- Daily cash counter with verification
- Low stock alerts
- Transaction history

See CHANGELOG.md for full details."

# 7. Push everything
git push origin main
git push origin v0.2.0

# 8. Optional: Delete v0.2-dev (or keep for reference)
# git branch -d v0.2-dev
# git push origin --delete v0.2-dev

# 9. Create GitHub Release (manual on GitHub)
# Go to Releases → Draft new release
# Choose tag v0.2.0
# Copy CHANGELOG content
# Publish release
```

---

## 🔥 Emergency Hotfix Workflow

If production bug found in v0.1.0 while developing v0.2:

```bash
# 1. Create hotfix from main
git checkout main
git checkout -b hotfix/0.1.1-critical-bug

# 2. Fix the bug
# Make fix...
git add .
git commit -m "fix: resolve critical payment bug"

# 3. Bump version to 0.1.1
# Edit version files
git commit -m "chore: bump version to 0.1.1"

# 4. Merge to main
git checkout main
git merge hotfix/0.1.1-critical-bug
git tag -a v0.1.1 -m "Hotfix: Critical payment bug"
git push origin main v0.1.1

# 5. Merge to v0.2-dev (important!)
git checkout v0.2-dev
git merge hotfix/0.1.1-critical-bug
git push origin v0.2-dev

# 6. Delete hotfix branch
git branch -d hotfix/0.1.1-critical-bug
```

---

## 📝 Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Code style (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring (no feature/fix)
- **perf**: Performance improvement
- **test**: Adding/updating tests
- **chore**: Build process, dependencies, tooling
- **ci**: CI/CD changes

### Examples
```bash
feat(inventory): add inventory categories CRUD API

Implements create, read, update, delete operations for inventory
categories with validation and error handling.

Closes #123

---

fix(payment): correct GST calculation rounding

Previously using float arithmetic caused precision errors.
Now using Decimal type for accurate calculations.

Fixes #456

---

docs(api): update API reference with inventory endpoints

Added documentation for:
- POST /api/v1/inventory/categories
- GET /api/v1/inventory/items
- PATCH /api/v1/inventory/items/:id

---

chore: bump version to 0.2.0

Updates version across all package files for v0.2.0 release.
```

---

## 🛡️ Branch Protection Rules

### For `main` branch:

**On GitHub:**
1. Go to Settings → Branches
2. Add rule for `main`
3. Enable:
   - ✅ Require pull request reviews before merging (1 approval)
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Require linear history
   - ✅ Do not allow bypassing the above settings
   - ✅ Restrict who can push to matching branches
   - ⚠️ Do not allow force pushes
   - ⚠️ Do not allow deletions

### For `v0.2-dev` branch:

**On GitHub:**
1. Add rule for pattern `v*-dev`
2. Enable:
   - ✅ Require pull request reviews (optional)
   - ✅ Require status checks to pass
   - ⚠️ Do not allow force pushes (use with caution)
   - Allow deletion (after merge to main)

---

## 🔍 Useful Git Commands

### Checking Status

```bash
# Current status
git status

# Show branches
git branch -a

# Show recent commits
git log --oneline -10

# Show branch history graph
git log --graph --oneline --all --decorate

# Show what changed
git diff

# Show commits that will be merged
git log main..v0.2-dev
```

### Working with Branches

```bash
# Switch branches
git checkout v0.2-dev

# Create and switch to new branch
git checkout -b feature/dark-mode

# Rename current branch
git branch -m old-name new-name

# Delete local branch
git branch -d feature/dark-mode

# Delete remote branch
git push origin --delete feature/dark-mode

# List merged branches
git branch --merged

# List unmerged branches
git branch --no-merged
```

### Syncing with Remote

```bash
# Fetch all changes
git fetch --all --prune

# Pull latest from current branch
git pull origin v0.2-dev

# Push current branch
git push origin v0.2-dev

# Push with tags
git push origin main --tags

# Set upstream for new branch
git push -u origin feature/dark-mode
```

### Undoing Changes

```bash
# Discard uncommitted changes in file
git restore <file>

# Unstage file
git restore --staged <file>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) ⚠️ DANGER
git reset --hard HEAD~1

# Revert a commit (creates new commit)
git revert <commit-hash>

# Stash changes temporarily
git stash
git stash pop  # Apply stashed changes
git stash list  # List stashes
```

### Tags

```bash
# List all tags
git tag

# Create annotated tag
git tag -a v0.2.0 -m "Release v0.2.0"

# Tag specific commit
git tag -a v0.1.1 <commit-hash> -m "Hotfix v0.1.1"

# Push single tag
git push origin v0.2.0

# Push all tags
git push origin --tags

# Delete local tag
git tag -d v0.2.0

# Delete remote tag
git push origin --delete v0.2.0

# Show tag details
git show v0.2.0

# Checkout specific tag
git checkout v0.1.0
```

---

## 🎨 Git Aliases (Optional)

Add these to your `~/.gitconfig` or run these commands:

```bash
# Status shortcuts
git config --global alias.st status
git config --global alias.br branch
git config --global alias.co checkout
git config --global alias.ci commit

# Log shortcuts
git config --global alias.lg "log --graph --oneline --all --decorate"
git config --global alias.last "log -1 HEAD"

# Branch shortcuts
git config --global alias.branches "branch -a"
git config --global alias.merged "branch --merged"

# Diff shortcuts
git config --global alias.unstage "restore --staged"
git config --global alias.discard "restore"

# Now you can use:
# git st  (instead of git status)
# git lg  (instead of git log --graph...)
# git co feature/dark-mode  (instead of git checkout)
```

---

## 📊 Visual Workflow Diagram

```
Time →

main:         v0.1.0 ───────────────────────────────────→ v0.2.0 ───→
                │                                           ↑
                │                                           │ merge
                ↓                                           │
v0.2-dev:       └─→ dev ──┬──┬──┬──┬──┬──┬──┬──┬──┬──→ dev ┘
                           │  │  │  │  │  │  │  │  │
                           │  │  │  │  │  │  │  │  │
feature/dark:              └──┘  │  │  │  │  │  │  │
                                 │  │  │  │  │  │  │
feature/inventory:               └──┴──┘  │  │  │  │
                                          │  │  │  │
feature/cash:                             └──┴──┘  │
                                                   │
bugfix/validation:                                 └──┘


hotfix:      ──────────── v0.1.1 ──────────────────────
                          ↓    ↓
                        main  v0.2-dev
```

---

## ✅ Checklist: Starting v0.2 Development

- [ ] Main branch is clean and pushed
- [ ] v0.1.0 is tagged
- [ ] Created v0.2-dev branch
- [ ] Set branch protection on GitHub
- [ ] Documented workflow (this file!)
- [ ] Team understands workflow
- [ ] Ready to create first feature branch

---

## 📚 Additional Resources

- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

---

## 🚨 Common Mistakes to Avoid

1. ❌ **Committing directly to main**
   - ✅ Always use feature branches

2. ❌ **Forgetting to pull before pushing**
   - ✅ Always `git pull` before `git push`

3. ❌ **Force pushing to protected branches**
   - ✅ Never use `git push --force` on main or dev branches

4. ❌ **Not updating CHANGELOG.md**
   - ✅ Update as you add features

5. ❌ **Merging untested code to main**
   - ✅ Test thoroughly before merging

6. ❌ **Not deleting feature branches after merge**
   - ✅ Keep repository clean

7. ❌ **Working on wrong branch**
   - ✅ Check `git branch` before starting work

8. ❌ **Not syncing hotfixes to dev branch**
   - ✅ Merge hotfixes to both main and dev

---

## 📞 Questions?

- **Which branch should I work on?**
  - Create a feature branch from `v0.2-dev`

- **Can I commit to v0.2-dev directly?**
  - Small fixes: Yes
  - Features: No, use feature branches

- **When do I bump the version?**
  - Only when merging to main for release
  - Not during development

- **What if I need to switch features midway?**
  - Commit current work or use `git stash`
  - Switch branches
  - Come back later

---

**Last Updated:** November 11, 2025
**Document Version:** 1.0
