"""CivicPulse — Signal ORM Model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Signal(Base):
    __tablename__ = "signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"))
    source = Column(String, nullable=False)
    signal_type = Column(String, nullable=False)
    intensity_score = Column(Numeric(4, 3), nullable=False)
    confidence = Column(Numeric(4, 3), nullable=False)
    signal_timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    ward = relationship("Ward", back_populates="signals")
