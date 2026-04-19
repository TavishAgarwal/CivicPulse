"""
CivicPulse — Wards Routes
GET /api/v1/wards — paginated ward list
GET /api/v1/wards/:id — ward detail
GET /api/v1/wards/:id/stress — CSS + signal breakdown
GET /api/v1/wards/:id/history — CSS time series
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from dependencies import get_current_user
from models.user import User
from models.ward import Ward
from models.signal import Signal
from models.dispatch import CSSHistory, Dispatch
from schemas.common import APIResponse
from routes.heatmap import get_status_label

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/wards", tags=["wards"])


@router.get("")
async def list_wards(
    city_id: Optional[str] = Query(None),
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List wards with latest CSS scores."""
    query = select(Ward).order_by(Ward.name)
    if city_id:
        query = query.where(Ward.city_id == city_id)
    if cursor:
        query = query.where(Ward.id > cursor)
    query = query.limit(limit + 1)

    result = await db.execute(query)
    wards = result.scalars().all()

    has_more = len(wards) > limit
    wards = wards[:limit]

    data = []
    for ward in wards:
        css_result = await db.execute(
            select(CSSHistory.css_score)
            .where(CSSHistory.ward_id == ward.id)
            .order_by(desc(CSSHistory.computed_at))
            .limit(1)
        )
        css_row = css_result.scalar_one_or_none()
        css_score = float(css_row) if css_row else 0.0

        data.append({
            "ward_id": str(ward.id),
            "ward_code": ward.ward_code,
            "ward_name": ward.name,
            "city_id": ward.city_id,
            "lat": float(ward.lat) if ward.lat else None,
            "lng": float(ward.lng) if ward.lng else None,
            "css_score": css_score,
            "status_label": get_status_label(css_score),
        })

    return APIResponse(
        data=data,
        meta={
            "cursor": str(wards[-1].id) if wards and has_more else None,
            "has_more": has_more,
            "limit": limit,
        },
    )


@router.get("/{ward_id}")
async def get_ward(ward_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get ward detail with CSS history."""
    result = await db.execute(select(Ward).where(Ward.id == ward_id))
    ward = result.scalar_one_or_none()

    if not ward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"status": "error", "code": "WARD_NOT_FOUND",
                    "message": f"Ward {ward_id} not found",
                    "timestamp": datetime.now(timezone.utc).isoformat()},
        )

    # Get 30-day CSS history
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    css_result = await db.execute(
        select(CSSHistory.css_score, CSSHistory.computed_at)
        .where(CSSHistory.ward_id == ward.id, CSSHistory.computed_at >= cutoff)
        .order_by(CSSHistory.computed_at)
    )
    history = [{"css_score": float(r.css_score), "computed_at": r.computed_at.isoformat()} for r in css_result]

    latest_css = history[-1]["css_score"] if history else 0.0

    return APIResponse(data={
        "ward_id": str(ward.id),
        "ward_code": ward.ward_code,
        "ward_name": ward.name,
        "city_id": ward.city_id,
        "lat": float(ward.lat) if ward.lat else None,
        "lng": float(ward.lng) if ward.lng else None,
        "population_tier": ward.population_tier,
        "css_score": latest_css,
        "status_label": get_status_label(latest_css),
        "css_history": history,
    })


@router.get("/{ward_id}/stress")
async def get_ward_stress(ward_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get latest CSS with contributing signal breakdown."""
    result = await db.execute(select(Ward).where(Ward.id == ward_id))
    ward = result.scalar_one_or_none()
    if not ward:
        raise HTTPException(status_code=404, detail={
            "status": "error", "code": "WARD_NOT_FOUND",
            "message": f"Ward {ward_id} not found",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    # Latest CSS
    css_result = await db.execute(
        select(CSSHistory.css_score).where(CSSHistory.ward_id == ward.id)
        .order_by(desc(CSSHistory.computed_at)).limit(1)
    )
    latest_css = float(css_result.scalar_one_or_none() or 0.0)

    # Signal breakdown (last 24h averages per type)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    signal_types = ["pharmacy", "school", "utility", "social", "foodbank", "health"]
    breakdown = []

    for st in signal_types:
        avg_result = await db.execute(
            select(func.avg(Signal.intensity_score))
            .where(Signal.ward_id == ward.id, Signal.signal_type == st,
                   Signal.signal_timestamp >= cutoff)
        )
        avg_val = avg_result.scalar_one_or_none()
        breakdown.append({
            "signal_type": st,
            "intensity_score": round(float(avg_val), 3) if avg_val else 0.0,
        })

    return APIResponse(data={
        "ward_id": str(ward.id),
        "ward_name": ward.name,
        "css_score": latest_css,
        "status_label": get_status_label(latest_css),
        "signals_breakdown": breakdown,
    })


@router.get("/{ward_id}/history")
async def get_ward_history(
    ward_id: str,
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get CSS time-series for a ward."""
    result = await db.execute(select(Ward).where(Ward.id == ward_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail={
            "status": "error", "code": "WARD_NOT_FOUND",
            "message": f"Ward {ward_id} not found",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    css_result = await db.execute(
        select(CSSHistory.css_score, CSSHistory.computed_at)
        .where(CSSHistory.ward_id == ward_id, CSSHistory.computed_at >= cutoff)
        .order_by(CSSHistory.computed_at)
    )

    history = [{"css_score": float(r.css_score), "computed_at": r.computed_at.isoformat()} for r in css_result]

    return APIResponse(
        data=history,
        meta={"ward_id": ward_id, "days": days, "data_points": len(history)},
    )
