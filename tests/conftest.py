"""
Global test configuration and fixtures
"""
import pytest
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def services_urls():
    """Service URLs for integration tests"""
    base_url = os.getenv("BASE_URL", "http://localhost")
    return {
        "auth": f"{base_url}:8001",
        "taxonomie": f"{base_url}:8002",
        "presidio": f"{base_url}:8003",
        "cleaning": f"{base_url}:8004",
        "classification": f"{base_url}:8005",
        "correction": f"{base_url}:8006",
        "annotation": f"{base_url}:8007",
        "quality": f"{base_url}:8008",
        "ethimask": f"{base_url}:8009",
        "nginx": f"{base_url}:8000",
    }

@pytest.fixture(scope="session")
async def test_db():
    """Setup test database"""
    mongodb_uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(mongodb_uri)
    db = client["DataGovDB"]
    yield db
    client.close()

@pytest.fixture
def admin_credentials():
    """Admin user credentials for testing"""
    return {
        "username": "admin",
        "password": "admin123"
    }
