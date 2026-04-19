"""
CivicPulse — Shared Test Fixtures
Provides mock DB, Redis, sample data, and common helpers.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

# Ensure src modules are importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for subdir in ["src/ingestion", "src/ml", "src/dispatch", "src/api"]:
    path = os.path.join(ROOT, subdir)
    if path not in sys.path:
        sys.path.insert(0, path)


# ── Sample Data ─────────────────────────────────────────────

@pytest.fixture
def sample_signal():
    """A valid UnifiedSignal-compatible dict."""
    return {
        "source": "pharmacy_api",
        "location_pin": "WARD-DEL-001",
        "signal_type": "pharmacy",
        "intensity_score": 0.72,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.85,
    }


@pytest.fixture
def sample_signal_with_pii():
    """A signal dict with PII fields that should be stripped."""
    return {
        "source": "pharmacy_api",
        "location_pin": "WARD-DEL-001",
        "signal_type": "pharmacy",
        "intensity_score": 0.72,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.85,
        "name": "John Doe",
        "phone": "+919876543210",
        "email": "john@example.com",
        "aadhaar": "1234-5678-9012",
        "address": "123 Street, Delhi",
    }


@pytest.fixture
def sample_volunteer():
    """A sample volunteer profile dict."""
    return {
        "volunteer_id": "vol-001",
        "skills": ["medical", "logistics"],
        "availability": {"days": ["Mon", "Wed", "Fri"], "hours": ["09:00-17:00"]},
        "max_radius_km": 10,
        "fatigue_score": 0.2,
        "performance_rating": 4.5,
        "lat": 28.6139,
        "lng": 77.2090,
    }


@pytest.fixture
def sample_ward():
    """A sample ward dict."""
    return {
        "id": "ward-001",
        "ward_code": "WARD-DEL-001",
        "name": "Ward 1",
        "city_id": "delhi",
        "lat": 28.6139,
        "lng": 77.2090,
        "population_tier": "medium",
    }


@pytest.fixture
def mock_db_conn():
    """Mock psycopg2 database connection."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cursor
