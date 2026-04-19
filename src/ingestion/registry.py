"""
CivicPulse — Connector Registry

Manages registration and retrieval of signal connectors.
When CIVICPULSE_ENV=development, automatically substitutes mock connectors.
No if-dev checks inside connectors — this registry handles it all.
"""

import os
import logging
from typing import Type

from .base import BaseConnector

logger = logging.getLogger(__name__)

# Registry mapping signal_type -> connector class
_real_connectors: dict[str, Type[BaseConnector]] = {}
_mock_connectors: dict[str, Type[BaseConnector]] = {}


def register_connector(signal_type: str, connector_cls: Type[BaseConnector]) -> None:
    """Register a real (production) connector for a signal type."""
    _real_connectors[signal_type] = connector_cls
    logger.info("Registered real connector for signal type: %s", signal_type)


def register_mock_connector(signal_type: str, connector_cls: Type[BaseConnector]) -> None:
    """Register a mock (development) connector for a signal type."""
    _mock_connectors[signal_type] = connector_cls
    logger.info("Registered mock connector for signal type: %s", signal_type)


def get_connector(signal_type: str) -> BaseConnector:
    """
    Get the appropriate connector for a signal type.
    Uses mock connectors when CIVICPULSE_ENV=development.

    Args:
        signal_type: The type of signal (pharmacy, school, etc.)

    Returns:
        An instantiated connector

    Raises:
        ValueError: If no connector is registered for the signal type
    """
    env = os.environ.get("CIVICPULSE_ENV", "development")

    if env == "development":
        if signal_type not in _mock_connectors:
            raise ValueError(
                f"No mock connector registered for signal type '{signal_type}'. "
                f"Available mocks: {list(_mock_connectors.keys())}"
            )
        logger.info("Using mock connector for %s (env=%s)", signal_type, env)
        return _mock_connectors[signal_type]()
    else:
        if signal_type not in _real_connectors:
            raise ValueError(
                f"No real connector registered for signal type '{signal_type}'. "
                f"Available connectors: {list(_real_connectors.keys())}"
            )
        logger.info("Using real connector for %s (env=%s)", signal_type, env)
        return _real_connectors[signal_type]()


def get_all_connectors() -> list[BaseConnector]:
    """
    Get connectors for all registered signal types.
    Automatically selects mock vs real based on environment.

    Returns:
        List of instantiated connectors
    """
    env = os.environ.get("CIVICPULSE_ENV", "development")
    registry = _mock_connectors if env == "development" else _real_connectors

    connectors = []
    for signal_type, connector_cls in registry.items():
        try:
            connectors.append(connector_cls())
            logger.info("Initialized connector: %s (%s)", signal_type, env)
        except Exception as e:
            logger.error("Failed to initialize connector for %s: %s", signal_type, e)

    return connectors


def list_registered_types() -> dict[str, list[str]]:
    """List all registered signal types for both real and mock connectors."""
    return {
        "real": list(_real_connectors.keys()),
        "mock": list(_mock_connectors.keys()),
    }
