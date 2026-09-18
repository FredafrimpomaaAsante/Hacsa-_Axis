from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EventStatus


class EventCreate(BaseModel):
    name: str
    description: str | None = None
    venue: str
    start_at: datetime
    end_at: datetime
    status: EventStatus = EventStatus.DRAFT


class EventUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    venue: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    status: EventStatus | None = None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organizer_id: int
    name: str
    description: str | None
    venue: str
    start_at: datetime
    end_at: datetime
    status: EventStatus
    created_at: datetime


class SessionCreate(BaseModel):
    title: str
    speaker: str | None = None
    location: str | None = None
    start_at: datetime
    end_at: datetime
    capacity: int = Field(default=0, ge=0)


class SessionUpdate(BaseModel):
    title: str | None = None
    speaker: str | None = None
    location: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    capacity: int | None = Field(default=None, ge=0)


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    title: str
    speaker: str | None
    location: str | None
    start_at: datetime
    end_at: datetime
    capacity: int
    registered_count: int
