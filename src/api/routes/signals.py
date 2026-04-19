"""
CivicPulse — Signal Ingest Route
POST /api/v1/signals/ingest — ingest a new signal with anonymization.
"""

import logging
import sys
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.signal import Signal
from models.ward import Ward
from schemas.signal import SignalIngestRequest
from schemas.common import APIResponse

# Add ingestion module to path for anonymizer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ingestion"))

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/signals", tags=["signals"])

# PII fields to strip (inline version of anonymize_at_source for API context)
PII_FIELDS = frozenset([
    "name", "full_name", "first_name", "last_name", "phone", "mobile",
    "email", "address", "street", "house_number", "person_id", "aadhaar",
    "voter_id", "dob", "date_of_birth",
])


@router.post("/ingest", status_code=201)
async def ingest_signal(
    request: SignalIngestRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a new signal. Auth required.
    Runs anonymization before writing to database.
    """
    try:
        # Resolve ward from location_pin
        result = await db.execute(
            select(Ward).where(Ward.ward_code == request.location_pin)
        )
        ward = result.scalar_one_or_none()

        if not ward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "code": "WARD_NOT_FOUND",
                    "message": f"No ward found for location_pin '{request.location_pin}'",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        # Defense-in-depth: strip any PII fields from request metadata
        request_data = request.model_dump()
        for pii_field in PII_FIELDS:
            request_data.pop(pii_field, None)

        # Create signal record (data already validated by Pydantic — no PII in schema)
        signal = Signal(
            ward_id=ward.id,
            source=request_data.get("source", request.source),
            signal_type=request_data.get("signal_type", request.signal_type),
            intensity_score=request_data.get("intensity_score", request.intensity_score),
            confidence=request_data.get("confidence", request.confidence),
            signal_timestamp=request_data.get("timestamp", request.timestamp),
        )

        db.add(signal)
        await db.commit()
        await db.refresh(signal)

        logger.info(
            "Signal ingested: id=%s type=%s ward=%s by user=%s",
            signal.id, signal.signal_type, ward.ward_code, user.id,
        )

        return APIResponse(
            data={
                "signal_id": str(signal.id),
                "received_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Signal ingest error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "code": "INGEST_FAILED",
                "message": "Failed to ingest signal.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
