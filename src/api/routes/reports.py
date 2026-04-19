"""
CivicPulse — Reports Route
GET /api/v1/reports/impact — aggregated impact metrics.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.dispatch import Dispatch, CSSHistory
from models.volunteer import Volunteer
from models.ward import Ward
from schemas.common import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

PERIOD_MAP = {"today": 1, "7d": 7, "30d": 30, "90d": 90}


@router.get("/impact")
async def get_impact_report(
    city_id: Optional[str] = Query(None),
    period: str = Query("30d", description="today|7d|30d|90d"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated impact metrics for reports dashboard."""
    days = PERIOD_MAP.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        # Dispatches total
        dispatch_query = select(func.count(Dispatch.id)).where(Dispatch.created_at >= cutoff)
        total_result = await db.execute(dispatch_query)
        dispatches_total = total_result.scalar_one_or_none() or 0

        # Dispatches completed
        completed_query = select(func.count(Dispatch.id)).where(
            Dispatch.created_at >= cutoff, Dispatch.status == "completed"
        )
        completed_result = await db.execute(completed_query)
        dispatches_completed = completed_result.scalar_one_or_none() or 0

        # Avg response time (dispatched_at to confirmed_at)
        avg_response = None
        try:
            resp_query = select(
                func.avg(func.extract("epoch", Dispatch.confirmed_at - Dispatch.dispatched_at) / 60)
            ).where(
                Dispatch.created_at >= cutoff,
                Dispatch.confirmed_at.isnot(None),
                Dispatch.dispatched_at.isnot(None),
            )
            resp_result = await db.execute(resp_query)
            avg_response = resp_result.scalar_one_or_none()
        except Exception:
            pass

        # Avg coordinator rating
        rating_query = select(func.avg(Dispatch.coordinator_rating)).where(
            Dispatch.created_at >= cutoff, Dispatch.coordinator_rating.isnot(None)
        )
        rating_result = await db.execute(rating_query)
        avg_rating = rating_result.scalar_one_or_none()

        # Wards covered (unique wards with dispatches)
        wards_query = select(func.count(func.distinct(Dispatch.ward_id))).where(Dispatch.created_at >= cutoff)
        wards_result = await db.execute(wards_query)
        wards_covered = wards_result.scalar_one_or_none() or 0

        # Active volunteers
        active_query = select(func.count(Volunteer.id)).where(Volunteer.is_available == True)
        active_result = await db.execute(active_query)
        volunteers_active = active_result.scalar_one_or_none() or 0

        # CSS average
        css_query = select(func.avg(CSSHistory.css_score)).where(CSSHistory.computed_at >= cutoff)
        css_result = await db.execute(css_query)
        css_avg = css_result.scalar_one_or_none()

        return APIResponse(data={
            "dispatches_total": dispatches_total,
            "dispatches_completed": dispatches_completed,
            "avg_response_time_minutes": round(float(avg_response), 1) if avg_response else None,
            "avg_coordinator_rating": round(float(avg_rating), 1) if avg_rating else None,
            "wards_covered": wards_covered,
            "volunteers_active": volunteers_active,
            "css_avg_before": round(float(css_avg), 1) if css_avg else None,
            "css_avg_after": None,  # Requires post-dispatch CSS tracking
            "period": period,
            "period_days": days,
        })

    except Exception as e:
        logger.error("Impact report error: %s", e, exc_info=True)
        return APIResponse(
            status="error",
            data={"error": "Failed to generate report"},
        )
