"""
Pytest configuration and fixtures for Lily Cafe POS System tests.
Provides test database, client, and authentication utilities.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base  # Import Base with all models registered
from app.api.deps import get_db  # Import get_db from deps (used by endpoints)
from app.core.security import create_access_token
from app.models import models


# ============================================================================
# Test Database Setup
# ============================================================================


@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh test database for each test function.
    Uses in-memory SQLite for fast, isolated tests.
    """
    # Create in-memory SQLite database with StaticPool to ensure
    # all connections share the same in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign key constraints for SQLite
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables (models are already registered via app.db.base import)
    Base.metadata.create_all(bind=engine)

    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create session
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Alternative fixture name for database session (used by main branch tests).
    Create a fresh database session for each test.
    """
    # Create in-memory SQLite database with StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(test_db):
    """
    Alias for test_db to support ang-36 tests.
    """
    return test_db


@pytest.fixture(scope="function")
def client(test_db):
    """
    Create a test client with overridden database dependency.
    Uses test_db fixture for compatibility with ang-35 tests.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# Authentication Fixtures
# ============================================================================


@pytest.fixture
def admin_credentials():
    """Admin login credentials."""
    return {"username": "admin", "password": "changeme123"}


@pytest.fixture
def auth_token(client, admin_credentials):
    """
    Get a valid JWT token for testing protected endpoints.
    Authenticates via the login endpoint (realistic approach).
    """
    response = client.post("/api/v1/auth/login", json=admin_credentials)
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_token_direct():
    """
    Generate a valid JWT token directly for testing protected endpoints.
    Alternative to auth_token that doesn't require API call.
    """
    return create_access_token(data={"sub": "admin"})


@pytest.fixture
def auth_headers(auth_token):
    """Generate authentication headers for API requests."""
    return {"Authorization": f"Bearer {auth_token}"}


# ============================================================================
# Test Data Fixtures - Main Branch Style (Single Items)
# ============================================================================


@pytest.fixture
def sample_category(test_db):
    """Create a sample category for testing (main branch fixture)."""
    category = models.Category(name="Beverages")
    test_db.add(category)
    test_db.commit()
    test_db.refresh(category)
    return category


@pytest.fixture
def sample_menu_item(test_db, sample_category):
    """Create a sample menu item for testing (main branch fixture)."""
    item = models.MenuItem(
        name="Filter Coffee",
        description="South Indian filter coffee",
        price=4000,  # ₹40 in paise
        category_id=sample_category.id,
        is_available=True,
    )
    test_db.add(item)
    test_db.commit()
    test_db.refresh(item)
    return item


# ============================================================================
# Test Data Fixtures - ANG-35/ANG-36 Style (Multiple Items)
# ============================================================================


@pytest.fixture
def sample_categories(test_db):
    """Create sample categories for testing (ang-35/ang-36 fixture)."""
    categories = [
        models.Category(name="South Indian"),
        models.Category(name="North Indian"),
        models.Category(name="Beverages"),
        models.Category(name="Snacks"),
        models.Category(name="Desserts"),
    ]

    for category in categories:
        test_db.add(category)

    test_db.commit()

    for category in categories:
        test_db.refresh(category)

    return categories


@pytest.fixture
def sample_menu_items(test_db, sample_categories):
    """Create sample menu items for testing (ang-35/ang-36 fixture)."""
    menu_items = [
        models.MenuItem(
            name="Masala Dosa",
            description="Crispy dosa with spiced potato filling",
            price=8000,  # ₹80 in paise
            category_id=sample_categories[0].id,  # South Indian
            is_available=True,
        ),
        models.MenuItem(
            name="Filter Coffee",
            description="Traditional South Indian filter coffee",
            price=4000,  # ₹40 in paise
            category_id=sample_categories[2].id,  # Beverages
            is_available=True,
        ),
        models.MenuItem(
            name="Samosa",
            description="Crispy potato samosa",
            price=3000,  # ₹30 in paise
            category_id=sample_categories[3].id,  # Snacks
            is_available=False,  # Out of stock
        ),
    ]

    for item in menu_items:
        test_db.add(item)

    test_db.commit()

    for item in menu_items:
        test_db.refresh(item)

    return menu_items


@pytest.fixture
def sample_order(test_db, sample_menu_items):
    """Create a sample order for testing (ang-35/ang-36 fixture)."""
    order = models.Order(
        order_number="ORD-20241031-0001",
        table_number=5,
        customer_name="Test Customer",
        subtotal=12000,  # ₹120
        gst_amount=2160,  # 18% of 12000
        total_amount=14160,  # ₹141.60
        status=models.OrderStatus.ACTIVE,
    )

    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)

    # Add order items
    order_items = [
        models.OrderItem(
            order_id=order.id,
            menu_item_id=sample_menu_items[0].id,
            menu_item_name=sample_menu_items[0].name,
            quantity=1,
            unit_price=sample_menu_items[0].price,
            subtotal=sample_menu_items[0].price,
        ),
        models.OrderItem(
            order_id=order.id,
            menu_item_id=sample_menu_items[1].id,
            menu_item_name=sample_menu_items[1].name,
            quantity=1,
            unit_price=sample_menu_items[1].price,
            subtotal=sample_menu_items[1].price,
        ),
    ]

    for item in order_items:
        test_db.add(item)

    test_db.commit()

    for item in order_items:
        test_db.refresh(item)

    return order


# ============================================================================
# Helper Functions / Factory Fixtures
# ============================================================================


@pytest.fixture
def create_test_category(test_db):
    """Factory fixture to create test categories."""
    def _create_category(name: str):
        category = models.Category(name=name)
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)
        return category

    return _create_category


@pytest.fixture
def create_test_menu_item(test_db, sample_categories):
    """Factory fixture to create test menu items."""
    def _create_menu_item(name: str, price: int, category_id: int = None):
        if category_id is None:
            category_id = sample_categories[0].id

        item = models.MenuItem(
            name=name,
            description=f"Test description for {name}",
            price=price,
            category_id=category_id,
            is_available=True,
        )
        test_db.add(item)
        test_db.commit()
        test_db.refresh(item)
        return item

    return _create_menu_item

@pytest.fixture
def paid_order(test_db, sample_menu_items):
    """Create a paid order for testing."""
    from app import crud
    from app.schemas.schemas import OrderCreate, PaymentCreate
    from app.models.models import OrderStatus

    order_data = OrderCreate(
        table_number=5,
        customer_name="Paid Customer",
        items=[{"menu_item_id": sample_menu_items[0].id, "quantity": 1}]
    )
    order = crud.create_order(test_db, order_data)

    payment_data = PaymentCreate(
        payment_method="cash",
        amount=order.total_amount
    )
    crud.create_payment(test_db, order.id, payment_data)

    test_db.refresh(order)
    return order

