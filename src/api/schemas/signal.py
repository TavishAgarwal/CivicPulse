"""CivicPulse — Signal Schemas."""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class SignalIngestRequest(BaseModel):
    source: str = Field(..., min_length=1, max_length=100)
    location_pin: str = Field(..., min_length=1, max_length=100)
    signal_type: str = Field(...)
    intensity_score: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime
    confidence: float = Field(..., ge=0.0, le=1.0)

    @field_validator("signal_type")
    @classmethod
    def validate_signal_type(cls, v):
        valid = {"pharmacy", "school", "utility", "social", "foodbank", "health"}
        if v not in valid:
            raise ValueError(f"signal_type must be one of {valid}")
        return v


class SignalResponse(BaseModel):
    signal_id: str
    received_at: datetime
