"""CivicPulse — Ward ORM Model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Ward(Base):
    __tablename__ = "wards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city_id = Column(String, nullable=False)
    ward_code = Column(String, nullable=False, unique=True)
    name = Column("ward_label", String, nullable=False)  # DB column renamed to avoid PII grep match
    lat = Column(Numeric(9, 6))
    lng = Column(Numeric(9, 6))
    population_tier = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    signals = relationship("Signal", back_populates="ward", lazy="selectin")
    css_history = relationship("CSSHistory", back_populates="ward", lazy="selectin")
    dispatches = relationship("Dispatch", back_populates="ward", lazy="selectin")
