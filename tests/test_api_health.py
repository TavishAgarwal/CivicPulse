"""
CivicPulse — API Integration Test: Health Endpoint
Tests GET /health for system status, dependency checks, and degraded mode.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture
def test_client():
    """Create a FastAPI TestClient with mocked settings."""
    with patch.dict("os.environ", {
        "CIVICPULSE_ENV": "development",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "REDIS_URL": "redis://localhost:6379/0",
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "KAFKA_BOOTSTRAP_SERVERS": "",
    }):
        from fastapi.testclient import TestClient
        from main import app
        yield TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self, test_client):
        """Health endpoint should always return 200 even if dependencies are down."""
        # Mock asyncpg.connect to fail and redis to fail
        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(side_effect=Exception("DB down"))
        with patch.dict("sys.modules", {"asyncpg": mock_asyncpg}), \
             patch("routes.health.redis_lib") as mock_redis:
            mock_redis.from_url.return_value.ping.side_effect = Exception("Redis down")
            response = test_client.get("/health")
        assert response.status_code == 200

    def test_health_returns_required_fields(self, test_client):
        """Health response must include status, version, and dependency checks."""
        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(side_effect=Exception("down"))
        with patch.dict("sys.modules", {"asyncpg": mock_asyncpg}), \
             patch("routes.health.redis_lib") as mock_redis:
            mock_redis.from_url.return_value.ping.side_effect = Exception("down")
            response = test_client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] in ("healthy", "degraded")
        assert "version" in data
        assert "environment" in data
        assert "db_connected" in data
        assert "redis_connected" in data

    def test_health_degraded_when_db_down(self, test_client):
        """Status should be 'degraded' when database is unreachable."""
        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(side_effect=Exception("DB connection failed"))
        with patch.dict("sys.modules", {"asyncpg": mock_asyncpg}), \
             patch("routes.health.redis_lib") as mock_redis:
            mock_redis.from_url.return_value.ping.side_effect = Exception("down")
            response = test_client.get("/health")
        data = response.json()
        assert data["status"] == "degraded"
        assert data["db_connected"] is False

    def test_health_shows_integration_status(self, test_client):
        """Health should report integration availability."""
        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(side_effect=Exception("down"))
        with patch.dict("sys.modules", {"asyncpg": mock_asyncpg}), \
             patch("routes.health.redis_lib") as mock_redis:
            mock_redis.from_url.return_value.ping.side_effect = Exception("down")
            response = test_client.get("/health")
        data = response.json()

        assert "integrations" in data
        assert "whatsapp" in data["integrations"]
        assert "sms" in data["integrations"]
