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

## Inventory, costing and purchases

The plan of record is `docs/INVENTORY_PLAN.md`. Read its "Next up" section before starting
inventory, dish costing, purchase, vendor or reconciliation work, and update it when you ship
a step. PRs for this work target `pre-release`, not `main`.
