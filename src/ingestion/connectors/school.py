"""
CivicPulse — School Attendance Signal Connector

Connects to school attendance systems to detect aggregate attendance drops.
Intensity mapping:
  0.0-0.3: Normal attendance (>85%)
  0.3-0.6: Moderate drop (70-85%)
  0.6-1.0: Severe drop (<70%) indicating family-level distress
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

SCHOOL_API_URL = os.environ.get("SCHOOL_API_URL", "")
SCHOOL_API_KEY = os.environ.get("SCHOOL_API_KEY", "")


class SchoolConnector(BaseConnector):
    """Connector for school attendance data (daily batch)."""

    def __init__(self):
        super().__init__(source_name="school_attendance", signal_type="school")

    async def fetch(self) -> AsyncGenerator[UnifiedSignal, None]:
        """Fetch aggregate attendance data from school MIS."""
        if not SCHOOL_API_URL:
            logger.error("SCHOOL_API_URL not configured — cannot fetch school data")
            return

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{SCHOOL_API_URL}/attendance/aggregate",
                    headers={"Authorization": f"Bearer {SCHOOL_API_KEY}"},
                )
                response.raise_for_status()
                data = response.json()

                for record in data.get("attendance_reports", []):
                    try:
                        anonymized = anonymize_at_source(record)

                        if not self.validate(anonymized):
                            logger.warning("Invalid school record skipped")
                            continue

                        yield self.normalize(anonymized)
                    except Exception as e:
                        logger.error("Failed to process school record: %s", e)
                        continue

        except httpx.HTTPStatusError as e:
            logger.error("School API HTTP error %d: %s", e.response.status_code, e)
        except httpx.RequestError as e:
            logger.error("School API request failed: %s", e)
        except Exception as e:
            logger.error("Unexpected error fetching school data: %s", e)

    def validate(self, raw: dict) -> bool:
        """Validate school record."""
        required = ["location_pin"]
        return all(key in raw for key in required)

    def normalize(self, raw: dict) -> UnifiedSignal:
        """Convert school attendance data to UnifiedSignal."""
        # Convert attendance rate to distress intensity
        # High attendance = low intensity, low attendance = high intensity
        attendance_rate = float(raw.get("attendance_rate", 0.85))
        intensity = max(0.0, min(1.0, 1.0 - attendance_rate))

        return UnifiedSignal(
            source=self.source_name,
            location_pin=str(raw["location_pin"]),
            signal_type=self.signal_type,
            intensity_score=intensity,
            timestamp=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
            confidence=max(0.0, min(1.0, float(raw.get("confidence", 0.8)))),
        )


register_connector("school", SchoolConnector)
