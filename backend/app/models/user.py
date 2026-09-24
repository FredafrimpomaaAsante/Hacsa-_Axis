import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.connections import Base


class RoleEnum(str, enum.Enum):
    participant = "participant"
    speaker = "speaker"
    organiser = "organiser"
    staff = "staff"
    safety_officer = "safety_officer"
    ops_lead = "ops_lead"


def generate_speaker_code() -> str:
    return f"SPK-{uuid.uuid4().hex[:8].upper()}"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(250), nullable=False)
    email = Column(String(250), unique=True, index=True, nullable=False)
    hashed_password = Column(String(500), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.participant, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    participant_profile = relationship("ParticipantProfile", back_populates="user", uselist=False)
    speaker_profile = relationship("SpeakerProfile", back_populates="user", uselist=False)


class ParticipantProfile(Base):
    __tablename__ = "participant_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    phone_number = Column(String(30), nullable=True)
    organization = Column(String(150), nullable=True)
    bio = Column(Text, nullable=True)
    photo_url = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="participant_profile")


class SpeakerProfile(Base):
    __tablename__ = "speaker_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    speaker_code = Column(String(20), unique=True, index=True, default=generate_speaker_code)
    title = Column(String(150), nullable=True)
    organization = Column(String(150), nullable=True)
    bio = Column(Text, nullable=True)
    photo_url = Column(String(300), nullable=True)
    expertise = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="speaker_profile")
    session_assignments = relationship("SessionSpeaker", back_populates="speaker")
