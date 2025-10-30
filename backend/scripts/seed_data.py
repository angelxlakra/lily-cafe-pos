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

        # Create categories
        categories = {
            "Coffee": models.Category(name="Coffee"),
            "Tea": models.Category(name="Tea"),
            "Cold Beverages": models.Category(name="Cold Beverages"),
            "Snacks": models.Category(name="Snacks"),
            "Breakfast": models.Category(name="Breakfast"),
            "Meals": models.Category(name="Meals"),
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

        # Create menu items (prices in paise: �80 = 8000 paise)
        menu_items = [
            # Coffee
            models.MenuItem(
                name="Espresso",
                description="Strong shot of Italian coffee",
                price=6000,  # �60
                category_id=categories["Coffee"].id,
            ),
            models.MenuItem(
                name="Cappuccino",
                description="Espresso with steamed milk and foam",
                price=9000,  # �90
                category_id=categories["Coffee"].id,
            ),
            models.MenuItem(
                name="Latte",
                description="Espresso with steamed milk",
                price=10000,  # �100
                category_id=categories["Coffee"].id,
            ),
            models.MenuItem(
                name="Americano",
                description="Espresso with hot water",
                price=7000,  # �70
                category_id=categories["Coffee"].id,
            ),
            models.MenuItem(
                name="Mocha",
                description="Chocolate flavored coffee",
                price=11000,  # �110
                category_id=categories["Coffee"].id,
            ),
            # Tea
            models.MenuItem(
                name="Masala Chai",
                description="Spiced Indian tea",
                price=4000,  # �40
                category_id=categories["Tea"].id,
            ),
            models.MenuItem(
                name="Green Tea",
                description="Healthy green tea",
                price=5000,  # �50
                category_id=categories["Tea"].id,
            ),
            models.MenuItem(
                name="Lemon Tea",
                description="Refreshing tea with lemon",
                price=5000,  # �50
                category_id=categories["Tea"].id,
            ),
            # Cold Beverages
            models.MenuItem(
                name="Cold Coffee",
                description="Chilled coffee with ice cream",
                price=12000,  # �120
                category_id=categories["Cold Beverages"].id,
            ),
            models.MenuItem(
                name="Iced Tea",
                description="Chilled lemon iced tea",
                price=8000,  # �80
                category_id=categories["Cold Beverages"].id,
            ),
            models.MenuItem(
                name="Fresh Lime Soda",
                description="Tangy lime with soda",
                price=6000,  # �60
                category_id=categories["Cold Beverages"].id,
            ),
            models.MenuItem(
                name="Mango Smoothie",
                description="Fresh mango smoothie",
                price=13000,  # �130
                category_id=categories["Cold Beverages"].id,
            ),
            # Snacks
            models.MenuItem(
                name="Samosa (2 pcs)",
                description="Crispy potato samosa",
                price=4000,  # �40
                category_id=categories["Snacks"].id,
            ),
            models.MenuItem(
                name="Veg Sandwich",
                description="Grilled vegetable sandwich",
                price=8000,  # �80
                category_id=categories["Snacks"].id,
            ),
            models.MenuItem(
                name="Paneer Sandwich",
                description="Grilled paneer sandwich",
                price=10000,  # �100
                category_id=categories["Snacks"].id,
            ),
            models.MenuItem(
                name="French Fries",
                description="Crispy golden fries",
                price=7000,  # �70
                category_id=categories["Snacks"].id,
            ),
            models.MenuItem(
                name="Veg Pakora",
                description="Assorted vegetable fritters",
                price=8000,  # �80
                category_id=categories["Snacks"].id,
            ),
            # Breakfast
            models.MenuItem(
                name="Poha",
                description="Flattened rice with spices",
                price=6000,  # �60
                category_id=categories["Breakfast"].id,
            ),
            models.MenuItem(
                name="Upma",
                description="Semolina with vegetables",
                price=6000,  # �60
                category_id=categories["Breakfast"].id,
            ),
            models.MenuItem(
                name="Idli Sambhar (3 pcs)",
                description="Steamed rice cakes with sambhar",
                price=8000,  # �80
                category_id=categories["Breakfast"].id,
            ),
            models.MenuItem(
                name="Masala Dosa",
                description="Crispy dosa with potato filling",
                price=9000,  # �90
                category_id=categories["Breakfast"].id,
            ),
            models.MenuItem(
                name="Aloo Paratha with Curd",
                description="Potato stuffed flatbread",
                price=10000,  # �100
                category_id=categories["Breakfast"].id,
            ),
            # Meals
            models.MenuItem(
                name="Veg Thali",
                description="Complete vegetarian meal",
                price=15000,  # �150
                category_id=categories["Meals"].id,
            ),
            models.MenuItem(
                name="Dal Khichdi",
                description="Rice and lentil comfort food",
                price=12000,  # �120
                category_id=categories["Meals"].id,
            ),
            models.MenuItem(
                name="Chole Bhature",
                description="Chickpea curry with fried bread",
                price=14000,  # �140
                category_id=categories["Meals"].id,
            ),
            models.MenuItem(
                name="Paneer Butter Masala with Roti",
                description="Rich paneer curry with flatbread",
                price=16000,  # �160
                category_id=categories["Meals"].id,
            ),
            # Desserts
            models.MenuItem(
                name="Gulab Jamun (2 pcs)",
                description="Sweet milk dumplings",
                price=6000,  # �60
                category_id=categories["Desserts"].id,
            ),
            models.MenuItem(
                name="Ras Malai (2 pcs)",
                description="Cottage cheese in sweet cream",
                price=8000,  # �80
                category_id=categories["Desserts"].id,
            ),
            models.MenuItem(
                name="Ice Cream",
                description="Choose your flavor",
                price=7000,  # �70
                category_id=categories["Desserts"].id,
            ),
            models.MenuItem(
                name="Brownie with Ice Cream",
                description="Chocolate brownie with vanilla ice cream",
                price=12000,  # �120
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
