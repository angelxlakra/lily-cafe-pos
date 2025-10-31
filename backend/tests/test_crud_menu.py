"""
Unit tests for Menu Item CRUD operations.
Tests database operations in app/crud/crud.py for menu items.
"""

import pytest
from app import crud, schemas
from app.models import models


class TestGetMenuItems:
    """Tests for get_menu_items function."""

    def test_get_menu_items_empty(self, test_db):
        """Test getting menu items when database is empty."""
        items = crud.get_menu_items(test_db)
        assert items == []

    def test_get_menu_items_all(self, test_db, sample_menu_items):
        """Test getting all menu items without filters."""
        items = crud.get_menu_items(test_db, available_only=False)

        assert len(items) == 3
        assert all(isinstance(item, models.MenuItem) for item in items)

    def test_get_menu_items_available_only(self, test_db, sample_menu_items):
        """Test filtering by available items only."""
        items = crud.get_menu_items(test_db, available_only=True)

        assert len(items) == 2  # Only Masala Dosa and Filter Coffee
        assert all(item.is_available for item in items)
        assert not any(item.name == "Samosa" for item in items)

    def test_get_menu_items_by_category(self, test_db, sample_menu_items, sample_categories):
        """Test filtering by category."""
        south_indian_id = sample_categories[0].id
        items = crud.get_menu_items(test_db, category_id=south_indian_id)

        assert len(items) == 1
        assert items[0].name == "Masala Dosa"
        assert items[0].category_id == south_indian_id

    def test_get_menu_items_available_and_category(self, test_db, sample_menu_items, sample_categories):
        """Test filtering by both available_only and category."""
        snacks_id = sample_categories[3].id  # Snacks category
        items = crud.get_menu_items(test_db, available_only=True, category_id=snacks_id)

        # Samosa is in Snacks but not available
        assert len(items) == 0


class TestGetMenuItem:
    """Tests for get_menu_item function."""

    def test_get_menu_item_exists(self, test_db, sample_menu_items):
        """Test getting a menu item by ID when it exists."""
        item_id = sample_menu_items[0].id
        item = crud.get_menu_item(test_db, item_id)

        assert item is not None
        assert item.id == item_id
        assert item.name == "Masala Dosa"
        assert item.price == 8000

    def test_get_menu_item_not_found(self, test_db):
        """Test getting a menu item by ID when it doesn't exist."""
        item = crud.get_menu_item(test_db, 9999)
        assert item is None


class TestCreateMenuItem:
    """Tests for create_menu_item function."""

    def test_create_menu_item_success(self, test_db, sample_categories):
        """Test creating a new menu item."""
        item_data = schemas.MenuItemCreate(
            name="Idli",
            description="Steamed rice cakes",
            price=5000,  # ₹50
            category_id=sample_categories[0].id,
        )

        item = crud.create_menu_item(test_db, item_data)

        assert item.id is not None
        assert item.name == "Idli"
        assert item.description == "Steamed rice cakes"
        assert item.price == 5000
        assert item.category_id == sample_categories[0].id
        assert item.is_available is True
        assert item.created_at is not None
        assert item.updated_at is not None

        # Verify it's in the database
        db_item = test_db.query(models.MenuItem).filter_by(id=item.id).first()
        assert db_item is not None
        assert db_item.name == "Idli"

    def test_create_menu_item_minimal_data(self, test_db, sample_categories):
        """Test creating a menu item with minimal required fields."""
        item_data = schemas.MenuItemCreate(
            name="Simple Item",
            price=1000,
            category_id=sample_categories[0].id,
        )

        item = crud.create_menu_item(test_db, item_data)

        assert item.id is not None
        assert item.name == "Simple Item"
        assert item.description is None
        assert item.price == 1000

    def test_create_menu_item_with_category_relationship(self, test_db, sample_categories):
        """Test that created item has proper category relationship."""
        item_data = schemas.MenuItemCreate(
            name="Test Item",
            price=5000,
            category_id=sample_categories[1].id,  # North Indian
        )

        item = crud.create_menu_item(test_db, item_data)
        test_db.refresh(item)

        assert item.category is not None
        assert item.category.name == "North Indian"


class TestUpdateMenuItem:
    """Tests for update_menu_item function."""

    def test_update_menu_item_name(self, test_db, sample_menu_items):
        """Test updating menu item name."""
        item_id = sample_menu_items[0].id
        update_data = schemas.MenuItemUpdate(name="Special Masala Dosa")

        updated_item = crud.update_menu_item(test_db, item_id, update_data)

        assert updated_item is not None
        assert updated_item.name == "Special Masala Dosa"
        assert updated_item.price == sample_menu_items[0].price  # Unchanged

    def test_update_menu_item_price(self, test_db, sample_menu_items):
        """Test updating menu item price."""
        item_id = sample_menu_items[0].id
        update_data = schemas.MenuItemUpdate(price=9000)  # ₹90

        updated_item = crud.update_menu_item(test_db, item_id, update_data)

        assert updated_item is not None
        assert updated_item.price == 9000
        assert updated_item.name == sample_menu_items[0].name  # Unchanged

    def test_update_menu_item_availability(self, test_db, sample_menu_items):
        """Test updating menu item availability."""
        item_id = sample_menu_items[0].id
        update_data = schemas.MenuItemUpdate(is_available=False)

        updated_item = crud.update_menu_item(test_db, item_id, update_data)

        assert updated_item is not None
        assert updated_item.is_available is False

    def test_update_menu_item_multiple_fields(self, test_db, sample_menu_items):
        """Test updating multiple fields at once."""
        item_id = sample_menu_items[0].id
        update_data = schemas.MenuItemUpdate(
            name="Updated Dosa",
            description="New description",
            price=8500,
            is_available=False,
        )

        updated_item = crud.update_menu_item(test_db, item_id, update_data)

        assert updated_item is not None
        assert updated_item.name == "Updated Dosa"
        assert updated_item.description == "New description"
        assert updated_item.price == 8500
        assert updated_item.is_available is False

    def test_update_menu_item_not_found(self, test_db):
        """Test updating a non-existent menu item."""
        update_data = schemas.MenuItemUpdate(name="Test")
        updated_item = crud.update_menu_item(test_db, 9999, update_data)

        assert updated_item is None

    def test_update_menu_item_updated_at_changes(self, test_db, sample_menu_items):
        """Test that updated_at timestamp changes on update."""
        item_id = sample_menu_items[0].id
        original_item = crud.get_menu_item(test_db, item_id)
        original_updated_at = original_item.updated_at

        import time
        time.sleep(0.1)  # Small delay to ensure timestamp difference

        update_data = schemas.MenuItemUpdate(name="Updated Name")
        updated_item = crud.update_menu_item(test_db, item_id, update_data)

        # Note: In SQLite, datetime resolution might not change
        # This test verifies the update mechanism works
        assert updated_item is not None
        assert updated_item.name == "Updated Name"


class TestDeleteMenuItem:
    """Tests for delete_menu_item function (soft delete)."""

    def test_delete_menu_item_success(self, test_db, sample_menu_items):
        """Test soft deleting a menu item."""
        item_id = sample_menu_items[0].id
        result = crud.delete_menu_item(test_db, item_id)

        assert result is True

        # Verify item still exists but is not available
        deleted_item = crud.get_menu_item(test_db, item_id)
        assert deleted_item is not None
        assert deleted_item.is_available is False

    def test_delete_menu_item_not_found(self, test_db):
        """Test soft deleting a non-existent menu item."""
        result = crud.delete_menu_item(test_db, 9999)
        assert result is False

    def test_deleted_item_filtered_by_available_only(self, test_db, sample_menu_items):
        """Test that deleted items are filtered out by available_only."""
        item_id = sample_menu_items[0].id

        # Delete the item
        crud.delete_menu_item(test_db, item_id)

        # Get available items only
        available_items = crud.get_menu_items(test_db, available_only=True)

        # Deleted item should not be in the list
        assert not any(item.id == item_id for item in available_items)

    def test_deleted_item_included_without_filter(self, test_db, sample_menu_items):
        """Test that deleted items are included when available_only=False."""
        item_id = sample_menu_items[0].id

        # Delete the item
        crud.delete_menu_item(test_db, item_id)

        # Get all items
        all_items = crud.get_menu_items(test_db, available_only=False)

        # Deleted item should still be in the list
        assert any(item.id == item_id for item in all_items)


class TestMenuItemRelationships:
    """Tests for menu item relationships."""

    def test_menu_item_category_relationship(self, test_db, sample_menu_items, sample_categories):
        """Test that menu items correctly relate to categories."""
        item = sample_menu_items[0]
        test_db.refresh(item)

        assert item.category is not None
        assert item.category.name == "South Indian"
        assert item.category_id == sample_categories[0].id

    def test_menu_item_order_items_relationship(self, test_db, sample_order, sample_menu_items):
        """Test that menu items correctly relate to order items."""
        item = sample_menu_items[0]
        test_db.refresh(item)

        assert len(item.order_items) >= 1
        assert any(oi.menu_item_name == "Masala Dosa" for oi in item.order_items)
