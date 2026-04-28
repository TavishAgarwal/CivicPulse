"""
CivicPulse — Pharmacy Signal Connector

Connects to pharmacy chain APIs to detect medicine stock-out patterns.
Intensity mapping:
  0.0-0.3: Normal stock levels
  0.3-0.6: Above-average demand
  0.6-1.0: Critical stock-outs in essential medicines
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

PHARMACY_API_URL = os.environ.get("PHARMACY_API_URL", "")
PHARMACY_API_KEY = os.environ.get("PHARMACY_API_KEY", "")


class PharmacyConnector(BaseConnector):
    """Connector for pharmacy stock-out data."""

    def __init__(self):
        super().__init__(source_name="pharmacy_api", signal_type="pharmacy")

    async def fetch(self) -> AsyncGenerator[UnifiedSignal, None]:
        """Fetch pharmacy stock-out data from the pharmacy chain API."""
        if not PHARMACY_API_URL:
            logger.error("PHARMACY_API_URL not configured — cannot fetch pharmacy data")
            return

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{PHARMACY_API_URL}/stock-levels",
                    headers={"Authorization": f"Bearer {PHARMACY_API_KEY}"},
                )
                response.raise_for_status()
                data = response.json()

                for record in data.get("stock_reports", []):
                    try:
                        anonymized = anonymize_at_source(record)

                        if not self.validate(anonymized):
                            logger.warning("Invalid pharmacy record skipped")
                            continue

                        yield self.normalize(anonymized)
                    except Exception as e:
                        logger.error("Failed to process pharmacy record: %s", e)
                        continue

        except httpx.HTTPStatusError as e:
            logger.error("Pharmacy API HTTP error %d: %s", e.response.status_code, e)
        except httpx.RequestError as e:
            logger.error("Pharmacy API request failed: %s", e)
        except Exception as e:
            logger.error("Unexpected error fetching pharmacy data: %s", e)

    def validate(self, raw: dict) -> bool:
        """Validate pharmacy record can be parsed."""
        required = ["location_pin", "intensity_score"]
        return all(key in raw for key in required)

    def normalize(self, raw: dict) -> UnifiedSignal:
        """Convert pharmacy data to UnifiedSignal."""
        return UnifiedSignal(
            source=self.source_name,
            location_pin=str(raw["location_pin"]),
            signal_type=self.signal_type,
            intensity_score=max(0.0, min(1.0, float(raw["intensity_score"]))),
            timestamp=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
            confidence=max(0.0, min(1.0, float(raw.get("confidence", 0.7)))),
        )


# Auto-register on import
register_connector("pharmacy", PharmacyConnector)
