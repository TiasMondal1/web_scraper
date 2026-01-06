"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import User, SubscriptionPlan
from app.auth import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override"""
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
def test_user(db):
    """Create a test user"""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        full_name="Test User",
        email_verified=True,
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_plans(db):
    """Create test subscription plans"""
    plans = [
        SubscriptionPlan(
            name="free",
            display_name="Free",
            description="Free plan",
            price_monthly=0,
            price_yearly=0,
            max_products=3,
            max_alerts_per_day=5,
            max_price_checks_per_day=2,
            historical_data_days=30
        ),
        SubscriptionPlan(
            name="pro",
            display_name="Pro",
            description="Pro plan",
            price_monthly=499,
            price_yearly=4990,
            max_products=100,
            max_alerts_per_day=100,
            max_price_checks_per_day=24,
            api_access=True,
            data_export=True,
            historical_data_days=365
        )
    ]
    
    for plan in plans:
        db.add(plan)
    db.commit()
    
    return plans


@pytest.fixture
def auth_headers(client, test_user, test_plans):
    """Get authentication headers for test user"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
