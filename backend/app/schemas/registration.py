from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventRegistrationCreate(BaseModel):
    event_id: str


class EventRegistrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    event_name: str
    registered: bool = True
    registered_at: datetime
