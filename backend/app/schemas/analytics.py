from datetime import datetime

from pydantic import BaseModel


class TimelineBucket(BaseModel):
    bucket: str
    count: int


class ZoneStatus(BaseModel):
    zone_name: str
    current_count: int
    capacity: int
    utilisation: float


class IncidentStats(BaseModel):
    open: int
    in_progress: int
    resolved: int
    by_severity: dict[str, int]
    average_response_seconds: float | None


class OperationalOverview(BaseModel):
    event_id: str
    generated_at: datetime

    total_checked_in: int
    rejected_scans: int

    incidents: IncidentStats

    active_alerts: int
    escalated_alerts: int

    zones: list[ZoneStatus]