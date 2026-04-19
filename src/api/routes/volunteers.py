"""
CivicPulse — Volunteer Routes
CRUD operations for volunteer profiles.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.volunteer import Volunteer
from models.dispatch import Dispatch
from schemas.volunteer import VolunteerCreate, VolunteerUpdate, VolunteerResponse
from schemas.common import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/volunteers", tags=["volunteers"])


@router.get("")
async def list_volunteers(
    skill: Optional[str] = Query(None),
    city_id: Optional[str] = Query(None),
    available: Optional[bool] = Query(None),
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List volunteers with filters."""
    query = select(Volunteer).order_by(Volunteer.display_handle)

    if city_id:
        query = query.where(Volunteer.city_id == city_id)
    if available is not None:
        query = query.where(Volunteer.is_available == available)
    if skill:
        query = query.where(Volunteer.skills.any(skill))
    if cursor:
        query = query.where(Volunteer.id > cursor)

    query = query.limit(limit + 1)
    result = await db.execute(query)
    volunteers = result.scalars().all()

    has_more = len(volunteers) > limit
    volunteers = volunteers[:limit]

    data = []
    for v in volunteers:
        data.append({
            "id": str(v.id),
            "display_handle": v.display_handle,
            "skills": v.skills or [],
            "max_radius_km": v.max_radius_km,
            "lat": float(v.lat) if v.lat else None,
            "lng": float(v.lng) if v.lng else None,
            "city_id": v.city_id,
            "fatigue_score": float(v.fatigue_score),
            "performance_rating": float(v.performance_rating) if v.performance_rating else None,
            "is_available": v.is_available,
        })

    return APIResponse(
        data=data,
        meta={"cursor": str(volunteers[-1].id) if volunteers and has_more else None, "has_more": has_more, "limit": limit},
    )


@router.post("", status_code=201)
async def create_volunteer(
    request: VolunteerCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new volunteer profile."""
    try:
        volunteer = Volunteer(
            display_handle=request.display_handle,
            skills=request.skills,
            max_radius_km=request.max_radius_km,
            lat=request.lat,
            lng=request.lng,
            city_id=request.city_id,
        )
        db.add(volunteer)
        await db.commit()
        await db.refresh(volunteer)

        return APIResponse(data={
            "id": str(volunteer.id),
            "display_handle": volunteer.display_handle,
            "skills": volunteer.skills,
            "max_radius_km": volunteer.max_radius_km,
            "is_available": volunteer.is_available,
        })
    except Exception as e:
        logger.error("Create volunteer error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail={
            "status": "error", "code": "CREATE_FAILED",
            "message": "Failed to create volunteer.",
            "timestamp": datetime.now(timezone.utc).isoformat()})


@router.get("/{volunteer_id}")
async def get_volunteer(volunteer_id: str, db: AsyncSession = Depends(get_db)):
    """Get volunteer profile with dispatch history."""
    result = await db.execute(select(Volunteer).where(Volunteer.id == volunteer_id))
    volunteer = result.scalar_one_or_none()

    if not volunteer:
        raise HTTPException(status_code=404, detail={
            "status": "error", "code": "VOLUNTEER_NOT_FOUND",
            "message": f"Volunteer {volunteer_id} not found",
            "timestamp": datetime.now(timezone.utc).isoformat()})

    # Get dispatch history
    dispatch_result = await db.execute(
        select(Dispatch).where(Dispatch.volunteer_id == volunteer_id)
        .order_by(Dispatch.created_at.desc()).limit(10)
    )
    dispatches = dispatch_result.scalars().all()

    return APIResponse(data={
        "id": str(volunteer.id),
        "display_handle": volunteer.display_handle,
        "skills": volunteer.skills or [],
        "max_radius_km": volunteer.max_radius_km,
        "lat": float(volunteer.lat) if volunteer.lat else None,
        "lng": float(volunteer.lng) if volunteer.lng else None,
        "city_id": volunteer.city_id,
        "fatigue_score": float(volunteer.fatigue_score),
        "performance_rating": float(volunteer.performance_rating) if volunteer.performance_rating else None,
        "is_available": volunteer.is_available,
        "dispatch_history": [{
            "id": str(d.id),
            "ward_id": str(d.ward_id),
            "status": d.status,
            "css_at_dispatch": float(d.css_at_dispatch) if d.css_at_dispatch else None,
            "dispatched_at": d.dispatched_at.isoformat() if d.dispatched_at else None,
            "coordinator_rating": d.coordinator_rating,
        } for d in dispatches],
    })


@router.put("/{volunteer_id}")
async def update_volunteer(
    volunteer_id: str,
    request: VolunteerUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update volunteer profile."""
    result = await db.execute(select(Volunteer).where(Volunteer.id == volunteer_id))
    volunteer = result.scalar_one_or_none()

    if not volunteer:
        raise HTTPException(status_code=404, detail={
            "status": "error", "code": "VOLUNTEER_NOT_FOUND",
            "message": f"Volunteer {volunteer_id} not found",
            "timestamp": datetime.now(timezone.utc).isoformat()})

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(volunteer, field, value)

    await db.commit()
    await db.refresh(volunteer)

    return APIResponse(data={
        "id": str(volunteer.id),
        "display_handle": volunteer.display_handle,
        "skills": volunteer.skills or [],
        "max_radius_km": volunteer.max_radius_km,
        "is_available": volunteer.is_available,
        "updated": True,
    })
