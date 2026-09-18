from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.connections import get_db

from app.models.attendance import (
    CheckIn,
    ScanRejection,
)

from app.models.safety import (
    Incident,
    VenueZone,
    SafetyAlert,
)

from app.models.enums import (
    IncidentStatus,
    EscalationLevel,
    AuditAction,
)

from app.schemas.analytics import (
    OperationalOverview,
    IncidentStats,
    ZoneStatus,
    TimelineBucket,
)

from app.security import (
    CurrentUser,
    OPS_ROLES,
    require_roles,
    record_audit,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Operational Analytics"]
)


@router.get(
    "/overview",
    response_model=OperationalOverview
)
def operational_overview(
    event_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(*OPS_ROLES)
    )
):

    check_ins = db.query(CheckIn).filter(
        CheckIn.event_id == event_id
    ).count()


    rejections = db.query(
        ScanRejection
    ).filter(
        ScanRejection.event_id == event_id
    ).count()


    incidents = db.query(
        Incident
    ).filter(
        Incident.event_id == event_id
    ).all()


    open_count = 0
    in_progress_count = 0
    resolved_count = 0


    severity_counts = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0
    }


    response_times = []


    for incident in incidents:

        if incident.status == IncidentStatus.OPEN:

            open_count += 1

        elif incident.status in [
            IncidentStatus.ASSIGNED,
            IncidentStatus.IN_PROGRESS
        ]:

            in_progress_count += 1

        elif incident.status in [
            IncidentStatus.RESOLVED,
            IncidentStatus.CLOSED
        ]:

            resolved_count += 1


        severity_counts[
            incident.severity.value
        ] += 1


        if incident.response_time_seconds is not None:

            response_times.append(
                incident.response_time_seconds
            )


    if response_times:

        average_response_seconds = round(
            sum(response_times)
            / len(response_times),
            1
        )

    else:

        average_response_seconds = None


    incident_stats = IncidentStats(
        open=open_count,
        in_progress=in_progress_count,
        resolved=resolved_count,
        by_severity=severity_counts,
        average_response_seconds=(
            average_response_seconds
        )
    )


    zones = db.query(
        VenueZone
    ).filter(
        VenueZone.event_id == event_id
    ).all()


    zone_statuses = []


    for zone in zones:

        zone_statuses.append(
            ZoneStatus(
                zone_name=zone.zone_name,
                current_count=zone.current_count,
                capacity=zone.capacity,
                utilisation=zone.utilisation
            )
        )


    alerts = db.query(
        SafetyAlert
    ).filter(
        SafetyAlert.event_id == event_id,
        SafetyAlert.resolved.is_(False)
    ).all()


    active_alerts = len(alerts)


    escalated_alerts = sum(
        1
        for alert in alerts
        if alert.escalation_level
        != EscalationLevel.NONE
    )


    record_audit(
        db=db,
        user=user,
        action=AuditAction.READ,
        entity_type="analytics",
        detail=(
            f"Viewed operational "
            f"overview for event {event_id}"
        )
    )


    return OperationalOverview(
        event_id=event_id,
        generated_at=datetime.utcnow(),
        total_checked_in=check_ins,
        rejected_scans=rejections,
        incidents=incident_stats,
        active_alerts=active_alerts,
        escalated_alerts=escalated_alerts,
        zones=zone_statuses
    )


@router.get(
    "/attendance-timeline",
    response_model=list[TimelineBucket]
)
def attendance_timeline(
    event_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(*OPS_ROLES)
    )
):

    rows = db.query(
        CheckIn
    ).filter(
        CheckIn.event_id == event_id
    ).all()


    buckets = defaultdict(int)


    for row in rows:

        hour = row.checked_in_at.strftime(
            "%Y-%m-%dT%H:00"
        )

        buckets[hour] += 1


    timeline = []


    for bucket, count in sorted(
        buckets.items()
    ):

        timeline.append(
            TimelineBucket(
                bucket=bucket,
                count=count
            )
        )


    record_audit(
        db=db,
        user=user,
        action=AuditAction.READ,
        entity_type="attendance_timeline",
        detail=(
            f"Viewed attendance timeline "
            f"for event {event_id}"
        )
    )


    return timeline