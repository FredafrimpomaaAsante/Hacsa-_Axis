from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.connections import get_db

from app.models.safety import (
    Incident,
    ResponseAssignment,
    SafetyAlert,
)

from app.models.enums import (
    AlertLevel,
    AlertType,
    EscalationLevel,
    IncidentSeverity,
    IncidentStatus,
    AuditAction,
)
from app.models.user import RoleEnum

from app.schemas.safety import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdateStatus,
    ResponseAssignmentCreate,
    ResponseAssignmentResponse,
)

from app.security import (
    CurrentUser,
    require_roles,
    record_audit,
    OPS_ROLES,
)

from app.realtime import manager


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)


@router.post(
    "/",
    response_model=IncidentResponse
)
async def report_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            *OPS_ROLES,
            RoleEnum.participant,
            RoleEnum.speaker,
            RoleEnum.vendor,
        )
    )
):
    is_medical = "medical" in " ".join(
        value or "" for value in (payload.title, payload.description)
    ).lower()
    severity = IncidentSeverity.CRITICAL if is_medical else payload.severity
    description = payload.description
    if payload.title:
        description = f"{payload.title}: {payload.description}"

    incident = Incident(
        event_id=payload.event_id,
        reported_by=user.id,
        location=payload.location,
        description=description,
        severity=severity
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    record_audit(
        db=db,
        user=user,
        action=AuditAction.CREATE,
        entity_type="incident",
        entity_id=incident.id,
        detail="Incident reported"
    )

    if severity in {IncidentSeverity.HIGH, IncidentSeverity.CRITICAL}:
        medical_alert = is_medical
        alert = SafetyAlert(
            event_id=incident.event_id,
            alert_type=AlertType.MEDICAL if medical_alert else AlertType.INCIDENT,
            level=AlertLevel.CRITICAL if severity == IncidentSeverity.CRITICAL else AlertLevel.ELEVATED,
            escalation_level=EscalationLevel.OPERATIONS_LEAD,
            zone_name=incident.location,
            incident_id=incident.id,
            message=(
                f"Immediate attention: {incident.description} · {incident.location}"
            )[:255],
            created_by=user.id,
        )
        db.add(alert)
        db.commit()

    await manager.broadcast({
        "type": "incident_created",
        "event_id": incident.event_id,
        "incident_id": incident.id,
        "severity": incident.severity.value,
        "location": incident.location,
        "title": payload.title or "Issue reported",
        "description": payload.description,
        "reported_by": user.id,
        "urgent": severity in {IncidentSeverity.HIGH, IncidentSeverity.CRITICAL},
        "status": incident.status.value,
        "message": "Immediate attention required" if severity in {IncidentSeverity.HIGH, IncidentSeverity.CRITICAL} else "New incident reported"
    })

    return incident


@router.get(
    "/",
    response_model=list[IncidentResponse]
)
def list_incidents(
    event_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(*OPS_ROLES)
    )
):
    incidents = db.query(Incident).filter(
        Incident.event_id == event_id
    ).order_by(
        Incident.created_at.desc()
    ).all()

    record_audit(
        db=db,
        user=user,
        action=AuditAction.READ,
        entity_type="incident",
        detail=f"Viewed incidents for event {event_id}"
    )

    return incidents


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse
)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(*OPS_ROLES)
    )
):
    incident = db.query(Incident).filter(
        Incident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    record_audit(
        db=db,
        user=user,
        action=AuditAction.READ,
        entity_type="incident",
        entity_id=incident.id,
        detail="Viewed incident"
    )

    return incident


@router.post(
    "/{incident_id}/assign",
    response_model=ResponseAssignmentResponse
)
async def assign_responder(
    incident_id: int,
    payload: ResponseAssignmentCreate,
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
    incident = db.query(Incident).filter(
        Incident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    if incident.status in [
        IncidentStatus.RESOLVED,
        IncidentStatus.CLOSED
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot assign a responder "
                "to a closed incident"
            )
        )

    assignment = ResponseAssignment(
        incident_id=incident.id,
        responder_id=payload.responder_id,
        assigned_by=user.id,
        notes=payload.notes
    )

    incident.status = IncidentStatus.ASSIGNED

    if not incident.acknowledged_at:
        incident.acknowledged_at = datetime.utcnow()

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    record_audit(
        db=db,
        user=user,
        action=AuditAction.UPDATE,
        entity_type="incident",
        entity_id=incident.id,
        detail=(
            f"Responder {payload.responder_id} "
            "assigned"
        )
    )

    await manager.broadcast({
        "type": "incident_assigned",
        "event_id": incident.event_id,
        "incident_id": incident.id,
        "responder_id": assignment.responder_id,
        "status": incident.status.value,
        "message": "Responder assigned to incident"
    })

    return assignment


@router.patch(
    "/{incident_id}/status",
    response_model=IncidentResponse
)
async def update_incident_status(
    incident_id: int,
    payload: IncidentUpdateStatus,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*OPS_ROLES))
):
    incident = db.query(Incident).filter(
        Incident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    incident.status = payload.status

    if payload.status == IncidentStatus.IN_PROGRESS:
        if not incident.acknowledged_at:
            incident.acknowledged_at = datetime.utcnow()

    if payload.status in [
        IncidentStatus.RESOLVED,
        IncidentStatus.CLOSED
    ]:
        if not incident.resolved_at:
            incident.resolved_at = datetime.utcnow()
        for alert in incident.alerts:
            alert.resolved = True
            alert.resolved_at = incident.resolved_at

    db.commit()
    db.refresh(incident)

    record_audit(
        db=db,
        user=user,
        action=AuditAction.UPDATE,
        entity_type="incident",
        entity_id=incident.id,
        detail=(
            f"Incident status changed to "
            f"{payload.status.value}"
        )
    )

    await manager.broadcast({
        "type": "incident_status_changed",
        "event_id": incident.event_id,
        "incident_id": incident.id,
        "status": incident.status.value,
        "message": "Incident status updated"
    })

    return incident