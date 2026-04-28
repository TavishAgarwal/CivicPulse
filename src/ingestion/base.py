"""
CivicPulse — BaseConnector Interface

All signal connectors (pharmacy, school, utility, social, foodbank, health)
must implement this interface. The interface enforces a consistent contract
for fetching and validating civic signals.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import AsyncGenerator

from pydantic import BaseModel, Field, field_validator


class UnifiedSignal(BaseModel):
    """
    Pydantic model for the Unified Signal Schema.
    Every signal source must produce data conforming to this model.
    """

    source: str = Field(..., min_length=1, max_length=100)
    location_pin: str = Field(..., min_length=1, max_length=100)
    signal_type: str = Field(...)
    intensity_score: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime
    confidence: float = Field(..., ge=0.0, le=1.0)

    @field_validator("signal_type")
    @classmethod
    def validate_signal_type(cls, v: str) -> str:
        valid_types = {"pharmacy", "school", "utility", "social", "foodbank", "health"}
        if v not in valid_types:
            raise ValueError(f"signal_type must be one of {valid_types}, got '{v}'")
        return v

    model_config = {"json_schema_extra": {"examples": [
        {
            "source": "pharmacy_api",
            "location_pin": "WARD-DEL-015",
            "signal_type": "pharmacy",
            "intensity_score": 0.72,
            "timestamp": "2026-04-18T10:30:00Z",
            "confidence": 0.85,
        }
    ]}}


class BaseConnector(ABC):
    """
    Abstract base class for all signal connectors.
    All signal connectors must implement this interface.
    """

    def __init__(self, source_name: str, signal_type: str):
        """
        Initialize the connector.

        Args:
            source_name: Identifier for this data source (e.g. 'pharmacy_api')
            signal_type: One of the valid signal types
        """
        self.source_name = source_name
        self.signal_type = signal_type

    @abstractmethod
    async def fetch(self) -> AsyncGenerator[UnifiedSignal, None]:
        """
        Yield normalized, pre-anonymized signals from this data source.
        Each yielded signal must conform to the UnifiedSignal schema.

        Yields:
            UnifiedSignal instances
        """
        ...

    @abstractmethod
    def validate(self, raw: dict) -> bool:
        """
        Validate that raw data from this source can be parsed into a UnifiedSignal.

        Args:
            raw: Raw data dictionary from the source

        Returns:
            True if the data is valid and parseable
        """
        ...

    def normalize(self, raw: dict) -> UnifiedSignal:
        """
        Convert raw data into a UnifiedSignal. Subclasses should override
        this if the source format differs from the schema.

        Args:
            raw: Raw data dictionary

        Returns:
            UnifiedSignal instance

        Raises:
            ValueError: If data cannot be normalized
        """
        try:
            return UnifiedSignal(
                source=self.source_name,
                location_pin=raw.get("location_pin", ""),
                signal_type=self.signal_type,
                intensity_score=float(raw.get("intensity_score", 0)),
                timestamp=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
                confidence=float(raw.get("confidence", 0.5)),
            )
        except Exception as e:
            raise ValueError(f"Failed to normalize signal from {self.source_name}: {e}")
