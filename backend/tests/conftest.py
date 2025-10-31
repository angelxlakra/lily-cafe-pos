"""
Pytest configuration and shared fixtures for Lily Cafe POS tests.
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.db.session import Base, get_db
from app.models.models import Category, MenuItem


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test function.

    This fixture:
    - Creates all tables before the test
    - Yields a database session
    - Drops all tables after the test
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> TestClient:
    """
    Create a test client with database dependency override.

    This client can be used to make requests to the API during tests.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_category(db: Session) -> Category:
    """Create a sample category for testing."""
    category = Category(name="Test Category")
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def sample_menu_items(db: Session, sample_category: Category) -> list[MenuItem]:
    """Create sample menu items for testing."""
    items = [
        MenuItem(
            name="Masala Dosa",
            description="Crispy dosa with potato filling",
            price=8000,  # ₹80 in paise
            category_id=sample_category.id,
            is_available=True,
        ),
        MenuItem(
            name="Filter Coffee",
            description="South Indian filter coffee",
            price=4000,  # ₹40 in paise
            category_id=sample_category.id,
            is_available=True,
        ),
        MenuItem(
            name="Idli (2 pcs)",
            description="Steamed rice cakes",
            price=5000,  # ₹50 in paise
            category_id=sample_category.id,
            is_available=True,
        ),
    ]
    for item in items:
        db.add(item)
    db.commit()
    for item in items:
        db.refresh(item)
    return items


@pytest.fixture
def auth_token(client: TestClient) -> str:
    """
    Get an authentication token for admin user.

    Note: This assumes auth endpoints are implemented.
    Modify based on actual auth implementation.
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "changeme123"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return ""


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Get authorization headers with bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}
