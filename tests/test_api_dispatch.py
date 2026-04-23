"""
CivicPulse — API Integration Test: Dispatch Endpoint
Tests POST /api/v1/dispatch/suggest for volunteer matching.
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


class TestDispatchSuggestEndpoint:
    """Tests for POST /api/v1/dispatch/suggest."""

    def test_suggest_requires_authentication(self, test_client):
        """Dispatch suggest should return 401 without a valid token."""
        response = test_client.post(
            "/api/v1/dispatch/suggest",
            json={"ward_id": "ward-001", "required_skills": ["medical"]},
        )
        assert response.status_code == 401

    def test_suggest_returns_structured_error(self, test_client):
        """401 response should have structured error body, not raw traceback."""
        response = test_client.post(
            "/api/v1/dispatch/suggest",
            json={"ward_id": "ward-001"},
        )
        data = response.json()
        assert "detail" in data
        # Should have structured error, not a raw string
        if isinstance(data["detail"], dict):
            assert "code" in data["detail"]
            assert "message" in data["detail"]

    def test_suggest_rejects_empty_body(self, test_client):
        """Dispatch suggest should reject requests with no body."""
        response = test_client.post("/api/v1/dispatch/suggest")
        # Should return 401 (no auth) or 422 (validation error) — never 500
        assert response.status_code in (401, 422)


class TestDispatchConfirmEndpoint:
    """Tests for POST /api/v1/dispatch/confirm."""

    def test_confirm_requires_authentication(self, test_client):
        """Dispatch confirm should return 401 without a valid token."""
        response = test_client.post(
            "/api/v1/dispatch/confirm",
            json={"ward_id": "ward-001", "volunteer_id": "vol-001"},
        )
        assert response.status_code == 401

    def test_confirm_rejects_empty_body(self, test_client):
        """Confirm should reject requests with no body."""
        response = test_client.post("/api/v1/dispatch/confirm")
        assert response.status_code in (401, 422)
