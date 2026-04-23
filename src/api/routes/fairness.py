"""
CivicPulse — Fairness Report Route
GET /api/v1/reports/fairness — per-ward false positive rate disparity analysis.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.dispatch import Dispatch, CSSHistory
from models.ward import Ward
from schemas.common import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

# Must match evaluation.py max_disparity
FAIRNESS_THRESHOLD_PCT = 15


@router.get("/fairness")
async def get_fairness_report(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Per-ward false positive rate disparity analysis.
    Returns data compatible with FairnessAudit.jsx visualization.
    """
    try:
        # Fetch all wards
        ward_result = await db.execute(select(Ward))
        wards = ward_result.scalars().all()

        if not wards:
            return APIResponse(data=_generate_demo_fairness("no_wards"))

        # For each ward, compute FP rate from recent dispatches
        # FP = dispatches where coordinator_rating <= 2 (false alarm)
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        ward_fp_data = []

        for ward in wards:
            # Total dispatches for this ward
            total_q = select(func.count(Dispatch.id)).where(
                Dispatch.ward_id == ward.id,
                Dispatch.created_at >= cutoff,
            )
            total_result = await db.execute(total_q)
            total = total_result.scalar_one_or_none() or 0

            if total == 0:
                ward_fp_data.append({
                    "ward": ward.ward_label or ward.ward_code,
                    "fp_rate": 0,
                })
                continue

            # False positives: dispatches with low coordinator rating
            fp_q = select(func.count(Dispatch.id)).where(
                Dispatch.ward_id == ward.id,
                Dispatch.created_at >= cutoff,
                Dispatch.coordinator_rating.isnot(None),
                Dispatch.coordinator_rating <= 2,
            )
            fp_result = await db.execute(fp_q)
            fp_count = fp_result.scalar_one_or_none() or 0

            fp_rate = round((fp_count / total) * 100, 1)
            ward_fp_data.append({
                "ward": ward.ward_label or ward.ward_code,
                "fp_rate": fp_rate,
            })

        # Check if we have meaningful data
        has_data = any(w["fp_rate"] > 0 for w in ward_fp_data)
        if not has_data:
            return APIResponse(data=_generate_demo_fairness("insufficient_data"))

        # Compute summary
        avg_rate = round(
            sum(w["fp_rate"] for w in ward_fp_data) / len(ward_fp_data), 1
        )
        violations = [w for w in ward_fp_data if w["fp_rate"] > FAIRNESS_THRESHOLD_PCT]

        return APIResponse(data={
            "source": "live",
            "ward_fp_data": ward_fp_data,
            "passed": len(violations) == 0,
            "violations": len(violations),
            "threshold": FAIRNESS_THRESHOLD_PCT,
            "avg_rate": avg_rate,
            "wards_checked": len(ward_fp_data),
        })

    except Exception as e:
        logger.error("Fairness report error: %s", e, exc_info=True)
        return APIResponse(data=_generate_demo_fairness("error"))


def _generate_demo_fairness(reason: str) -> dict:
    """Fallback demo data matching FairnessAudit.jsx format."""
    return {
        "source": "demo",
        "reason": reason,
        "ward_fp_data": [
            {"ward": "Ward 1", "fp_rate": 8},
            {"ward": "Ward 2", "fp_rate": 11},
            {"ward": "Ward 3", "fp_rate": 6},
            {"ward": "Ward 4", "fp_rate": 14},
            {"ward": "Ward 5", "fp_rate": 9},
            {"ward": "Ward 6", "fp_rate": 18},
            {"ward": "Ward 7", "fp_rate": 7},
            {"ward": "Ward 8", "fp_rate": 12},
            {"ward": "Ward 9", "fp_rate": 5},
            {"ward": "Ward 10", "fp_rate": 16},
            {"ward": "Ward 11", "fp_rate": 10},
            {"ward": "Ward 12", "fp_rate": 8},
            {"ward": "Ward 13", "fp_rate": 13},
            {"ward": "Ward 14", "fp_rate": 7},
            {"ward": "Ward 15", "fp_rate": 11},
        ],
        "passed": False,
        "violations": 2,
        "threshold": FAIRNESS_THRESHOLD_PCT,
        "avg_rate": 10.3,
        "wards_checked": 15,
    }
