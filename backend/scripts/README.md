# Database Scripts

This directory contains utility scripts for managing the Lily Cafe POS database.

## Available Scripts

### 1. `seed_from_csv.py` - CSV-Based Database Seeding ⭐

**Purpose**: Purge all database data and seed from CSV files (production data).

**What it does**:
- Deletes the existing SQLite database file
- Recreates empty schema
- Reads `categories.csv` from project root
- Reads `menu_items.csv` from project root
- Populates database with CSV data

**Usage**:
```bash
uv run python -m scripts.seed_from_csv
```

**Data transformations**:
- Prices: CSV rupees → database paise (₹100 → 10000 paise)
- Veg/Non-Veg: CSV "Veg"/"Non-Veg" → database boolean `is_vegetarian`
- All items set to available by default

---

### 2. `seed_data.py` - Sample Data Seeding

**Purpose**: Add sample/demo data to existing database (development/testing).

**What it does**:
- Checks if data exists (skips if found)
- Seeds sample South Indian, North Indian, Beverages, Snacks, and Desserts
- Does NOT delete existing data

**Usage**:
```bash
uv run python -m scripts.seed_data
```

⚠️ **Note**: This uses old sample data, not the current production menu.

---

### 3. `reset_db_clean.py` - Clean Database Reset

**Purpose**: Create a fresh empty database with no data.

**What it does**:
- Deletes SQLite database file
- Recreates empty schema
- No seed data added

**Usage**:
```bash
uv run python -m scripts.reset_db_clean
```

**Use case**: Production handover with clean slate.

---

### 4. `reset_db_with_seed.py` - Reset with Sample Data

**Purpose**: Quick development reset with demo data.

**What it does**:
- Deletes SQLite database file
- Recreates schema
- Runs `seed_data.py` to add sample data

**Usage**:
```bash
uv run python -m scripts.reset_db_with_seed
```

**Use case**: Quick return to default sample dataset during development.

---

## CSV File Format

### `categories.csv`
```csv
category_id,category_name
1,Hot Beverages
2,Cold Beverages
```

### `menu_items.csv`
```csv
item_id,name,description,price,veg_non_veg,category_id
1,MK Special Coffee,House special coffee blend,100,Veg,1
2,Chicken Ramen,Whole wheat noodles in chicken broth,250,Non-Veg,4
```

**Fields**:
- `price`: In rupees (will be converted to paise internally)
- `veg_non_veg`: Either "Veg" or "Non-Veg"
- `category_id`: Must match an existing category ID

---

## Common Workflows

### Initial Setup (Production Menu)
```bash
# Use CSV data for production menu
uv run python -m scripts.seed_from_csv
```

### Development Testing
```bash
# Quick reset with sample data
uv run python -m scripts.reset_db_with_seed
```

### Update Menu from CSV
```bash
# Re-seed from updated CSV files
uv run python -m scripts.seed_from_csv
```

### Fresh Start
```bash
# Empty database
uv run python -m scripts.reset_db_clean
```

---

## Database Location

Default SQLite database: `backend/restaurant.db`

Configure via `DATABASE_URL` in `.env` file.
