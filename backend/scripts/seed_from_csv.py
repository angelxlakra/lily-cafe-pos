"""
Database reset and CSV seed script for Lily Cafe POS System.

Removes the SQLite database file, recreates the schema, and seeds it with data
from the CSV files (categories.csv and menu_items.csv).

Usage:
    uv run python -m scripts.seed_from_csv
"""

import csv
from pathlib import Path
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.db.session import SessionLocal, init_db
from app.models import models


# Path to project root (2 levels up from this script)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def resolve_sqlite_path() -> Path:
    """Resolve the filesystem path of the SQLite database."""
    url = make_url(settings.DATABASE_URL)

    if url.drivername != "sqlite":
        raise RuntimeError(
            "seed_from_csv is only intended for SQLite databases. "
            f"Current URL: {settings.DATABASE_URL}"
        )

    if not url.database:
        raise RuntimeError("SQLite database path is empty in DATABASE_URL.")

    db_path = Path(url.database)
    if not db_path.is_absolute():
        db_path = (BACKEND_ROOT / db_path).resolve()

    return db_path


def purge_database():
    """Delete the existing database file."""
    db_path = resolve_sqlite_path()

    if db_path.exists():
        print(f"🗑️  Purging database file: {db_path}")
        db_path.unlink()
    else:
        print(f"ℹ️  No existing database file found at {db_path}")

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)


def read_categories_csv() -> list[dict]:
    """Read categories from CSV file."""
    csv_path = PROJECT_ROOT / "categories.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Categories CSV not found at: {csv_path}")

    categories = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['category_id'] and row['category_name']:  # Skip empty rows
                categories.append({
                    'id': int(row['category_id']),
                    'name': row['category_name'].strip()
                })

    return categories


def read_menu_items_csv() -> list[dict]:
    """Read menu items from CSV file."""
    csv_path = PROJECT_ROOT / "menu_items.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Menu items CSV not found at: {csv_path}")

    menu_items = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['item_id'] and row['name']:  # Skip empty rows
                # Convert price from rupees to paise (multiply by 100)
                price_rupees = int(row['price'])
                price_paise = price_rupees * 100

                # Convert veg_non_veg to boolean (True for Veg, False for Non-Veg)
                is_vegetarian = row['veg_non_veg'].strip().lower() == 'veg'

                menu_items.append({
                    'id': int(row['item_id']),
                    'name': row['name'].strip(),
                    'description': row['description'].strip() if row['description'] else '',
                    'price': price_paise,
                    'category_id': int(row['category_id']),
                    'is_vegetarian': is_vegetarian,
                    'is_available': True  # All items available by default
                })

    return menu_items


def seed_from_csv():
    """Seed database with data from CSV files."""
    print("\n" + "="*60)
    print("🌱 LILY CAFE POS - CSV Database Seeding")
    print("="*60 + "\n")

    # Step 1: Purge existing database
    purge_database()

    # Step 2: Recreate schema
    print("🏗️  Recreating database schema...")
    init_db()
    print("✅ Schema created\n")

    # Step 3: Read CSV files
    print("📖 Reading CSV files...")
    categories_data = read_categories_csv()
    menu_items_data = read_menu_items_csv()
    print(f"✅ Found {len(categories_data)} categories")
    print(f"✅ Found {len(menu_items_data)} menu items\n")

    # Step 4: Seed database
    db = SessionLocal()

    try:
        # Seed categories
        print("📝 Seeding categories...")
        category_map = {}  # Map CSV IDs to database objects

        for cat_data in categories_data:
            category = models.Category(
                id=cat_data['id'],
                name=cat_data['name']
            )
            db.add(category)
            category_map[cat_data['id']] = category
            print(f"   ➕ {cat_data['name']}")

        db.commit()
        print(f"✅ Seeded {len(categories_data)} categories\n")

        # Seed menu items
        print("📝 Seeding menu items...")

        for item_data in menu_items_data:
            menu_item = models.MenuItem(
                id=item_data['id'],
                name=item_data['name'],
                description=item_data['description'],
                price=item_data['price'],
                category_id=item_data['category_id'],
                is_vegetarian=item_data['is_vegetarian'],
                is_available=item_data['is_available']
            )
            db.add(menu_item)

            # Show veg/non-veg indicator
            veg_indicator = "🌱" if item_data['is_vegetarian'] else "🍖"
            price_display = f"₹{item_data['price'] / 100:.0f}"
            print(f"   ➕ {veg_indicator} {item_data['name']} - {price_display}")

        db.commit()
        print(f"✅ Seeded {len(menu_items_data)} menu items\n")

        # Summary
        print("="*60)
        print("🎉 DATABASE SEEDING COMPLETE!")
        print("="*60)
        print("\n📊 Summary by Category:")

        for cat_data in categories_data:
            items_in_category = [
                item for item in menu_items_data
                if item['category_id'] == cat_data['id']
            ]
            print(f"   • {cat_data['name']}: {len(items_in_category)} items")

        print("\n" + "="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_from_csv()
