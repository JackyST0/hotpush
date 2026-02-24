"""
认证模块测试
"""
import pytest
from app.middleware.auth import create_token, verify_token, is_public_path


class TestTokenOperations:
    def test_create_and_verify_token(self):
        data = {"sub": "admin", "role": "admin", "username": "admin"}
        token = create_token(data)
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "admin"
        assert payload["role"] == "admin"

    def test_verify_invalid_token(self):
        payload = verify_token("invalid.token.here")
        assert payload is None

    def test_verify_empty_token(self):
        payload = verify_token("")
        assert payload is None


class TestPublicPaths:
    @pytest.mark.parametrize("path", [
        "/", "/health", "/docs", "/openapi.json",
        "/api/auth/login", "/api/auth/register", "/api/auth/check",
        "/api/stats", "/static/main.js",
    ])
    def test_public_paths(self, path):
        assert is_public_path(path) is True

    @pytest.mark.parametrize("path", [
        "/api/hot", "/api/push/test", "/api/config/channels",
        "/api/users", "/api/rules",
    ])
    def test_protected_paths(self, path):
        assert is_public_path(path) is False


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client):
        response = await client.get("/api/hot")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_valid_token(self, client, admin_token):
        response = await client.get(
            "/api/sources",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_login_with_correct_credentials(self, client):
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "test_password_123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data

    @pytest.mark.asyncio
    async def test_login_with_wrong_password(self, client):
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong_password"}
        )
        assert response.status_code == 401
