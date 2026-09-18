from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AssignmentStatus, BoothStatus


class BoothCreate(BaseModel):
    code: str
    zone: str | None = None
    size: str = "standard"
    fee: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: BoothStatus = BoothStatus.AVAILABLE


class BoothUpdate(BaseModel):
    zone: str | None = None
    size: str | None = None
    fee: Decimal | None = Field(default=None, ge=0)
    status: BoothStatus | None = None


class BoothOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    code: str
    zone: str | None
    size: str
    fee: Decimal
    status: BoothStatus


class AssignmentCreate(BaseModel):
    booth_id: int
    vendor_id: int
    application_id: int | None = None


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booth_id: int
    vendor_id: int
    application_id: int | None
    assigned_by_id: int
    status: AssignmentStatus
    assigned_at: datetime
    released_at: datetime | None
