from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.networking import ConnectionStatusEnum


class ConnectionRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester_id: int
    recipient_id: int
    status: ConnectionStatusEnum
    created_at: datetime
    responded_at: Optional[datetime] = None


class ConnectionRespond(BaseModel):
    accept: bool

