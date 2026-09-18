import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.connections import Base


class SessionStatusEnum(str, enum.Enum):
    scheduled = "scheduled"
    rescheduled = "rescheduled"
    cancelled = "cancelled"


class Venue(Base):
    """A physical location where sessions happen."""

    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    location = Column(String(200), nullable=True)
    capacity = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)

    sessions = relationship("Session", back_populates="venue")


class Session(Base):
    """A single scheduled session/talk within the event."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=True)
    status = Column(
        Enum(SessionStatusEnum), default=SessionStatusEnum.scheduled, nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    venue = relationship("Venue", back_populates="sessions")
    speaker_assignments = relationship("SessionSpeaker", back_populates="session")
    interests = relationship("SessionInterest", back_populates="session")


class SessionSpeaker(Base):
    """Speaker-to-session assignment (many-to-many: a session can have several
    speakers, and a speaker can be assigned to several sessions)."""

    __tablename__ = "session_speakers"
    __table_args__ = (
        UniqueConstraint("session_id", "speaker_id", name="uq_session_speaker"),
    )

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    speaker_id = Column(Integer, ForeignKey("speaker_profiles.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="speaker_assignments")
    speaker = relationship("SpeakerProfile", back_populates="session_assignments")


class SessionInterest(Base):
    """A participant following a session, so they get schedule-change notifications
    even without being an assigned speaker."""

    __tablename__ = "session_interests"
    __table_args__ = (
        UniqueConstraint("session_id", "user_id", name="uq_session_interest"),
    )

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="interests")

