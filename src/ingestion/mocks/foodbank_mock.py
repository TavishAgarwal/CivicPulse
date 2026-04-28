"""CivicPulse — Mock Food Bank Connector. Development-only."""

import asyncio, json, logging, os, random
from datetime import datetime, timezone
from typing import AsyncGenerator
from anonymizer import anonymize_at_source
from base import BaseConnector, UnifiedSignal
from registry import register_mock_connector

logger = logging.getLogger(__name__)
SYNTHETIC_DATA_PATH = os.environ.get("SYNTHETIC_DATA_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "synthetic", "signals_sample.json"))
MOCK_INTERVAL_SECONDS = float(os.environ.get("MOCK_INTERVAL_SECONDS", "5"))

class FoodbankMockConnector(BaseConnector):
    def __init__(self):
        super().__init__(source_name="foodbank_sensors_mock", signal_type="foodbank")

    async def fetch(self) -> AsyncGenerator[UnifiedSignal, None]:
        for s in self._load():
            try:
                a = anonymize_at_source(s)
                a["intensity_score"] = max(0.0, min(1.0, float(a.get("intensity_score", 0.3)) + random.uniform(-0.05, 0.05)))
                a["timestamp"] = datetime.now(timezone.utc).isoformat()
                if self.validate(a):
                    yield self.normalize(a)
                await asyncio.sleep(MOCK_INTERVAL_SECONDS)
            except Exception as e:
                logger.error("Mock foodbank error: %s", e)

    def validate(self, raw: dict) -> bool:
        return "location_pin" in raw

    def normalize(self, raw: dict) -> UnifiedSignal:
        return UnifiedSignal(source=self.source_name, location_pin=str(raw["location_pin"]),
            signal_type=self.signal_type,
            intensity_score=max(0.0, min(1.0, float(raw.get("intensity_score", 0.3)))),
            timestamp=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
            confidence=max(0.0, min(1.0, float(raw.get("confidence", 0.8)))))

    def _load(self) -> list[dict]:
        try:
            p = os.path.abspath(SYNTHETIC_DATA_PATH)
            if os.path.exists(p):
                with open(p) as f:
                    return [s for s in json.load(f) if s.get("signal_type") == "foodbank"]
        except Exception:
            pass
        return [{"location_pin": f"WARD-DEL-{i:03d}", "signal_type": "foodbank",
                 "intensity_score": random.uniform(0.1, 0.8), "confidence": random.uniform(0.7, 0.95)}
                for i in range(1, 11)]

register_mock_connector("foodbank", FoodbankMockConnector)
