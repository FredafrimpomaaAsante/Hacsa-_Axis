from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApplicationStatus


class ApplicationCreate(BaseModel):
    event_id: int
    products: str
    message: str | None = None
    requested_booth_size: str | None = None


class ApplicationReview(BaseModel):
    status: ApplicationStatus
    review_notes: str | None = None
    booth_id: int | None = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor_id: int
    event_id: int
    products: str
    message: str | None
    requested_booth_size: str | None
    status: ApplicationStatus
    review_notes: str | None
    reviewed_by_id: int | None
    reviewed_at: datetime | None
    created_at: datetime
