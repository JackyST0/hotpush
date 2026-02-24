"""
基础健康检查和路由测试
"""
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_root_returns_ok(client):
    response = await client.get("/")
    assert response.status_code == 200
