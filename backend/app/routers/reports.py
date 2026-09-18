import csv
import io
from datetime import datetime
from typing import Any, Iterable, Sequence

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.connections import get_db

from app.models.attendance import (
    CheckIn,
    ScanRejection,
)

from app.models.safety import (
    Incident,
    SafetyAlert,
    OccupancyReading,
)

from app.models.audit import AuditLog

from app.models.enums import AuditAction

from app.security import (
    CurrentUser,
    require_roles,
    record_audit,
)

router = APIRouter(
    prefix="/reports",
    tags=["Reports & Exports"]
)


def csv_response(
    headers: Sequence[str],
    rows: Iterable[Sequence[Any]],
    filename: str
):
    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(headers)

    for row in rows:
        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
            f'attachment; filename="{filename}"'
        }
    )


def timestamped_filename(
    name: str
) -> str:

    timestamp = datetime.utcnow().strftime(
        "%Y%m%d_%H%M%S"
    )

    return f"{name}_{timestamp}.csv"


@router.get("/attendance")
def export_attendance(
    event_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "organiser",
            "ops_lead",
            "organiser",
        )
    )
):

    rows = db.query(CheckIn).filter(
        CheckIn.event_id == event_id
    ).order_by(
        CheckIn.checked_in_at.asc()
    ).all()

    data = []

    for row in rows:
        data.append([
            row.id,
            row.event_id,
            row.participant_id,
            row.method.value,
            row.scanned_by,
            row.checked_in_at.isoformat()
        ])

    record_audit(
        db=db,
        user=user,
        action=AuditAction.EXPORT,
        entity_type="attendance",
        detail=(
            f"Exported attendance "
            f"for event {event_id}"
        )
    )

    return csv_response(
        [
            "id",
            "event_id",
            "participant_id",
            "method",
            "scanned_by",
            "checked_in_at"
        ],
        data,
        timestamped_filename("attendance")
    )


@router.get("/incidents")
def export_incidents(
    event_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "safety_officer",
            "ops_lead",
            "organiser",
        )
    )
):

    rows = db.query(Incident).filter(
        Incident.event_id == event_id
    ).order_by(
        Incident.created_at.asc()
    ).all()

    data = []

    for row in rows:

        responders = "; ".join(
            assignment.responder_id
            for assignment in row.assignments
        )

        data.append([
            row.id,
            row.severity.value,
            row.status.value,
            row.location,
            row.description.replace(
                "\n",
                " "
            ),
            row.reported_by,
            row.created_at.isoformat(),
            (
                row.acknowledged_at.isoformat()
                if row.acknowledged_at
                else ""
            ),
            (
                row.resolved_at.isoformat()
                if row.resolved_at
                else ""
            ),
            (
                row.response_time_seconds
                if row.response_time_seconds
                is not None
                else ""
            ),
            responders
        ])

    record_audit(
        db=db,
        user=user,
        action=AuditAction.EXPORT,
        entity_type="incidents",
        detail=(
            f"Exported incidents "
            f"for event {event_id}"
        )
    )

    return csv_response(
        [
            "id",
            "severity",
            "status",
            "location",
            "description",
            "reported_by",
            "created_at",
            "acknowledged_at",
            "resolved_at",
            "response_time_seconds",
            "responders"
        ],
        data,
        timestamped_filename("incidents")
    )


@router.get("/alerts")
def export_alerts(
    event_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "safety_officer",
            "ops_lead",
            "organiser",
        )
    )
):

    rows = db.query(SafetyAlert).filter(
        SafetyAlert.event_id == event_id
    ).order_by(
        SafetyAlert.created_at.asc()
    ).all()

    data = []

    for row in rows:
        data.append([
            row.id,
            row.alert_type.value,
            row.level.value,
            row.escalation_level.value,
            row.zone_name or "",
            row.incident_id or "",
            row.message,
            row.created_by or "",
            row.created_at.isoformat(),
            row.acknowledged_by or "",
            row.resolved,
            (
                row.resolved_at.isoformat()
                if row.resolved_at
                else ""
            )
        ])

    record_audit(
        db=db,
        user=user,
        action=AuditAction.EXPORT,
        entity_type="alerts",
        detail=(
            f"Exported alerts "
            f"for event {event_id}"
        )
    )

    return csv_response(
        [
            "id",
            "alert_type",
            "level",
            "escalation_level",
            "zone_name",
            "incident_id",
            "message",
            "created_by",
            "created_at",
            "acknowledged_by",
            "resolved",
            "resolved_at"
        ],
        data,
        timestamped_filename("alerts")
    )


@router.get("/occupancy")
def export_occupancy(
    event_id: str,
    zone_name: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "organiser",
            "safety_officer",
            "ops_lead",
            "organiser",
        )
    )
):

    query = db.query(
        OccupancyReading
    ).filter(
        OccupancyReading.event_id == event_id
    )

    if zone_name:
        query = query.filter(
            OccupancyReading.zone_name
            == zone_name
        )

    rows = query.order_by(
        OccupancyReading.recorded_at.asc()
    ).all()

    data = []

    for row in rows:

        utilisation = (
            round(
                row.current_count
                / row.capacity
                * 100,
                1
            )
            if row.capacity
            else 0
        )

        data.append([
            row.id,
            row.zone_name,
            row.current_count,
            row.capacity,
            utilisation,
            row.recorded_by,
            row.recorded_at.isoformat()
        ])

    record_audit(
        db=db,
        user=user,
        action=AuditAction.EXPORT,
        entity_type="occupancy",
        detail=(
            f"Exported occupancy "
            f"for event {event_id}"
        )
    )

    return csv_response(
        [
            "id",
            "zone_name",
            "current_count",
            "capacity",
            "utilisation_pct",
            "recorded_by",
            "recorded_at"
        ],
        data,
        timestamped_filename("occupancy")
    )


@router.get("/audit")
def export_audit_log(
    since: datetime | None = None,
    limit: int = Query(
        5000,
        le=50000
    ),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "ops_lead",
            "organiser",
        )
    )
):

    query = db.query(AuditLog)

    if since:
        query = query.filter(
            AuditLog.created_at >= since
        )

    rows = query.order_by(
        AuditLog.created_at.asc()
    ).limit(limit).all()

    data = []

    for row in rows:
        data.append([
            row.id,
            row.actor_id,
            row.actor_role,
            row.action.value,
            row.entity_type,
            row.entity_id or "",
            row.detail or "",
            row.ip_address or "",
            row.created_at.isoformat()
        ])

    record_audit(
        db=db,
        user=user,
        action=AuditAction.EXPORT,
        entity_type="audit_log",
        detail="Exported audit log"
    )

    return csv_response(
        [
            "id",
            "actor_id",
            "actor_role",
            "action",
            "entity_type",
            "entity_id",
            "detail",
            "ip_address",
            "created_at"
        ],
        data,
        timestamped_filename("audit_log")
    )


@router.get("/summary")
def event_summary_report(
    event_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "organiser",
            "ops_lead",
            "organiser",
        )
    )
):

    check_ins = db.query(CheckIn).filter(
        CheckIn.event_id == event_id
    ).all()

    incidents = db.query(Incident).filter(
        Incident.event_id == event_id
    ).all()

    alerts = db.query(SafetyAlert).filter(
        SafetyAlert.event_id == event_id
    ).all()

    rejections = db.query(
        ScanRejection
    ).filter(
        ScanRejection.event_id == event_id
    ).count()

    resolved_incidents = [
        incident
        for incident in incidents
        if incident.response_time_seconds
        is not None
    ]

    average_response_seconds = None

    if resolved_incidents:

        average_response_seconds = round(
            sum(
                incident.response_time_seconds
                for incident in resolved_incidents
            )
            / len(resolved_incidents),
            1
        )

    record_audit(
        db=db,
        user=user,
        action=AuditAction.EXPORT,
        entity_type="event_summary",
        detail=(
            f"Generated event summary "
            f"for event {event_id}"
        )
    )

    return {
        "event_id": event_id,
        "generated_at":
            datetime.utcnow().isoformat(),

        "attendance": {
            "total_checked_in":
                len(check_ins),

            "rejected_scans":
                rejections,

            "first_check_in": (
                min(
                    check_in.checked_in_at
                    for check_in in check_ins
                ).isoformat()
                if check_ins
                else None
            ),

            "last_check_in": (
                max(
                    check_in.checked_in_at
                    for check_in in check_ins
                ).isoformat()
                if check_ins
                else None
            )
        },

        "safety": {
            "total_incidents":
                len(incidents),

            "resolved_incidents":
                len(resolved_incidents),

            "unresolved_incidents":
                len(incidents)
                - len(resolved_incidents),

            "average_response_seconds":
                average_response_seconds,

            "total_alerts":
                len(alerts),

            "escalated_alerts":
                sum(
                    1
                    for alert in alerts
                    if alert.escalations
                )
        }
    }