"""
CivicPulse — Base Connector & UnifiedSignal Tests
Tests the base connector interface and signal schema validation.
"""

import sys
import os
import pytest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ingestion"))

from base import BaseConnector, UnifiedSignal


class TestUnifiedSignal:
    """Tests for the UnifiedSignal Pydantic model."""

    def test_valid_signal(self, sample_signal):
        """Valid signal data should create a UnifiedSignal."""
        signal = UnifiedSignal(**sample_signal)
        assert signal.source == "pharmacy_api"
        assert signal.signal_type == "pharmacy"
        assert 0.0 <= signal.intensity_score <= 1.0

    def test_signal_intensity_bounds(self):
        """Intensity score must be between 0.0 and 1.0."""
        with pytest.raises(Exception):
            UnifiedSignal(
                source="test", location_pin="WARD-001",
                signal_type="pharmacy", intensity_score=1.5,
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.5,
            )

    def test_signal_confidence_bounds(self):
        """Confidence must be between 0.0 and 1.0."""
        with pytest.raises(Exception):
            UnifiedSignal(
                source="test", location_pin="WARD-001",
                signal_type="pharmacy", intensity_score=0.5,
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=-0.1,
            )

    def test_signal_required_fields(self):
        """Missing required fields should raise validation error."""
        with pytest.raises(Exception):
            UnifiedSignal(source="test")

    def test_signal_model_dump(self, sample_signal):
        """model_dump should return a dict with all fields."""
        signal = UnifiedSignal(**sample_signal)
        dumped = signal.model_dump()
        assert "source" in dumped
        assert "location_pin" in dumped
        assert "signal_type" in dumped
        assert "intensity_score" in dumped

    def test_signal_zero_intensity(self):
        """Zero intensity should be valid."""
        signal = UnifiedSignal(
            source="test", location_pin="WARD-001",
            signal_type="pharmacy", intensity_score=0.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=0.5,
        )
        assert signal.intensity_score == 0.0


class TestBaseConnector:
    """Tests for the BaseConnector abstract class."""

    def test_cannot_instantiate(self):
        """BaseConnector is abstract and should not be directly instantiated."""
        with pytest.raises(TypeError):
            BaseConnector()

    def test_subclass_requires_fetch(self):
        """Subclasses must implement fetch()."""
        class BadConnector(BaseConnector):
            source_name = "test"
        with pytest.raises(TypeError):
            BadConnector()
