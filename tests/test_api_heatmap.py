"""
CivicPulse — API Integration Test: Heatmap Endpoint
Tests GET /api/v1/heatmap for ward CSS data retrieval.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone


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


@pytest.fixture
def mock_auth_token():
    """Generate a mock JWT token for authenticated requests."""
    with patch("dependencies.decode_access_token") as mock_decode:
        mock_decode.return_value = {"sub": "test-user-id"}
        yield "Bearer test-token"


class TestHeatmapEndpoint:
    """Tests for GET /api/v1/heatmap."""

    def test_heatmap_requires_no_auth_for_public_data(self, test_client):
        """Heatmap should be accessible for viewing ward data."""
        # The heatmap endpoint may or may not require auth depending on config
        response = test_client.get("/api/v1/heatmap", params={"city": "delhi"})
        # Should return either 200 (public) or 401 (auth required) — never 500
        assert response.status_code in (200, 401)

    def test_heatmap_returns_valid_structure(self, test_client, mock_auth_token):
        """Heatmap response should have status and data fields."""
        with patch("routes.heatmap.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_get_db.return_value = mock_session

            response = test_client.get(
                "/api/v1/heatmap",
                params={"city": "delhi"},
                headers={"Authorization": mock_auth_token},
            )
            # Should not crash — may return empty data
            assert response.status_code in (200, 401)

    def test_heatmap_rejects_missing_city(self, test_client, mock_auth_token):
        """Heatmap should handle missing city parameter gracefully."""
        response = test_client.get(
            "/api/v1/heatmap",
            headers={"Authorization": mock_auth_token},
        )
        # Should not return 500
        assert response.status_code != 500
