"""CivicPulse — Dispatch Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DispatchSuggestRequest(BaseModel):
    ward_id: str


class DispatchConfirmRequest(BaseModel):
    dispatch_id: str
    volunteer_id: str


class DispatchCompleteRequest(BaseModel):
    coordinator_rating: int = Field(..., ge=1, le=5)
    notes: Optional[str] = None


class VolunteerMatch(BaseModel):
    volunteer_id: str
    display_handle: str
    skills: list[str]
    distance_km: Optional[float] = None
    fatigue_score: float
    match_score: float
    score_breakdown: dict = {}


class DispatchSuggestion(BaseModel):
    ward_id: str
    ward_name: str
    css_score: float
    matches: list[VolunteerMatch]


class DispatchResponse(BaseModel):
    id: str
    ward_id: str
    volunteer_id: Optional[str] = None
    css_at_dispatch: Optional[float] = None
    status: str
    match_score: Optional[float] = None
    dispatched_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    coordinator_rating: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
