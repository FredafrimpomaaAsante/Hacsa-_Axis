from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint

from app.connections import Base


class EventRegistration(Base):
    __tablename__ = "event_registrations"
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_registration_user"),
        Index("ix_event_registration_event", "event_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), nullable=False)
    event_name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    registered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
