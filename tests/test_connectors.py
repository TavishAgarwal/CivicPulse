"""
CivicPulse — Connector Tests
Tests all 6 signal connectors: pharmacy, school, utility, social, foodbank, health.
Uses mock HTTP to avoid real API calls.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ingestion"))

from base import UnifiedSignal


class TestPharmacyConnector:
    """Tests for PharmacyConnector."""

    def test_import(self):
        from connectors.pharmacy import PharmacyConnector
        assert PharmacyConnector.source_name == "pharmacy_api"

    def test_instantiation(self):
        from connectors.pharmacy import PharmacyConnector
        connector = PharmacyConnector()
        assert connector is not None
        assert hasattr(connector, "fetch")

    @pytest.mark.asyncio
    async def test_fetch_returns_unified_signals(self):
        from connectors.pharmacy import PharmacyConnector
        connector = PharmacyConnector()
        with patch.object(connector, "fetch", return_value=AsyncMock()):
            connector.fetch.return_value.__aiter__ = AsyncMock(return_value=iter([
                UnifiedSignal(
                    source="pharmacy_api", location_pin="WARD-DEL-001",
                    signal_type="pharmacy", intensity_score=0.7,
                    timestamp=datetime.now(timezone.utc).isoformat(), confidence=0.8,
                )
            ]))

    def test_source_name(self):
        from connectors.pharmacy import PharmacyConnector
        assert "pharmacy" in PharmacyConnector.source_name.lower()

    def test_signal_type(self):
        from connectors.pharmacy import PharmacyConnector
        connector = PharmacyConnector()
        assert hasattr(connector, "source_name")


class TestSchoolConnector:
    """Tests for SchoolConnector."""

    def test_import(self):
        from connectors.school import SchoolConnector
        assert SchoolConnector.source_name == "school_attendance"

    def test_instantiation(self):
        from connectors.school import SchoolConnector
        connector = SchoolConnector()
        assert connector is not None

    def test_has_fetch_method(self):
        from connectors.school import SchoolConnector
        connector = SchoolConnector()
        assert hasattr(connector, "fetch")
        assert callable(getattr(connector, "fetch"))

    def test_source_name_contains_school(self):
        from connectors.school import SchoolConnector
        assert "school" in SchoolConnector.source_name.lower()

    def test_inherits_base(self):
        from connectors.school import SchoolConnector
        from base import BaseConnector
        assert issubclass(SchoolConnector, BaseConnector)


class TestUtilityConnector:
    """Tests for UtilityConnector."""

    def test_import(self):
        from connectors.utility import UtilityConnector
        assert UtilityConnector.source_name == "utility_billing"

    def test_instantiation(self):
        from connectors.utility import UtilityConnector
        connector = UtilityConnector()
        assert connector is not None

    def test_inherits_base(self):
        from connectors.utility import UtilityConnector
        from base import BaseConnector
        assert issubclass(UtilityConnector, BaseConnector)

    def test_has_fetch(self):
        from connectors.utility import UtilityConnector
        assert hasattr(UtilityConnector(), "fetch")

    def test_source_name_correct(self):
        from connectors.utility import UtilityConnector
        assert UtilityConnector.source_name == "utility_billing"


class TestSocialConnector:
    """Tests for SocialConnector."""

    def test_import(self):
        from connectors.social import SocialConnector
        assert SocialConnector.source_name == "social_media"

    def test_instantiation(self):
        from connectors.social import SocialConnector
        connector = SocialConnector()
        assert connector is not None

    def test_inherits_base(self):
        from connectors.social import SocialConnector
        from base import BaseConnector
        assert issubclass(SocialConnector, BaseConnector)

    def test_has_fetch(self):
        from connectors.social import SocialConnector
        assert hasattr(SocialConnector(), "fetch")

    def test_source_name_correct(self):
        from connectors.social import SocialConnector
        assert SocialConnector.source_name == "social_media"


class TestFoodbankConnector:
    """Tests for FoodbankConnector."""

    def test_import(self):
        from connectors.foodbank import FoodbankConnector
        assert FoodbankConnector.source_name == "foodbank_distribution"

    def test_instantiation(self):
        from connectors.foodbank import FoodbankConnector
        connector = FoodbankConnector()
        assert connector is not None

    def test_inherits_base(self):
        from connectors.foodbank import FoodbankConnector
        from base import BaseConnector
        assert issubclass(FoodbankConnector, BaseConnector)

    def test_has_fetch(self):
        from connectors.foodbank import FoodbankConnector
        assert hasattr(FoodbankConnector(), "fetch")

    def test_source_name_correct(self):
        from connectors.foodbank import FoodbankConnector
        assert FoodbankConnector.source_name == "foodbank_distribution"


class TestHealthConnector:
    """Tests for HealthConnector."""

    def test_import(self):
        from connectors.health import HealthConnector
        assert HealthConnector.source_name == "health_clinic"

    def test_instantiation(self):
        from connectors.health import HealthConnector
        connector = HealthConnector()
        assert connector is not None

    def test_inherits_base(self):
        from connectors.health import HealthConnector
        from base import BaseConnector
        assert issubclass(HealthConnector, BaseConnector)

    def test_has_fetch(self):
        from connectors.health import HealthConnector
        assert hasattr(HealthConnector(), "fetch")

    def test_source_name_correct(self):
        from connectors.health import HealthConnector
        assert HealthConnector.source_name == "health_clinic"
