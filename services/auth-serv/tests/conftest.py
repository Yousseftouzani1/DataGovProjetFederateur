"""
conftest.py - Pytest fixtures for auth service tests
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "password": "TestPassword123",
        "role": "steward",
        "email": "test@example.com"
    }

@pytest.fixture
def sample_admin_data():
    """Sample admin user data"""
    return {
        "username": "adminuser",
        "password": "AdminPass456",
        "role": "admin",
        "email": "admin@example.com"
    }

@pytest.fixture
def valid_jwt_token():
    """Generate a valid JWT token for testing"""
    from backend.auth.utils import create_token
    return create_token({"sub": "testuser", "role": "steward"})

@pytest.fixture
def admin_jwt_token():
    """Generate an admin JWT token for testing"""
    from backend.auth.utils import create_token
    return create_token({"sub": "admin", "role": "admin"})

@pytest.fixture
def expired_jwt_token():
    """Generate an expired JWT token for testing"""
    from jose import jwt
    from datetime import datetime, timedelta
    from backend.auth.utils import SECRET_KEY, ALGORITHM
    
    data = {
        "sub": "testuser",
        "role": "steward",
        "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
