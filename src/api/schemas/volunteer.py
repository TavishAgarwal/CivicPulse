"""CivicPulse — Volunteer Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VolunteerCreate(BaseModel):
    display_handle: str = Field(..., min_length=2, max_length=50)
    skills: list[str] = Field(..., min_length=1)
    max_radius_km: int = Field(default=10, ge=1, le=50)
    lat: Optional[float] = None
    lng: Optional[float] = None
    city_id: Optional[str] = None


class VolunteerUpdate(BaseModel):
    display_handle: Optional[str] = None
    skills: Optional[list[str]] = None
    max_radius_km: Optional[int] = Field(default=None, ge=1, le=50)
    is_available: Optional[bool] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    city_id: Optional[str] = None


class VolunteerResponse(BaseModel):
    id: str
    display_handle: str
    skills: list[str]
    max_radius_km: int
    lat: Optional[float] = None
    lng: Optional[float] = None
    city_id: Optional[str] = None
    fatigue_score: float
    performance_rating: Optional[float] = None
    is_available: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
