"""CivicPulse — Ward Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class WardSummary(BaseModel):
    ward_id: str
    ward_name: str
    city_id: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    css_score: Optional[float] = None
    status_label: Optional[str] = None

    model_config = {"from_attributes": True}


class WardDetail(WardSummary):
    ward_code: str
    population_tier: Optional[int] = None
    created_at: Optional[datetime] = None


class WardStress(BaseModel):
    ward_id: str
    ward_name: str
    css_score: Optional[float] = None
    status_label: Optional[str] = None
    signals_breakdown: list[dict] = []


class CSSHistoryPoint(BaseModel):
    css_score: float
    computed_at: datetime


class HeatmapWard(BaseModel):
    ward_id: str
    ward_name: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    css_score: float
    status_label: str
