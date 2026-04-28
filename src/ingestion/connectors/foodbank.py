"""
CivicPulse — Food Bank Signal Connector

Monitors food bank queue lengths and stock levels.
Intensity mapping:
  0.0-0.3: Normal operations
  0.3-0.6: Above-average demand
  0.6-1.0: Critical demand / stock depletion
"""

import logging
import os
from datetime import datetime, timezone
from typing import AsyncGenerator

import httpx

from anonymizer import anonymize_at_source
from base import BaseConnector, UnifiedSignal
from registry import register_connector

logger = logging.getLogger(__name__)

FOODBANK_API_URL = os.environ.get("FOODBANK_API_URL", "")
FOODBANK_API_KEY = os.environ.get("FOODBANK_API_KEY", "")


class FoodbankConnector(BaseConnector):
    """Connector for food bank demand data (real-time)."""

    def __init__(self):
        super().__init__(source_name="foodbank_sensors", signal_type="foodbank")

    async def fetch(self) -> AsyncGenerator[UnifiedSignal, None]:
        if not FOODBANK_API_URL:
            logger.error("FOODBANK_API_URL not configured")
            return

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{FOODBANK_API_URL}/demand/current",
                    headers={"Authorization": f"Bearer {FOODBANK_API_KEY}"},
                )
                response.raise_for_status()
                data = response.json()

                for record in data.get("demand_reports", []):
                    try:
                        anonymized = anonymize_at_source(record)
                        if not self.validate(anonymized):
                            continue
                        yield self.normalize(anonymized)
                    except Exception as e:
                        logger.error("Failed to process foodbank record: %s", e)

        except httpx.HTTPStatusError as e:
            logger.error("Foodbank API HTTP error %d: %s", e.response.status_code, e)
        except httpx.RequestError as e:
            logger.error("Foodbank API request failed: %s", e)
        except Exception as e:
            logger.error("Unexpected error fetching foodbank data: %s", e)

    def validate(self, raw: dict) -> bool:
        return "location_pin" in raw

    def normalize(self, raw: dict) -> UnifiedSignal:
        intensity = max(0.0, min(1.0, float(raw.get("intensity_score", 0.3))))
        return UnifiedSignal(
            source=self.source_name,
            location_pin=str(raw["location_pin"]),
            signal_type=self.signal_type,
            intensity_score=intensity,
            timestamp=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
            confidence=max(0.0, min(1.0, float(raw.get("confidence", 0.8)))),
        )


register_connector("foodbank", FoodbankConnector)
