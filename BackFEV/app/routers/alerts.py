from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.safety import (
    Incident,
    SafetyAlert,
    AlertEscalation,
)
from app.models.enums import (
    AlertLevel,
    EscalationLevel,
    IncidentSeverity,
    AuditAction,
)
from app.schemas.safety import (
    AlertCreate,
    AlertEscalate,
    AlertResponse,
)
from app.security import (
    CurrentUser,
    OPS_ROLES,
    require_roles,
    record_audit,
)
from app.realtime import manager


router = APIRouter(
    prefix="/alerts",
    tags=["Safety Alerts"]
)


def escalation_time_for(severity):
    if severity == IncidentSeverity.CRITICAL:
        return settings.ESCALATION_MINUTES_CRITICAL

    if severity == IncidentSeverity.HIGH:
        return settings.ESCALATION_MINUTES_HIGH

    if severity == IncidentSeverity.MEDIUM:
        return settings.ESCALATION_MINUTES_MEDIUM

    return settings.ESCALATION_MINUTES_LOW


def next_escalation_level(current):
    if current == EscalationLevel.NONE:
        return EscalationLevel.SUPERVISOR

    if current == EscalationLevel.SUPERVISOR:
        return EscalationLevel.OPERATIONS_LEAD

    if current == EscalationLevel.OPERATIONS_LEAD:
        return EscalationLevel.EMERGENCY_SERVICES

    return None


@router.post(
    "/",
    response_model=AlertResponse
)
async def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "safety_officer",
            "ops_lead"
        )
    )
):
    alert = SafetyAlert(
        event_id=payload.event_id,
        alert_type=payload.alert_type,
        level=payload.level,
        zone_name=payload.zone_name,
        incident_id=payload.incident_id,
        message=payload.message,
        created_by=user.id
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    record_audit(
        db=db,
        user=user,
        action=AuditAction.CREATE,
        entity_type="safety_alert",
        entity_id=alert.id,
        detail="Safety alert created"
    )

    await manager.broadcast({
        "type": "safety_alert_created",
        "event_id": alert.event_id,
        "alert_id": alert.id,
        "level": alert.level.value,
        "alert_type": alert.alert_type.value,
        "zone_name": alert.zone_name,
        "message": alert.message
    })

    return alert


@router.get(
    "/",
    response_model=list[AlertResponse]
)
def list_alerts(
    event_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(*OPS_ROLES)
    )
):
    alerts = db.query(SafetyAlert).filter(
        SafetyAlert.event_id == event_id
    ).order_by(
        SafetyAlert.created_at.desc()
    ).all()

    record_audit(
        db=db,
        user=user,
        action=AuditAction.READ,
        entity_type="safety_alert",
        detail=f"Viewed alerts for event {event_id}"
    )

    return alerts


@router.get(
    "/{alert_id}",
    response_model=AlertResponse
)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(*OPS_ROLES)
    )
):
    alert = db.query(SafetyAlert).filter(
        SafetyAlert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    return alert


@router.patch(
    "/{alert_id}/acknowledge",
    response_model=AlertResponse
)
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "safety_officer",
            "ops_lead"
        )
    )
):
    alert = db.query(SafetyAlert).filter(
        SafetyAlert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    if alert.resolved:
        raise HTTPException(
            status_code=400,
            detail="Alert is already resolved"
        )

    if alert.acknowledged_at:
        raise HTTPException(
            status_code=400,
            detail="Alert has already been acknowledged"
        )

    alert.acknowledged_by = user.id
    alert.acknowledged_at = datetime.utcnow()

    db.commit()
    db.refresh(alert)

    record_audit(
        db=db,
        user=user,
        action=AuditAction.UPDATE,
        entity_type="safety_alert",
        entity_id=alert.id,
        detail="Safety alert acknowledged"
    )

    await manager.broadcast({
        "type": "safety_alert_acknowledged",
        "event_id": alert.event_id,
        "alert_id": alert.id,
        "acknowledged_by": user.id,
        "message": "Safety alert acknowledged"
    })

    return alert


@router.patch(
    "/{alert_id}/escalate",
    response_model=AlertResponse
)
async def escalate_alert(
    alert_id: int,
    payload: AlertEscalate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "safety_officer",
            "ops_lead"
        )
    )
):
    alert = db.query(SafetyAlert).filter(
        SafetyAlert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    if alert.resolved:
        raise HTTPException(
            status_code=400,
            detail="Cannot escalate a resolved alert"
        )

    old_level = alert.escalation_level

    alert.escalation_level = payload.to_level

    escalation = AlertEscalation(
        alert_id=alert.id,
        from_level=old_level,
        to_level=payload.to_level,
        reason=payload.reason,
        escalated_by=user.id
    )

    db.add(escalation)
    db.commit()
    db.refresh(alert)

    record_audit(
        db=db,
        user=user,
        action=AuditAction.UPDATE,
        entity_type="safety_alert",
        entity_id=alert.id,
        detail=(
            f"Alert escalated from "
            f"{old_level.value} to "
            f"{payload.to_level.value}"
        )
    )

    await manager.broadcast({
        "type": "safety_alert_escalated",
        "event_id": alert.event_id,
        "alert_id": alert.id,
        "from_level": old_level.value,
        "to_level": payload.to_level.value,
        "message": "Safety alert escalated"
    })

    return alert


@router.patch(
    "/{alert_id}/resolve",
    response_model=AlertResponse
)
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "safety_officer",
            "ops_lead"
        )
    )
):
    alert = db.query(SafetyAlert).filter(
        SafetyAlert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    if alert.resolved:
        raise HTTPException(
            status_code=400,
            detail="Alert is already resolved"
        )

    alert.resolved = True
    alert.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(alert)

    record_audit(
        db=db,
        user=user,
        action=AuditAction.UPDATE,
        entity_type="safety_alert",
        entity_id=alert.id,
        detail="Safety alert resolved"
    )

    await manager.broadcast({
        "type": "safety_alert_resolved",
        "event_id": alert.event_id,
        "alert_id": alert.id,
        "message": "Safety alert resolved"
    })

    return alert


@router.post(
    "/sweep",
    response_model=list[AlertResponse]
)
async def escalation_sweep(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles("ops_lead")
    )
):
    incidents = db.query(Incident).filter(
        Incident.resolved_at.is_(None)
    ).all()

    escalated_alerts = []

    now = datetime.utcnow()

    for incident in incidents:

        if incident.severity not in [
            IncidentSeverity.MEDIUM,
            IncidentSeverity.HIGH,
            IncidentSeverity.CRITICAL
        ]:
            continue

        minutes = escalation_time_for(
            incident.severity
        )

        deadline = (
            incident.created_at
            + timedelta(minutes=minutes)
        )

        if now < deadline:
            continue

        alert = db.query(SafetyAlert).filter(
            SafetyAlert.incident_id == incident.id,
            SafetyAlert.resolved.is_(False)
        ).first()

        if not alert:
            alert = SafetyAlert(
                event_id=incident.event_id,
                alert_type="incident",
                level=AlertLevel.CRITICAL,
                escalation_level=EscalationLevel.NONE,
                incident_id=incident.id,
                message=(
                    f"Incident {incident.id} "
                    "requires escalation"
                ),
                created_by=user.id
            )

            db.add(alert)
            db.commit()
            db.refresh(alert)

        next_level = next_escalation_level(
            alert.escalation_level
        )

        if next_level is None:
            continue

        old_level = alert.escalation_level

        alert.escalation_level = next_level

        escalation = AlertEscalation(
            alert_id=alert.id,
            from_level=old_level,
            to_level=next_level,
            reason=(
                "Automatic escalation after "
                "response deadline"
            ),
            escalated_by=user.id
        )

        db.add(escalation)
        db.commit()
        db.refresh(alert)

        escalated_alerts.append(alert)

        await manager.broadcast({
            "type": "safety_alert_escalated",
            "event_id": alert.event_id,
            "alert_id": alert.id,
            "incident_id": incident.id,
            "from_level": old_level.value,
            "to_level": next_level.value,
            "message": "Alert automatically escalated"
        })

    return escalated_alerts