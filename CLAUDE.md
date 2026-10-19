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

## Design & skills

Project skills live in `.claude/skills/` (committed so cloud sessions get them too).

- **Product and design context:** `PRODUCT.md` (users, principles, constraints) and `DESIGN.md` (tokens, type, components) are the source of truth. Read them before UI work; don't restate or override them here.
- **Visual direction:** `impeccable` only, in product (app) mode. Do not use taste, ui-ux-pro-max or other visual-direction skills in this repo.
- **Code:** keep it minimal everywhere, backend and frontend logic alike (`ponytail`): reuse what exists, prefer the stdlib and native inputs over new dependencies. Never cut validation, money/GST correctness, auth checks or accessibility basics.
- **Motion:** functional feedback only (press, item added, errors, loading), under ~200ms. No decorative or scroll-driven animation; billing must never wait on an animation. Use `animate` when adding motion and `review-animations` to check it.
- **Before merging UI changes:** run `impeccable` audit/critique on the changed screens and `ponytail-review` on the diff.
