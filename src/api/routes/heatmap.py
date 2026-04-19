"""
CivicPulse — Heatmap Route
GET /api/v1/heatmap — CSS scores for all wards in a city, colored by threshold.
"""

import logging
from datetime import datetime, date, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from dependencies import get_current_user
from models.user import User
from models.ward import Ward
from models.dispatch import CSSHistory
from schemas.common import APIResponse
from schemas.ward import HeatmapWard

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["heatmap"])


def get_status_label(css_score: float) -> str:
    """Map CSS score to status label using thresholds from env."""
    if css_score >= settings.css_critical_threshold:
        return "critical"
    elif css_score >= settings.css_high_threshold:
        return "high"
    elif css_score > settings.css_stable_max:
        return "elevated"
    else:
        return "stable"


@router.get("/heatmap")
async def get_heatmap(
    city_id: Optional[str] = Query(None, description="Filter by city"),
    date_filter: Optional[date] = Query(None, alias="date", description="Date (YYYY-MM-DD)"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return CSS scores for all wards in a city for heatmap rendering."""
    try:
        # Get all wards, optionally filtered by city
        query = select(Ward)
        if city_id:
            query = query.where(Ward.city_id == city_id)

        result = await db.execute(query)
        wards = result.scalars().all()

        heatmap_data = []
        for ward in wards:
            # Get latest CSS score for this ward
            css_query = (
                select(CSSHistory.css_score, CSSHistory.computed_at)
                .where(CSSHistory.ward_id == ward.id)
                .order_by(desc(CSSHistory.computed_at))
                .limit(1)
            )

            if date_filter:
                css_query = css_query.where(
                    func.date(CSSHistory.computed_at) == date_filter
                )

            css_result = await db.execute(css_query)
            css_row = css_result.first()

            css_score = float(css_row.css_score) if css_row else 0.0

            heatmap_data.append(HeatmapWard(
                ward_id=str(ward.id),
                ward_name=ward.name,
                lat=float(ward.lat) if ward.lat else None,
                lng=float(ward.lng) if ward.lng else None,
                css_score=css_score,
                status_label=get_status_label(css_score),
            ))

        # Sort by CSS score descending (most stressed first)
        heatmap_data.sort(key=lambda w: w.css_score, reverse=True)

        return APIResponse(
            data=[w.model_dump() for w in heatmap_data],
            meta={
                "city_id": city_id or "all",
                "date": str(date_filter or date.today()),
                "ward_count": len(heatmap_data),
            },
        )

    except Exception as e:
        logger.error("Heatmap error: %s", e, exc_info=True)
        return APIResponse(
            status="error",
            data=[],
            meta={"error": "Failed to load heatmap data"},
        )
