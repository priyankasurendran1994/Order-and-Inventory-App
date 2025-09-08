import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.core.config import settings
from sqlalchemy.engine.url import make_url

# Use SQLite for test DB only
SQLALCHEMY_DATABASE_URL = settings.database_url

# Parse URL to check the DB type
url = make_url(SQLALCHEMY_DATABASE_URL)

if url.drivername.startswith("sqlite"):
    # SQLite-specific args
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL or other DBs
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Drop & recreate tables before each test for isolation"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def db_session():
    """Provide a database session for tests"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session):
    """Override get_db dependency"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def sample_product_data():
    return {
        "name": "Test Product",
        "price": 99.99,
        "stock": 10
    }

@pytest.fixture
def sample_order_data():
    return {
        "items": [
            {"product_id": 1, "quantity": 2}
        ]
    }
