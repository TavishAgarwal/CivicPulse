"""
CivicPulse — Social Media Sentiment Signal Connector

Monitors geo-tagged social media sentiment for distress signals.
Intensity mapping:
  0.0-0.3: Normal/positive baseline
  0.3-0.6: Elevated negative sentiment
  0.6-1.0: Crisis-level community distress signals
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

SOCIAL_API_URL = os.environ.get("SOCIAL_API_URL", "")
SOCIAL_API_BEARER_TOKEN = os.environ.get("SOCIAL_API_BEARER_TOKEN", "")


class SocialConnector(BaseConnector):
    """Connector for social media sentiment analysis (near real-time)."""

    def __init__(self):
        super().__init__(source_name="social_sentiment", signal_type="social")

    async def fetch(self) -> AsyncGenerator[UnifiedSignal, None]:
        if not SOCIAL_API_URL:
            logger.error("SOCIAL_API_URL not configured")
            return

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{SOCIAL_API_URL}/sentiment/aggregate",
                    headers={"Authorization": f"Bearer {SOCIAL_API_BEARER_TOKEN}"},
                )
                response.raise_for_status()
                data = response.json()

                for record in data.get("sentiment_reports", []):
                    try:
                        anonymized = anonymize_at_source(record)
                        if not self.validate(anonymized):
                            continue
                        yield self.normalize(anonymized)
                    except Exception as e:
                        logger.error("Failed to process social record: %s", e)

        except httpx.HTTPStatusError as e:
            logger.error("Social API HTTP error %d: %s", e.response.status_code, e)
        except httpx.RequestError as e:
            logger.error("Social API request failed: %s", e)
        except Exception as e:
            logger.error("Unexpected error fetching social data: %s", e)

    def validate(self, raw: dict) -> bool:
        return "location_pin" in raw

    def normalize(self, raw: dict) -> UnifiedSignal:
        # Convert negative sentiment ratio to intensity
        neg_ratio = float(raw.get("negative_sentiment_ratio", 0.2))
        intensity = max(0.0, min(1.0, neg_ratio))

        return UnifiedSignal(
            source=self.source_name,
            location_pin=str(raw["location_pin"]),
            signal_type=self.signal_type,
            intensity_score=intensity,
            timestamp=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
            confidence=max(0.0, min(1.0, float(raw.get("confidence", 0.6)))),
        )


register_connector("social", SocialConnector)
