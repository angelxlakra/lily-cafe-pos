"""
Pytest configuration and fixtures for Lily Cafe POS System tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.main import app
from app.api.deps import get_db


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_credentials():
    """Admin login credentials."""
    return {"username": "admin", "password": "changeme123"}


@pytest.fixture
def sample_category(db_session):
    """Create a sample category for testing."""
    from app.models.models import Category

    category = Category(name="Beverages")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def sample_menu_item(db_session, sample_category):
    """Create a sample menu item for testing."""
    from app.models.models import MenuItem

    item = MenuItem(
        name="Filter Coffee",
        description="South Indian filter coffee",
        price=4000,  # ₹40 in paise
        category_id=sample_category.id,
        is_available=True,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture
def auth_token(client, admin_credentials):
    """Get a valid JWT token for testing protected endpoints."""
    response = client.post("/api/v1/auth/login", json=admin_credentials)
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers with valid JWT token."""
    return {"Authorization": f"Bearer {auth_token}"}
