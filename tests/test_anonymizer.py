"""
CivicPulse — Anonymizer Unit Tests

Tests the non-negotiable privacy enforcement layer.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ingestion"))

from anonymizer import anonymize_at_source, validate_no_pii


class TestAnonymizer:
    """Test anonymize_at_source — the critical privacy enforcement point."""

    def test_strips_pii_fields(self):
        """All known PII fields must be removed."""
        raw = {
            "name": "John Doe",
            "phone": "+91-9876543210",
            "email": "john@example.com",
            "address": "123 Main St",
            "aadhaar": "1234-5678-9012",
            "location_pin": "WARD-DEL-001",
            "signal_type": "pharmacy",
            "intensity_score": 0.7,
        }
        result = anonymize_at_source(raw)

        assert "name" not in result
        assert "phone" not in result
        assert "email" not in result
        assert "address" not in result
        assert "aadhaar" not in result
        assert result["location_pin"] == "WARD-DEL-001"
        assert result["intensity_score"] == 0.7

    def test_rounds_coordinates(self):
        """Coordinates must be rounded to 3 decimal places for k-anonymity."""
        raw = {
            "lat": 28.6139456789,
            "lng": 77.2090123456,
            "location_pin": "WARD-DEL-001",
        }
        result = anonymize_at_source(raw)
        assert result["lat"] == 28.614
        assert result["lng"] == 77.209

    def test_preserves_non_pii_fields(self):
        """Non-PII fields must be preserved."""
        raw = {
            "source": "pharmacy_api",
            "location_pin": "WARD-DEL-001",
            "signal_type": "pharmacy",
            "intensity_score": 0.65,
            "confidence": 0.8,
            "timestamp": "2025-01-15T12:00:00Z",
        }
        result = anonymize_at_source(raw)

        assert result["source"] == "pharmacy_api"
        assert result["location_pin"] == "WARD-DEL-001"
        assert result["signal_type"] == "pharmacy"
        assert result["intensity_score"] == 0.65

    def test_empty_input(self):
        """Empty input should return empty dict."""
        result = anonymize_at_source({})
        assert result == {}

    def test_strips_nested_pii_fields(self):
        """PII field names are detected regardless of casing."""
        raw = {
            "first_name": "Jane",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "voter_id": "ABC123",
            "location_pin": "WARD-MUM-007",
        }
        result = anonymize_at_source(raw)
        assert "first_name" not in result
        assert "last_name" not in result
        assert "dob" not in result
        assert "voter_id" not in result
        assert result["location_pin"] == "WARD-MUM-007"


class TestValidateNoPII:
    """Test the PII validation function."""

    def test_clean_data_passes(self):
        raw = {
            "source": "pharmacy_api",
            "location_pin": "WARD-DEL-001",
            "signal_type": "pharmacy",
            "intensity_score": 0.65,
        }
        assert validate_no_pii(raw) is True

    def test_dirty_data_fails(self):
        raw = {
            "source": "pharmacy_api",
            "name": "John Doe",
            "location_pin": "WARD-DEL-001",
        }
        assert validate_no_pii(raw) is False

    def test_phone_number_fails(self):
        raw = {"phone": "9876543210", "location_pin": "WARD-DEL-001"}
        assert validate_no_pii(raw) is False
