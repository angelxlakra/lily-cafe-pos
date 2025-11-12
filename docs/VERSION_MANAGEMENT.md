# Version Management Guide

## Current Version: 0.1.0

This document outlines how to manage version changes for the Lily Cafe POS System.

---

## 📦 Semantic Versioning

We follow [Semantic Versioning 2.0.0](https://semver.org/):

**Format:** `MAJOR.MINOR.PATCH`

- **MAJOR** (0.x.x): Breaking changes, incompatible API changes
- **MINOR** (x.1.x): New features, backward-compatible
- **PATCH** (x.x.1): Bug fixes, backward-compatible

### Examples:
- `0.1.0` → `0.2.0`: New features (inventory, cash counter)
- `0.2.0` → `0.2.1`: Bug fixes in inventory
- `0.2.0` → `1.0.0`: Production-ready release, stable API

---

## 🔄 When to Bump Version

### PATCH Version (0.1.x → 0.1.y)
- Bug fixes
- Security patches
- Documentation updates
- Performance improvements
- No new features

### MINOR Version (0.x.0 → 0.y.0)
- New features added
- New API endpoints
- New database tables
- Backward-compatible changes
- **This is what we're doing for v0.2**

### MAJOR Version (x.0.0 → y.0.0)
- Breaking API changes
- Database schema breaking changes
- Major UI/UX overhaul
- Incompatible with previous version
- **We'll do this for v1.0 (production release)**

---

## ✅ Version Change Checklist

Use this checklist every time you change versions:

### 1. **Update Package Files**

#### Backend: `backend/pyproject.toml`
```toml
[project]
version = "0.2.0"  # Update this line
```

#### Frontend: `frontend/package.json`
```json
{
  "version": "0.2.0",  // Update this line
}
```

### 2. **Update Version Constants**

#### Backend: `backend/app/version.py`
```python
__version__ = "0.2.0"
__version_info__ = (0, 2, 0)

VERSION_HISTORY = {
    "0.1.0": "2025-11-11 - Initial MVP release",
    "0.2.0": "2025-11-XX - Inventory & cash counter",  # Add new entry
}
```

#### Frontend: `frontend/src/version.ts`
```typescript
export const VERSION = '0.2.0';

export const VERSION_INFO = {
  version: VERSION,
  major: 0,
  minor: 2,  // Update
  patch: 0,
  releaseDate: '2025-11-XX',  // Update
  releaseName: 'Inventory Tracker & Cash Counter',  // Update
};
```

### 3. **Update CHANGELOG.md**

Move features from `[Unreleased]` to new version section:

```markdown
## [Unreleased]
<!-- Empty or next features -->

## [0.2.0] - 2025-11-XX

### Added
- Dark mode theme toggle
- Inventory management system
- Daily cash counter
- (list all new features)

### Changed
- (list modified features)

### Fixed
- (list bug fixes)
```

### 4. **Create Git Tag**

```bash
# Commit all version changes first
git add .
git commit -m "chore: bump version to 0.2.0"

# Create annotated tag
git tag -a v0.2.0 -m "Release v0.2.0: Inventory Tracker & Cash Counter"

# Push tag to remote
git push origin v0.2.0

# Or push all tags
git push --tags
```

### 5. **Update Documentation**

- Update README.md if needed
- Update deployment guides with new features
- Add migration guides if database changed
- Update API documentation

### 6. **Test Version Endpoints**

```bash
# Test backend version
curl http://localhost:8000/
curl http://localhost:8000/version

# Should return:
# {
#   "version": "0.2.0",
#   "version_tuple": [0, 2, 0],
#   "release_date": "2025-11-XX - Inventory & cash counter"
# }
```

### 7. **Create GitHub Release** (Optional)

If using GitHub:
1. Go to Releases page
2. Click "Draft a new release"
3. Choose tag `v0.2.0`
4. Add release notes from CHANGELOG
5. Attach any binaries/installers
6. Publish release

---

## 🚀 Version Workflow for v0.2

Here's the complete workflow for bumping to v0.2:

### **Before Starting Development**

```bash
# Create development branch
git checkout -b v0.2-development

# All v0.2 work happens in this branch
```

### **During Development**

- Keep CHANGELOG.md updated in `[Unreleased]` section
- Version numbers stay at `0.1.0`
- Commit regularly with conventional commits:
  - `feat: add dark mode toggle`
  - `feat: add inventory categories API`
  - `fix: correct GST calculation`
  - `docs: update inventory guide`

### **When v0.2 is Complete**

```bash
# 1. Finalize CHANGELOG
nano CHANGELOG.md  # Move [Unreleased] to [0.2.0]

# 2. Update all version files (see checklist above)
# - backend/pyproject.toml
# - frontend/package.json
# - backend/app/version.py
# - frontend/src/version.ts

# 3. Commit version bump
git add .
git commit -m "chore: bump version to 0.2.0"

# 4. Merge to main
git checkout main
git merge v0.2-development

# 5. Create tag
git tag -a v0.2.0 -m "Release v0.2.0: Inventory Tracker & Cash Counter

Features:
- Dark mode theme toggle
- Inventory management system
- Daily cash counter with verification
- Low stock alerts
- Transaction history

See CHANGELOG.md for full details."

# 6. Push everything
git push origin main
git push origin v0.2.0
```

---

## 📍 Where Version is Used

### Backend
1. ✅ `backend/pyproject.toml` - Package version
2. ✅ `backend/app/version.py` - Version constants
3. ✅ `backend/app/main.py` - FastAPI app metadata
4. ✅ `GET /` endpoint - Returns version in JSON
5. ✅ `GET /version` endpoint - Detailed version info
6. ✅ API docs - Shows in Swagger UI at `/docs`

### Frontend
1. ✅ `frontend/package.json` - Package version
2. ✅ `frontend/src/version.ts` - Version constants
3. ⏳ Footer component - Could display version
4. ⏳ About page - Could show version info
5. ⏳ Console log - Could log version on load

### Documentation
1. ✅ `CHANGELOG.md` - Complete version history
2. ✅ `README.md` - Current version mention
3. ✅ API docs - Version in OpenAPI spec

---

## 🔍 Version Query Commands

### Check Current Version

```bash
# Backend version
grep 'version = ' backend/pyproject.toml

# Frontend version
grep '"version":' frontend/package.json

# Python version constant
cat backend/app/version.py | grep __version__

# TypeScript version constant
cat frontend/src/version.ts | grep VERSION
```

### Check Git Tags

```bash
# List all tags
git tag -l

# Show latest tag
git describe --tags --abbrev=0

# Show tag details
git show v0.1.0
```

### Check Deployed Version

```bash
# Query running backend
curl http://localhost:8000/version

# Or from frontend code
fetch('/version').then(r => r.json()).then(console.log)
```

---

## 📝 Version Naming Conventions

### Git Tags
- Format: `vMAJOR.MINOR.PATCH`
- Examples: `v0.1.0`, `v0.2.0`, `v1.0.0`
- Always prefix with `v`

### Git Branches
- Development: `v0.2-development`
- Hotfix: `hotfix/0.1.1-payment-bug`
- Feature: `feature/inventory-management`

### Git Commits
- Version bumps: `chore: bump version to 0.2.0`
- Features: `feat: add dark mode toggle`
- Fixes: `fix: resolve payment calculation error`
- Docs: `docs: update API documentation`

---

## 🎯 Version 0.2 Specific Notes

### What's Changing in v0.2:
- **MINOR version bump** (0.1.0 → 0.2.0)
- **Database schema**: 4 new tables
- **API endpoints**: ~15-20 new endpoints
- **UI**: 5-8 new pages/components
- **Backward compatible**: All v0.1 features still work

### Migration Notes:
- No breaking changes to existing APIs
- v0.1 database will be migrated automatically
- All v0.1 features remain functional
- New features are additive only

---

## ✨ Best Practices

1. **Never skip versions**: Go 0.1 → 0.2 → 0.3, not 0.1 → 0.3
2. **Update CHANGELOG first**: Keep it updated during development
3. **Tag after testing**: Only tag when version is stable
4. **Annotated tags only**: Use `git tag -a`, not `git tag`
5. **Single source of truth**: Use version constants, not hardcoded strings
6. **Test version endpoints**: Always verify after bumping
7. **Document breaking changes**: Very clearly in CHANGELOG
8. **Keep consistency**: Same version across backend/frontend

---

## 🔗 Related Documents

- [CHANGELOG.md](../CHANGELOG.md) - Complete version history
- [v0.1-technical-spec.md](v0.1-technical-spec.md) - v0.1 specifications
- [v0.2-technical-spec.md](v0.2-technical-spec.md) - v0.2 specifications
- [v0.1-completion-report.md](v0.1-completion-report.md) - v0.1 status report

---

## 📞 Questions?

If unsure about version bumping:
1. Check [Semantic Versioning](https://semver.org/)
2. Review this guide's examples
3. Look at CHANGELOG.md for patterns
4. When in doubt, bump MINOR (not MAJOR)

---

**Last Updated:** November 11, 2025
**Document Version:** 1.0
