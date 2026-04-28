"""
CivicPulse — Mock School Connector
Development-only mock. Never makes real network calls.
"""

import asyncio
import json
import logging
import os
import random
from datetime import datetime, timezone
from typing import AsyncGenerator

from anonymizer import anonymize_at_source
from base import BaseConnector, UnifiedSignal
from registry import register_mock_connector

logger = logging.getLogger(__name__)

SYNTHETIC_DATA_PATH = os.environ.get(
    "SYNTHETIC_DATA_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "synthetic", "signals_sample.json"),
)
MOCK_INTERVAL_SECONDS = float(os.environ.get("MOCK_INTERVAL_SECONDS", "5"))


class SchoolMockConnector(BaseConnector):
    def __init__(self):
        super().__init__(source_name="school_attendance_mock", signal_type="school")

    async def fetch(self) -> AsyncGenerator[UnifiedSignal, None]:
        signals = self._load_synthetic_signals()
        for signal_data in signals:
            try:
                anonymized = anonymize_at_source(signal_data)
                jitter = random.uniform(-0.05, 0.05)
                anonymized["intensity_score"] = max(
                    0.0, min(1.0, float(anonymized.get("intensity_score", 0.3)) + jitter)
                )
                anonymized["timestamp"] = datetime.now(timezone.utc).isoformat()
                if self.validate(anonymized):
                    yield self.normalize(anonymized)
                await asyncio.sleep(MOCK_INTERVAL_SECONDS)
            except Exception as e:
                logger.error("Mock school error: %s", e)

    def validate(self, raw: dict) -> bool:
        return "location_pin" in raw

    def normalize(self, raw: dict) -> UnifiedSignal:
        return UnifiedSignal(
            source=self.source_name,
            location_pin=str(raw["location_pin"]),
            signal_type=self.signal_type,
            intensity_score=max(0.0, min(1.0, float(raw.get("intensity_score", 0.3)))),
            timestamp=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
            confidence=max(0.0, min(1.0, float(raw.get("confidence", 0.8)))),
        )

    def _load_synthetic_signals(self) -> list[dict]:
        try:
            abs_path = os.path.abspath(SYNTHETIC_DATA_PATH)
            if os.path.exists(abs_path):
                with open(abs_path, "r") as f:
                    return [s for s in json.load(f) if s.get("signal_type") == "school"]
        except Exception as e:
            logger.warning("Synthetic data not available: %s", e)
        return [
            {"location_pin": f"WARD-DEL-{i:03d}", "signal_type": "school",
             "intensity_score": random.uniform(0.05, 0.7), "confidence": random.uniform(0.7, 0.95)}
            for i in range(1, 11)
        ]


register_mock_connector("school", SchoolMockConnector)
