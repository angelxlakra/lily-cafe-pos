"""
Seed data script for Lily Cafe POS System.
Populates the database with sample categories and menu items for testing.

Usage:
    uv run python -m scripts.seed_data
"""

from app.db.session import SessionLocal, init_db
from app.models import models


def seed_database():
    """Seed the database with sample data."""
    print("Initializing database...")
    init_db()

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_categories = db.query(models.Category).count()
        if existing_categories > 0:
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding categories...")

        # Create categories (aligned with v0.1 spec)
        categories = {
            "South Indian": models.Category(name="South Indian"),
            "North Indian": models.Category(name="North Indian"),
            "Beverages": models.Category(name="Beverages"),
            "Snacks": models.Category(name="Snacks"),
            "Desserts": models.Category(name="Desserts"),
        }

        for category in categories.values():
            db.add(category)

        db.commit()
        print(f"Created {len(categories)} categories")

        # Refresh to get IDs
        for name, category in categories.items():
            db.refresh(category)

        print("Seeding menu items...")

        # Create menu items (prices in paise: ₹80 = 8000 paise)
        menu_items = [
            # South Indian
            models.MenuItem(
                name="Masala Dosa",
                description="Crispy dosa with spiced potato filling",
                price=8000,  # ₹80
                category_id=categories["South Indian"].id,
            ),
            models.MenuItem(
                name="Plain Dosa",
                description="Crispy rice crepe",
                price=6000,  # ₹60
                category_id=categories["South Indian"].id,
            ),
            models.MenuItem(
                name="Idli (2 pcs)",
                description="Steamed rice cakes with sambhar and chutney",
                price=5000,  # ₹50
                category_id=categories["South Indian"].id,
            ),
            models.MenuItem(
                name="Medu Vada (2 pcs)",
                description="Crispy lentil donuts",
                price=5000,  # ₹50
                category_id=categories["South Indian"].id,
            ),
            models.MenuItem(
                name="Rava Dosa",
                description="Crispy semolina dosa",
                price=7000,  # ₹70
                category_id=categories["South Indian"].id,
            ),
            models.MenuItem(
                name="Uttapam",
                description="Thick rice pancake with vegetables",
                price=7000,  # ₹70
                category_id=categories["South Indian"].id,
            ),
            # North Indian
            models.MenuItem(
                name="Chole Bhature",
                description="Chickpea curry with fried bread",
                price=10000,  # ₹100
                category_id=categories["North Indian"].id,
            ),
            models.MenuItem(
                name="Aloo Paratha",
                description="Potato stuffed flatbread with curd",
                price=8000,  # ₹80
                category_id=categories["North Indian"].id,
            ),
            models.MenuItem(
                name="Paneer Butter Masala",
                description="Cottage cheese in rich tomato gravy",
                price=14000,  # ₹140
                category_id=categories["North Indian"].id,
            ),
            models.MenuItem(
                name="Dal Makhani",
                description="Black lentils in creamy sauce",
                price=12000,  # ₹120
                category_id=categories["North Indian"].id,
            ),
            models.MenuItem(
                name="Rajma Chawal",
                description="Kidney beans curry with rice",
                price=10000,  # ₹100
                category_id=categories["North Indian"].id,
            ),
            # Beverages
            models.MenuItem(
                name="Filter Coffee",
                description="Traditional South Indian filter coffee",
                price=4000,  # ₹40
                category_id=categories["Beverages"].id,
            ),
            models.MenuItem(
                name="Masala Tea",
                description="Spiced Indian tea",
                price=2000,  # ₹20
                category_id=categories["Beverages"].id,
            ),
            models.MenuItem(
                name="Cold Coffee",
                description="Chilled coffee with ice cream",
                price=8000,  # ₹80
                category_id=categories["Beverages"].id,
            ),
            models.MenuItem(
                name="Lemon Soda",
                description="Fresh lime with soda",
                price=5000,  # ₹50
                category_id=categories["Beverages"].id,
            ),
            models.MenuItem(
                name="Buttermilk",
                description="Refreshing spiced yogurt drink",
                price=3000,  # ₹30
                category_id=categories["Beverages"].id,
            ),
            models.MenuItem(
                name="Mango Lassi",
                description="Sweet mango yogurt drink",
                price=7000,  # ₹70
                category_id=categories["Beverages"].id,
            ),
            # Snacks
            models.MenuItem(
                name="Samosa (2 pcs)",
                description="Crispy potato samosa",
                price=3000,  # ₹30
                category_id=categories["Snacks"].id,
            ),
            models.MenuItem(
                name="Veg Sandwich",
                description="Grilled vegetable sandwich",
                price=6000,  # ₹60
                category_id=categories["Snacks"].id,
            ),
            models.MenuItem(
                name="French Fries",
                description="Crispy golden fries",
                price=6000,  # ₹60
                category_id=categories["Snacks"].id,
            ),
            models.MenuItem(
                name="Veg Pakora",
                description="Assorted vegetable fritters",
                price=7000,  # ₹70
                category_id=categories["Snacks"].id,
            ),
            models.MenuItem(
                name="Paneer Tikka",
                description="Grilled cottage cheese cubes",
                price=12000,  # ₹120
                category_id=categories["Snacks"].id,
            ),
            # Desserts
            models.MenuItem(
                name="Gulab Jamun (2 pcs)",
                description="Sweet milk dumplings in sugar syrup",
                price=5000,  # ₹50
                category_id=categories["Desserts"].id,
            ),
            models.MenuItem(
                name="Ras Malai (2 pcs)",
                description="Cottage cheese in sweet cream",
                price=7000,  # ₹70
                category_id=categories["Desserts"].id,
            ),
            models.MenuItem(
                name="Gajar Halwa",
                description="Carrot pudding with nuts",
                price=6000,  # ₹60
                category_id=categories["Desserts"].id,
            ),
            models.MenuItem(
                name="Ice Cream",
                description="Choose your flavor",
                price=5000,  # ₹50
                category_id=categories["Desserts"].id,
            ),
        ]

        for item in menu_items:
            db.add(item)

        db.commit()
        print(f"Created {len(menu_items)} menu items")

        print("\n Database seeded successfully!")
        print("\nSample data includes:")
        for name, category in categories.items():
            count = len([item for item in menu_items if item.category_id == category.id])
            print(f"  - {name}: {count} items")

    except Exception as e:
        print(f"L Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
