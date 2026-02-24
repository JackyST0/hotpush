"""
测试配置和 fixtures
"""
import os
import pytest

os.environ.setdefault("ADMIN_PASSWORD", "test_password_123")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("DEBUG", "true")

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.middleware.auth import create_token


@pytest.fixture
def admin_token():
    return create_token({"sub": "admin", "role": "admin", "username": "admin"})


@pytest.fixture
def user_token():
    return create_token({"sub": "testuser", "role": "user", "username": "testuser"})


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
