"""
Unit tests for Category CRUD operations.
Tests database operations in app/crud/crud.py for categories.
"""

import pytest
from app import crud, schemas
from app.models import models


class TestGetCategories:
    """Tests for get_categories function."""

    def test_get_categories_empty(self, test_db):
        """Test getting categories when database is empty."""
        categories = crud.get_categories(test_db)
        assert categories == []

    def test_get_categories_with_data(self, test_db, sample_categories):
        """Test getting all categories."""
        categories = crud.get_categories(test_db)

        assert len(categories) == 5
        assert all(isinstance(cat, models.Category) for cat in categories)

        # Verify category names
        category_names = [cat.name for cat in categories]
        assert "South Indian" in category_names
        assert "Beverages" in category_names
        assert "Desserts" in category_names


class TestGetCategory:
    """Tests for get_category function."""

    def test_get_category_exists(self, test_db, sample_categories):
        """Test getting a category by ID when it exists."""
        category_id = sample_categories[0].id
        category = crud.get_category(test_db, category_id)

        assert category is not None
        assert category.id == category_id
        assert category.name == "South Indian"

    def test_get_category_not_found(self, test_db, sample_categories):
        """Test getting a category by ID when it doesn't exist."""
        category = crud.get_category(test_db, 9999)
        assert category is None


class TestCreateCategory:
    """Tests for create_category function."""

    def test_create_category_success(self, test_db):
        """Test creating a new category."""
        category_data = schemas.CategoryCreate(name="Italian")
        category = crud.create_category(test_db, category_data)

        assert category.id is not None
        assert category.name == "Italian"
        assert category.created_at is not None

        # Verify it's in the database
        db_category = test_db.query(models.Category).filter_by(id=category.id).first()
        assert db_category is not None
        assert db_category.name == "Italian"

    def test_create_category_duplicate_name(self, test_db, sample_categories):
        """Test creating a category with duplicate name fails."""
        category_data = schemas.CategoryCreate(name="South Indian")

        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            crud.create_category(test_db, category_data)
            test_db.commit()

    def test_create_multiple_categories(self, test_db):
        """Test creating multiple categories."""
        categories_data = [
            schemas.CategoryCreate(name="Italian"),
            schemas.CategoryCreate(name="Chinese"),
            schemas.CategoryCreate(name="Mexican"),
        ]

        created_categories = []
        for data in categories_data:
            category = crud.create_category(test_db, data)
            created_categories.append(category)

        assert len(created_categories) == 3

        # Verify all are in database
        all_categories = crud.get_categories(test_db)
        assert len(all_categories) == 3

        category_names = [cat.name for cat in all_categories]
        assert "Italian" in category_names
        assert "Chinese" in category_names
        assert "Mexican" in category_names


class TestCategoryRelationships:
    """Tests for category relationships with menu items."""

    def test_category_menu_items_relationship(self, test_db, sample_categories, sample_menu_items):
        """Test that categories correctly relate to menu items."""
        south_indian = sample_categories[0]  # South Indian category

        # Refresh to load relationships
        test_db.refresh(south_indian)

        # Check menu items relationship
        assert len(south_indian.menu_items) >= 1
        assert any(item.name == "Masala Dosa" for item in south_indian.menu_items)

    def test_category_without_menu_items(self, test_db, create_test_category):
        """Test category with no menu items."""
        category = create_test_category("Empty Category")

        test_db.refresh(category)
        assert len(category.menu_items) == 0
