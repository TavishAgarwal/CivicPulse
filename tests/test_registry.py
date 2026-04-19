"""
CivicPulse — Connector Registry Tests
Tests registration, retrieval, and environment-based selection.
"""

import sys
import os
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ingestion"))

from registry import (
    register_connector,
    register_mock_connector,
    get_connector,
    get_all_connectors,
    list_registered_types,
    _real_connectors,
    _mock_connectors,
)
from base import BaseConnector


class DummyConnector(BaseConnector):
    source_name = "dummy_source"

    async def fetch(self):
        yield None


class DummyMockConnector(BaseConnector):
    source_name = "dummy_mock_source"

    async def fetch(self):
        yield None


class TestConnectorRegistry:

    def setup_method(self):
        """Clear registries before each test."""
        _real_connectors.clear()
        _mock_connectors.clear()

    def test_register_real_connector(self):
        register_connector("dummy", DummyConnector)
        assert "dummy" in _real_connectors
        assert _real_connectors["dummy"] == DummyConnector

    def test_register_mock_connector(self):
        register_mock_connector("dummy", DummyMockConnector)
        assert "dummy" in _mock_connectors

    @patch.dict(os.environ, {"CIVICPULSE_ENV": "production"})
    def test_get_real_connector_in_production(self):
        register_connector("dummy", DummyConnector)
        connector = get_connector("dummy")
        assert isinstance(connector, DummyConnector)

    @patch.dict(os.environ, {"CIVICPULSE_ENV": "development"})
    def test_get_mock_connector_in_development(self):
        register_mock_connector("dummy", DummyMockConnector)
        connector = get_connector("dummy")
        assert isinstance(connector, DummyMockConnector)

    def test_unregistered_raises_error(self):
        with pytest.raises(ValueError, match="No mock connector"):
            get_connector("nonexistent")

    @patch.dict(os.environ, {"CIVICPULSE_ENV": "production"})
    def test_unregistered_real_raises_error(self):
        with pytest.raises(ValueError, match="No real connector"):
            get_connector("nonexistent")

    def test_list_registered_types(self):
        register_connector("real_type", DummyConnector)
        register_mock_connector("mock_type", DummyMockConnector)
        types = list_registered_types()
        assert "real_type" in types["real"]
        assert "mock_type" in types["mock"]

    @patch.dict(os.environ, {"CIVICPULSE_ENV": "development"})
    def test_get_all_connectors_dev(self):
        register_mock_connector("d1", DummyMockConnector)
        register_mock_connector("d2", DummyMockConnector)
        connectors = get_all_connectors()
        assert len(connectors) == 2
