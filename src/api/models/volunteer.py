"""CivicPulse — Volunteer ORM Model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_handle = Column(String, nullable=False)
    skills = Column(ARRAY(String), nullable=False, default=list)
    max_radius_km = Column(Integer, nullable=False, default=10)
    lat = Column(Numeric(9, 6))
    lng = Column(Numeric(9, 6))
    city_id = Column(String)
    fatigue_score = Column(Numeric(3, 2), nullable=False, default=0.0)
    performance_rating = Column(Numeric(3, 2), nullable=True)
    is_available = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    dispatches = relationship("Dispatch", back_populates="volunteer", lazy="selectin")
