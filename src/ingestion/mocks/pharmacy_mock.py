"""
CivicPulse — Mock Pharmacy Connector

Development-only mock that reads from synthetic data.
Never makes any real network call.
"""

import asyncio
import json
import logging
import os
import random
from datetime import datetime, timezone
from typing import AsyncGenerator

from ..anonymizer import anonymize_at_source
from ..base import BaseConnector, UnifiedSignal
from ..registry import register_mock_connector

logger = logging.getLogger(__name__)

SYNTHETIC_DATA_PATH = os.environ.get(
    "SYNTHETIC_DATA_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "synthetic", "signals_sample.json"),
)
MOCK_INTERVAL_SECONDS = float(os.environ.get("MOCK_INTERVAL_SECONDS", "5"))


class PharmacyMockConnector(BaseConnector):
    """Mock pharmacy connector for development. Reads from synthetic data."""

    def __init__(self):
        super().__init__(source_name="pharmacy_api_mock", signal_type="pharmacy")

    async def fetch(self) -> AsyncGenerator[UnifiedSignal, None]:
        """Yield pharmacy signals from synthetic data with realistic jitter."""
        signals = self._load_synthetic_signals()

        for signal_data in signals:
            try:
                anonymized = anonymize_at_source(signal_data)
                # Add realistic jitter to intensity
                jitter = random.uniform(-0.05, 0.05)
                anonymized["intensity_score"] = max(
                    0.0, min(1.0, float(anonymized.get("intensity_score", 0.5)) + jitter)
                )
                anonymized["timestamp"] = datetime.now(timezone.utc).isoformat()

                if self.validate(anonymized):
                    yield self.normalize(anonymized)

                await asyncio.sleep(MOCK_INTERVAL_SECONDS)
            except Exception as e:
                logger.error("Mock pharmacy error: %s", e)
                continue

    def validate(self, raw: dict) -> bool:
        return "location_pin" in raw and "intensity_score" in raw

    def normalize(self, raw: dict) -> UnifiedSignal:
        return UnifiedSignal(
            source=self.source_name,
            location_pin=str(raw["location_pin"]),
            signal_type=self.signal_type,
            intensity_score=max(0.0, min(1.0, float(raw["intensity_score"]))),
            timestamp=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
            confidence=max(0.0, min(1.0, float(raw.get("confidence", 0.7)))),
        )

    def _load_synthetic_signals(self) -> list[dict]:
        """Load pharmacy signals from synthetic data file."""
        try:
            abs_path = os.path.abspath(SYNTHETIC_DATA_PATH)
            if os.path.exists(abs_path):
                with open(abs_path, "r") as f:
                    all_signals = json.load(f)
                return [s for s in all_signals if s.get("signal_type") == "pharmacy"]
        except Exception as e:
            logger.warning("Could not load synthetic data: %s. Using generated data.", e)

        # Fallback: generate in-memory mock data
        return [
            {
                "location_pin": f"WARD-DEL-{i:03d}",
                "signal_type": "pharmacy",
                "intensity_score": random.uniform(0.1, 0.9),
                "confidence": random.uniform(0.6, 0.95),
            }
            for i in range(1, 11)
        ]


register_mock_connector("pharmacy", PharmacyMockConnector)
