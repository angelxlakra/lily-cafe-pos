# UV Package Manager - Quick Reference Guide

This project uses `uv` instead of `pip` and `venv` for faster, more reliable Python package management.

## 📦 What is UV?

`uv` is a blazingly fast Python package installer and resolver written in Rust. It's a drop-in replacement for `pip` and `pip-tools` that's 10-100x faster.

**Benefits:**
- ⚡ Extremely fast dependency resolution and installation
- 🔒 Automatic virtual environment management
- 📦 Compatible with `pyproject.toml` (modern Python standard)
- 🎯 Works seamlessly with existing Python projects
- 🔄 Drop-in replacement for pip commands

---

## 🚀 Installation

### One-time setup (install uv)

**On macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**On Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Or via pip (if you have Python already):**
```bash
pip install uv
```

**Verify installation:**
```bash
uv --version
```

---

## 🏗️ Project Setup

### Initial setup (first time)

```bash
# Clone/download project
cd restaurant-pos

# Install all dependencies (creates .venv automatically)
uv sync

# That's it! uv will:
# 1. Create a .venv directory
# 2. Install Python 3.11+ if needed
# 3. Install all dependencies from pyproject.toml
# 4. Create a lockfile for reproducibility
```

### What `uv sync` does
- Reads `pyproject.toml` for dependencies
- Creates `.venv` virtual environment (if it doesn't exist)
- Installs all dependencies
- Creates/updates `uv.lock` file (like package-lock.json for npm)

---

## 📝 Common Commands

### Installing dependencies

```bash
# Install all dependencies (use this most often)
uv sync

# Install with optional dependencies (e.g., dev tools)
uv sync --extra dev

# Install multiple optional groups
uv sync --extra dev --extra analytics
```

### Running Python commands

```bash
# Run Python scripts (uv automatically uses the virtual environment)
uv run python backend/seed_data.py

# Run uvicorn server
uv run uvicorn backend.main:app --reload

# Run any Python command
uv run python -c "print('Hello from uv!')"
```

**Note:** `uv run` automatically activates the virtual environment, so you don't need to activate it manually!

### Adding new packages

```bash
# Add a new package to dependencies
uv add package-name

# Add to optional dev dependencies
uv add --optional dev pytest

# Add with version constraint
uv add "fastapi>=0.104.1"

# Add multiple packages
uv add pandas openpyxl
```

### Removing packages

```bash
# Remove a package
uv remove package-name
```

### Updating packages

```bash
# Update all packages
uv sync --upgrade

# Update specific package
uv add --upgrade package-name
```

---

## 🔧 Common Tasks for This Project

### First-time setup

```bash
cd restaurant-pos

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
nano .env  # Edit with your values

# Initialize database
uv run python -c "from backend.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Seed sample data
uv run python backend/seed_data.py

# Start development server
uv run uvicorn backend.main:app --reload
```

### Daily development

```bash
# Start backend server (development mode with auto-reload)
uv run uvicorn backend.main:app --reload

# Start backend server (production mode)
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Run tests (when tests are added)
uv run pytest

# Format code with black
uv run black backend/

# Lint code with ruff
uv run ruff check backend/
```

### When pyproject.toml changes

```bash
# Someone updated pyproject.toml (e.g., added new dependencies)
# Just run sync again:
uv sync

# This will install any new dependencies
```

---

## 📂 Virtual Environment

### Where is it?

`uv` creates a `.venv` directory in your project root (same as `python -m venv`).

### Do I need to activate it?

**No!** When you use `uv run`, it automatically uses the virtual environment.

But if you want to activate it manually:

**Unix (macOS/Linux):**
```bash
source .venv/bin/activate
```

**Windows:**
```powershell
.venv\Scripts\activate
```

**Deactivate:**
```bash
deactivate
```

---

## 🆚 UV vs Traditional Tools

### Old way (pip + venv)
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python backend/seed_data.py
```

### New way (uv)
```bash
uv sync
uv run python backend/seed_data.py
```

**Much simpler!** And 10-100x faster.

---

## 🔐 Security & Reproducibility

### Lock file

`uv sync` creates a `uv.lock` file that pins exact versions of all dependencies (including transitive dependencies).

**Commit this file to git!** It ensures everyone gets the same dependency versions.

### Updating the lock file

```bash
# Update all dependencies to latest compatible versions
uv sync --upgrade

# This updates uv.lock with new versions
```

---

## 🐛 Troubleshooting

### "uv: command not found"

uv is not installed or not in your PATH.
- Reinstall uv using one of the installation methods above
- Or use `pip install uv`

### "No such file or directory: pyproject.toml"

You're not in the project root directory.
```bash
cd restaurant-pos
uv sync
```

### Virtual environment issues

Delete `.venv` and recreate:
```bash
rm -rf .venv  # or rmdir /s .venv on Windows
uv sync
```

### Cache issues

Clear uv's cache:
```bash
uv cache clean
uv sync
```

### Python version issues

uv will use the Python version specified in `pyproject.toml` (3.11+).

Check your Python version:
```bash
python --version  # or python3 --version
```

If you don't have Python 3.11+, install it:
- **macOS:** `brew install python@3.11`
- **Ubuntu:** `sudo apt install python3.11`
- **Windows:** Download from python.org

---

## 📚 Advanced Features

### Installing from a lockfile only

```bash
# Only install what's in uv.lock (no updates)
uv sync --frozen
```

### Installing different Python versions

```bash
# Install a specific Python version
uv python install 3.11

# Use a specific Python version for the project
uv python pin 3.11
```

### Working with multiple projects

Each project has its own `.venv` automatically. Just `cd` to the project and `uv sync`.

---

## 🎯 Quick Command Reference

| Task | UV Command |
|------|------------|
| Install dependencies | `uv sync` |
| Add package | `uv add package-name` |
| Remove package | `uv remove package-name` |
| Run script | `uv run python script.py` |
| Run command | `uv run command` |
| Update packages | `uv sync --upgrade` |
| Install dev dependencies | `uv sync --extra dev` |
| Start server | `uv run uvicorn backend.main:app --reload` |
| Run tests | `uv run pytest` |

---

## 📖 Documentation

**Official UV docs:** https://github.com/astral-sh/uv

**pyproject.toml guide:** https://packaging.python.org/en/latest/guides/writing-pyproject-toml/

---

## ✅ For Lily Cafe POS Project

### Essential commands you'll use:

```bash
# Setup (once)
uv sync
cp .env.example .env

# Database setup (once)
uv run python -c "from backend.database import Base, engine; Base.metadata.create_all(bind=engine)"
uv run python backend/seed_data.py

# Daily work
uv run uvicorn backend.main:app --reload  # Start dev server

# When pyproject.toml changes
uv sync

# If you add a new Python dependency
uv add package-name
```

---

**Pro tip:** Think of `uv run` as a magic prefix that makes any Python command "just work" without worrying about virtual environments!
