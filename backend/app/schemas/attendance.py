from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import CheckInMethod


# Data needed when a participant checks in
class CheckInCreate(BaseModel):

    event_id: str
    participant_id: str
    pass_code: str
    method: CheckInMethod = CheckInMethod.QR_SCAN
    scanned_by: str | None = None


# Data returned after a successful check-in
class CheckInResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    participant_id: str
    pass_code: str
    method: CheckInMethod
    scanned_by: str
    checked_in_at: datetime


# Data returned when a scan is rejected
class ScanRejectionResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    pass_code: str | None
    reason: str
    scanned_by: str
    occurred_at: datetime