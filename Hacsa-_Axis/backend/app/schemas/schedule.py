from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.schedule import SessionStatusEnum


class VenueCreate(BaseModel):
    name: str
    location: Optional[str] = None
    capacity: Optional[int] = None
    description: Optional[str] = None


class VenueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: Optional[str] = None
    capacity: Optional[int] = None
    description: Optional[str] = None


class SessionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    venue_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    capacity: Optional[int] = None


class SessionUpdate(BaseModel):
    """Partial update — send only the fields that are changing (e.g. a reschedule
    or a cancellation). Any of start_time/end_time/venue_id/status actually
    changing triggers schedule-change notifications automatically."""

    title: Optional[str] = None
    description: Optional[str] = None
    venue_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    capacity: Optional[int] = None
    status: Optional[SessionStatusEnum] = None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    venue_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    capacity: Optional[int] = None
    status: SessionStatusEnum


class SpeakerAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    speaker_id: int
    assigned_at: datetime


class SessionInterestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    user_id: int
    created_at: datetime

