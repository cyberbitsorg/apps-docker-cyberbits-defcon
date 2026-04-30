import os
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

from routers.health import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_health_returns_only_status_key():
    with (
        patch("routers.health.get_pool", new_callable=AsyncMock) as mock_pool,
        patch("routers.health.get_redis", new_callable=AsyncMock) as mock_redis,
    ):
        mock_pool.return_value.fetchval = AsyncMock(return_value=1)
        mock_redis.return_value.ping = AsyncMock(return_value=True)

        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"status"}
    assert body["status"] == "ok"


def test_health_returns_503_when_db_fails():
    with (
        patch("routers.health.get_pool", new_callable=AsyncMock) as mock_pool,
        patch("routers.health.get_redis", new_callable=AsyncMock) as mock_redis,
    ):
        mock_pool.return_value.fetchval = AsyncMock(side_effect=Exception("db down"))
        mock_redis.return_value.ping = AsyncMock(return_value=True)

        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded"}


def test_health_does_not_expose_service_names():
    with (
        patch("routers.health.get_pool", new_callable=AsyncMock) as mock_pool,
        patch("routers.health.get_redis", new_callable=AsyncMock) as mock_redis,
    ):
        mock_pool.return_value.fetchval = AsyncMock(return_value=1)
        mock_redis.return_value.ping = AsyncMock(return_value=True)

        response = client.get("/health")

    body = response.json()
    assert "database" not in body
    assert "redis" not in body
