from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    IncidentSeverity,
    IncidentStatus,
    AlertType,
    AlertLevel,
    EscalationLevel,
)


# -------------------------
# Incidents
# -------------------------

class IncidentCreate(BaseModel):
    event_id: str
    location: str
    description: str
    severity: IncidentSeverity = IncidentSeverity.LOW


class IncidentUpdateStatus(BaseModel):
    status: IncidentStatus


class ResponseAssignmentCreate(BaseModel):
    responder_id: str
    notes: str | None = None


class ResponseAssignmentResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    responder_id: str
    assigned_by: str
    assigned_at: datetime
    notes: str | None
    status: IncidentStatus


class IncidentResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    reported_by: str
    location: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    created_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    response_time_seconds: int | None
    assignments: list[ResponseAssignmentResponse] = Field(
        default_factory=list
    )


# -------------------------
# Occupancy
# -------------------------

class OccupancyReport(BaseModel):
    event_id: str
    zone_name: str
    current_count: int = Field(ge=0)
    capacity: int = Field(gt=0)


class OccupancyDelta(BaseModel):
    event_id: str
    zone_name: str
    delta: int


class VenueZoneResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    zone_name: str
    current_count: int
    capacity: int
    utilisation: float
    updated_at: datetime


class OccupancyReadingResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    zone_name: str
    current_count: int
    capacity: int
    recorded_by: str
    recorded_at: datetime


# -------------------------
# Safety Alerts
# -------------------------

class AlertCreate(BaseModel):
    event_id: str
    alert_type: AlertType = AlertType.OTHER
    level: AlertLevel = AlertLevel.INFO
    zone_name: str | None = None
    incident_id: int | None = None
    message: str


class AlertEscalate(BaseModel):
    to_level: EscalationLevel
    reason: str | None = None


class AlertEscalationResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    from_level: EscalationLevel
    to_level: EscalationLevel
    reason: str | None
    escalated_by: str | None
    escalated_at: datetime


class AlertResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    alert_type: AlertType
    level: AlertLevel
    escalation_level: EscalationLevel
    zone_name: str | None
    incident_id: int | None
    message: str
    created_by: str | None
    created_at: datetime
    acknowledged_by: str | None
    acknowledged_at: datetime | None
    resolved: bool
    resolved_at: datetime | None
    escalations: list[AlertEscalationResponse] = Field(
        default_factory=list
    )