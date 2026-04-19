"""CivicPulse — Dispatch ORM Model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Dispatch(Base):
    __tablename__ = "dispatches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"))
    volunteer_id = Column(UUID(as_uuid=True), ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True)
    css_at_dispatch = Column(Numeric(5, 2))
    status = Column(String, nullable=False, default="pending")
    match_score = Column(Numeric(5, 4))
    dispatched_at = Column(DateTime(timezone=True))
    confirmed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    coordinator_notes = Column(Text)
    coordinator_rating = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    ward = relationship("Ward", back_populates="dispatches")
    volunteer = relationship("Volunteer", back_populates="dispatches")


class CSSHistory(Base):
    __tablename__ = "css_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"))
    css_score = Column(Numeric(5, 2), nullable=False)
    contributing_signals = Column(String)  # JSONB stored as text
    computed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    ward = relationship("Ward", back_populates="css_history")
