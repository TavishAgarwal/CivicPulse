"""CivicPulse — Mock Health Worker Connector. Development-only."""

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

class HealthMockConnector(BaseConnector):
    def __init__(self):
        super().__init__(source_name="health_worker_logs_mock", signal_type="health")

    async def fetch(self) -> AsyncGenerator[UnifiedSignal, None]:
        for s in self._load():
            try:
                a = anonymize_at_source(s)
                a["intensity_score"] = max(0.0, min(1.0, float(a.get("intensity_score", 0.2)) + random.uniform(-0.05, 0.05)))
                a["timestamp"] = datetime.now(timezone.utc).isoformat()
                if self.validate(a):
                    yield self.normalize(a)
                await asyncio.sleep(MOCK_INTERVAL_SECONDS)
            except Exception as e:
                logger.error("Mock health error: %s", e)

    def validate(self, raw: dict) -> bool:
        return "location_pin" in raw

    def normalize(self, raw: dict) -> UnifiedSignal:
        return UnifiedSignal(source=self.source_name, location_pin=str(raw["location_pin"]),
            signal_type=self.signal_type,
            intensity_score=max(0.0, min(1.0, float(raw.get("intensity_score", 0.2)))),
            timestamp=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
            confidence=max(0.0, min(1.0, float(raw.get("confidence", 0.75)))))

    def _load(self) -> list[dict]:
        try:
            p = os.path.abspath(SYNTHETIC_DATA_PATH)
            if os.path.exists(p):
                with open(p) as f:
                    return [s for s in json.load(f) if s.get("signal_type") == "health"]
        except Exception:
            pass
        return [{"location_pin": f"WARD-DEL-{i:03d}", "signal_type": "health",
                 "intensity_score": random.uniform(0.05, 0.6), "confidence": random.uniform(0.65, 0.9)}
                for i in range(1, 11)]

register_mock_connector("health", HealthMockConnector)
