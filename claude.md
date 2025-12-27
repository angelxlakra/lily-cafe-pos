# Claude Code Instructions for Lily Cafe POS

## Python Environment Management

This project uses `uv` for Python package and environment management.

**IMPORTANT**: Always use `uv run` to execute Python commands and scripts in the backend.

Examples:
- `uv run python scripts/migrate_add_quantity_served.py`
- `uv run pytest tests/`
- `uv run python -m app.main`

Do NOT use:
- `python script.py`
- `source .venv/bin/activate && python script.py`

## Project Structure

- `/backend` - FastAPI backend application
- `/frontend` - React TypeScript frontend application
