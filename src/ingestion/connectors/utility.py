"""
CivicPulse — Utility Payment Signal Connector

Connects to utility payment portals to detect payment delay patterns.
Intensity mapping:
  0.0-0.3: Normal payment patterns
  0.3-0.6: Elevated default rates
  0.6-1.0: Widespread payment failures indicating economic distress
"""

import logging
import os
from datetime import datetime, timezone
from typing import AsyncGenerator

import httpx

from ..anonymizer import anonymize_at_source
from ..base import BaseConnector, UnifiedSignal
from ..registry import register_connector

logger = logging.getLogger(__name__)

UTILITY_API_URL = os.environ.get("UTILITY_API_URL", "")
UTILITY_API_KEY = os.environ.get("UTILITY_API_KEY", "")


class UtilityConnector(BaseConnector):
    """Connector for utility payment delay data (daily batch)."""

    def __init__(self):
        super().__init__(source_name="utility_payments", signal_type="utility")

    async def fetch(self) -> AsyncGenerator[UnifiedSignal, None]:
        if not UTILITY_API_URL:
            logger.error("UTILITY_API_URL not configured")
            return

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{UTILITY_API_URL}/payment/aggregate",
                    headers={"Authorization": f"Bearer {UTILITY_API_KEY}"},
                )
                response.raise_for_status()
                data = response.json()

                for record in data.get("payment_reports", []):
                    try:
                        anonymized = anonymize_at_source(record)
                        if not self.validate(anonymized):
                            continue
                        yield self.normalize(anonymized)
                    except Exception as e:
                        logger.error("Failed to process utility record: %s", e)

        except httpx.HTTPStatusError as e:
            logger.error("Utility API HTTP error %d: %s", e.response.status_code, e)
        except httpx.RequestError as e:
            logger.error("Utility API request failed: %s", e)
        except Exception as e:
            logger.error("Unexpected error fetching utility data: %s", e)

    def validate(self, raw: dict) -> bool:
        return "location_pin" in raw

    def normalize(self, raw: dict) -> UnifiedSignal:
        default_rate = float(raw.get("default_rate", 0.1))
        intensity = max(0.0, min(1.0, default_rate))

        return UnifiedSignal(
            source=self.source_name,
            location_pin=str(raw["location_pin"]),
            signal_type=self.signal_type,
            intensity_score=intensity,
            timestamp=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
            confidence=max(0.0, min(1.0, float(raw.get("confidence", 0.75)))),
        )


register_connector("utility", UtilityConnector)
