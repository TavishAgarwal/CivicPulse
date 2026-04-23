"""
CivicPulse — Dispatch Routes
POST /api/v1/dispatch/suggest — match volunteers to a ward
POST /api/v1/dispatch/confirm — confirm a dispatch
POST /api/v1/dispatch/:id/complete — mark dispatch complete
GET /api/v1/dispatches — list dispatches with filters
"""

import logging
import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from dependencies import get_current_user
from models.user import User
from models.ward import Ward
from models.volunteer import Volunteer
from models.dispatch import Dispatch, CSSHistory
from schemas.dispatch import (
    DispatchSuggestRequest, DispatchConfirmRequest, DispatchCompleteRequest,
    VolunteerMatch, DispatchSuggestion,
)
from schemas.common import APIResponse
from routes.heatmap import get_status_label

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["dispatch"])


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """Calculate distance in km between two coordinates."""
    if any(v is None for v in [lat1, lng1, lat2, lng2]):
        return 999.0
    R = 6371
    dlat = math.radians(float(lat2) - float(lat1))
    dlng = math.radians(float(lng2) - float(lng1))
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_match_score(volunteer, ward, required_skills: list[str]) -> dict:
    """Compute match score with breakdown. Weights from env config."""
    # Proximity
    distance = haversine_km(volunteer.lat, volunteer.lng, ward.lat, ward.lng)
    if distance > volunteer.max_radius_km:
        proximity_score = 0.0
    else:
        proximity_score = max(0, 1.0 - (distance / volunteer.max_radius_km))

    # Skill alignment
    vol_skills = set(volunteer.skills or [])
    req_skills = set(required_skills) if required_skills else set()
    if req_skills:
        skill_score = len(vol_skills & req_skills) / len(req_skills)
    else:
        skill_score = 1.0 if vol_skills else 0.5

    # Availability
    availability_score = 1.0 if volunteer.is_available else 0.0

    # Fatigue (inverse)
    fatigue_inv = 1.0 - float(volunteer.fatigue_score or 0)

    total = (
        settings.dispatch_weight_proximity * proximity_score
        + settings.dispatch_weight_skill * skill_score
        + settings.dispatch_weight_availability * availability_score
        + settings.dispatch_weight_fatigue * fatigue_inv
    )

    return {
        "total": round(total, 4),
        "proximity": round(proximity_score, 4),
        "skill": round(skill_score, 4),
        "availability": round(availability_score, 4),
        "fatigue": round(fatigue_inv, 4),
        "distance_km": round(distance, 2),
    }


@router.post("/dispatch/suggest")
async def suggest_dispatch(
    request: DispatchSuggestRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Suggest top volunteers for a ward dispatch."""
    # Get ward
    result = await db.execute(select(Ward).where(Ward.id == request.ward_id))
    ward = result.scalar_one_or_none()
    if not ward:
        raise HTTPException(status_code=404, detail={
            "status": "error", "code": "WARD_NOT_FOUND",
            "message": f"Ward {request.ward_id} not found",
            "timestamp": datetime.now(timezone.utc).isoformat()})

    # Get latest CSS
    css_result = await db.execute(
        select(CSSHistory.css_score).where(CSSHistory.ward_id == ward.id)
        .order_by(desc(CSSHistory.computed_at)).limit(1)
    )
    css_score = float(css_result.scalar_one_or_none() or 0.0)

    # Get available volunteers in the same city
    vol_query = select(Volunteer).where(
        Volunteer.is_available == True,
        Volunteer.fatigue_score < 0.85,
    )
    if ward.city_id:
        vol_query = vol_query.where(Volunteer.city_id == ward.city_id)

    vol_result = await db.execute(vol_query)
    volunteers = vol_result.scalars().all()

    # Score and rank
    matches = []
    for vol in volunteers:
        scores = compute_match_score(vol, ward, [])
        if scores["total"] > 0.1:  # Minimum threshold
            matches.append(VolunteerMatch(
                volunteer_id=str(vol.id),
                display_handle=vol.display_handle,
                skills=vol.skills or [],
                distance_km=scores["distance_km"],
                fatigue_score=float(vol.fatigue_score),
                match_score=scores["total"],
                score_breakdown=scores,
            ))

    matches.sort(key=lambda m: m.match_score, reverse=True)
    top_matches = matches[:settings.dispatch_match_count]

    return APIResponse(data=DispatchSuggestion(
        ward_id=str(ward.id),
        ward_name=ward.name,
        css_score=css_score,
        matches=top_matches,
    ).model_dump())


@router.post("/dispatch/confirm")
async def confirm_dispatch(
    request: DispatchConfirmRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm and create a dispatch record."""
    # Validate volunteer exists
    vol_result = await db.execute(select(Volunteer).where(Volunteer.id == request.volunteer_id))
    volunteer = vol_result.scalar_one_or_none()
    if not volunteer:
        raise HTTPException(status_code=404, detail={
            "status": "error", "code": "VOLUNTEER_NOT_FOUND",
            "message": f"Volunteer {request.volunteer_id} not found",
            "timestamp": datetime.now(timezone.utc).isoformat()})

    # Get CSS for ward from dispatch_id (dispatch_id is actually ward_id in first creation)
    dispatch_result = await db.execute(select(Dispatch).where(Dispatch.id == request.dispatch_id))
    existing_dispatch = dispatch_result.scalar_one_or_none()

    if existing_dispatch:
        # Update existing dispatch
        existing_dispatch.volunteer_id = volunteer.id
        existing_dispatch.status = "confirmed"
        existing_dispatch.confirmed_at = datetime.now(timezone.utc)
        await db.commit()
        dispatch = existing_dispatch
    else:
        # Create new dispatch
        css_result = await db.execute(
            select(CSSHistory.css_score).where(CSSHistory.ward_id == request.dispatch_id)
            .order_by(desc(CSSHistory.computed_at)).limit(1)
        )
        css_score = float(css_result.scalar_one_or_none() or 0.0)

        dispatch = Dispatch(
            ward_id=request.dispatch_id,
            volunteer_id=volunteer.id,
            css_at_dispatch=css_score,
            status="confirmed",
            dispatched_at=datetime.now(timezone.utc),
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(dispatch)
        await db.commit()
        await db.refresh(dispatch)

    # Notify the volunteer via cascading fallback (WhatsApp → SMS → Manual Log)
    try:
        from services.notifier import notify_volunteer_async
        ward_result = await db.execute(select(Ward).where(Ward.id == dispatch.ward_id))
        ward_for_notify = ward_result.scalar_one_or_none()
        ward_name_for_notify = ward_for_notify.ward_label if ward_for_notify else "Unknown Ward"
        await notify_volunteer_async(
            volunteer_id=str(volunteer.id),
            ward_name=ward_name_for_notify,
            css_score=dispatch.css_at_dispatch or 0.0,
        )
    except Exception as notify_err:
        logger.warning("Notification failed (dispatch still confirmed): %s", notify_err)

    return APIResponse(data={
        "dispatch_id": str(dispatch.id),
        "status": dispatch.status,
        "volunteer_id": str(volunteer.id),
        "confirmed_at": dispatch.confirmed_at.isoformat() if dispatch.confirmed_at else None,
    })


@router.post("/dispatch/{dispatch_id}/complete")
async def complete_dispatch(
    dispatch_id: str,
    request: DispatchCompleteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark dispatch as complete and update fatigue score."""
    result = await db.execute(select(Dispatch).where(Dispatch.id == dispatch_id))
    dispatch = result.scalar_one_or_none()
    if not dispatch:
        raise HTTPException(status_code=404, detail={
            "status": "error", "code": "DISPATCH_NOT_FOUND",
            "message": f"Dispatch {dispatch_id} not found",
            "timestamp": datetime.now(timezone.utc).isoformat()})

    dispatch.status = "completed"
    dispatch.completed_at = datetime.now(timezone.utc)
    dispatch.coordinator_rating = request.coordinator_rating
    dispatch.coordinator_notes = request.notes

    # Update volunteer fatigue
    if dispatch.volunteer_id:
        vol_result = await db.execute(select(Volunteer).where(Volunteer.id == dispatch.volunteer_id))
        volunteer = vol_result.scalar_one_or_none()
        if volunteer:
            new_fatigue = min(1.0, float(volunteer.fatigue_score) + settings.fatigue_increment_per_dispatch)
            volunteer.fatigue_score = new_fatigue

            # Update performance rating (rolling average)
            if volunteer.performance_rating is not None:
                volunteer.performance_rating = round(
                    (float(volunteer.performance_rating) + request.coordinator_rating) / 2, 2
                )
            else:
                volunteer.performance_rating = float(request.coordinator_rating)

    await db.commit()

    return APIResponse(data={
        "dispatch_id": str(dispatch.id),
        "status": "completed",
        "completed_at": dispatch.completed_at.isoformat(),
        "rating": request.coordinator_rating,
    })


@router.get("/dispatches")
async def list_dispatches(
    status_filter: Optional[str] = Query(None, alias="status"),
    ward_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List dispatches with filters."""
    query = select(Dispatch).order_by(desc(Dispatch.created_at))

    if status_filter:
        query = query.where(Dispatch.status == status_filter)
    if ward_id:
        query = query.where(Dispatch.ward_id == ward_id)
    if cursor:
        query = query.where(Dispatch.id < cursor)

    query = query.limit(limit + 1)
    result = await db.execute(query)
    dispatches = result.scalars().all()

    has_more = len(dispatches) > limit
    dispatches = dispatches[:limit]

    data = []
    for d in dispatches:
        data.append({
            "id": str(d.id),
            "ward_id": str(d.ward_id) if d.ward_id else None,
            "volunteer_id": str(d.volunteer_id) if d.volunteer_id else None,
            "css_at_dispatch": float(d.css_at_dispatch) if d.css_at_dispatch else None,
            "status": d.status,
            "match_score": float(d.match_score) if d.match_score else None,
            "dispatched_at": d.dispatched_at.isoformat() if d.dispatched_at else None,
            "confirmed_at": d.confirmed_at.isoformat() if d.confirmed_at else None,
            "completed_at": d.completed_at.isoformat() if d.completed_at else None,
            "coordinator_rating": d.coordinator_rating,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })

    return APIResponse(
        data=data,
        meta={"cursor": str(dispatches[-1].id) if dispatches and has_more else None, "has_more": has_more},
    )
