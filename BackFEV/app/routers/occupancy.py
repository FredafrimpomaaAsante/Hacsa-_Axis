from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

from app.models.safety import (
    VenueZone,
    OccupancyReading,
    SafetyAlert,
)

from app.models.enums import (
    AuditAction,
    AlertType,
    AlertLevel,
    EscalationLevel,
)

from app.schemas.safety import (
    OccupancyReport,
    OccupancyDelta,
    VenueZoneResponse,
    OccupancyReadingResponse,
)

from app.security import (
    CurrentUser,
    OPS_ROLES,
    require_roles,
    record_audit,
)

from app.realtime import manager


router = APIRouter(
    prefix="/occupancy",
    tags=["Occupancy"]
)


def create_occupancy_alert(
    zone: VenueZone,
    db: Session,
    user: CurrentUser
):
    utilisation = zone.utilisation

    if utilisation >= settings.OCCUPANCY_CRITICAL_THRESHOLD:

        level = AlertLevel.CRITICAL

        message = (
            f"Critical occupancy in "
            f"{zone.zone_name}: "
            f"{zone.current_count}/"
            f"{zone.capacity}"
        )

    elif utilisation >= settings.OCCUPANCY_ELEVATED_THRESHOLD:

        level = AlertLevel.ELEVATED

        message = (
            f"High occupancy in "
            f"{zone.zone_name}: "
            f"{zone.current_count}/"
            f"{zone.capacity}"
        )

    else:
        return None


    existing_alert = db.query(
        SafetyAlert
    ).filter(
        SafetyAlert.event_id == zone.event_id,
        SafetyAlert.zone_name == zone.zone_name,
        SafetyAlert.alert_type == AlertType.CROWD,
        SafetyAlert.resolved.is_(False)
    ).first()


    if existing_alert:

        existing_alert.level = level
        existing_alert.message = message

        db.commit()
        db.refresh(existing_alert)

        return existing_alert


    alert = SafetyAlert(
        event_id=zone.event_id,
        alert_type=AlertType.CROWD,
        level=level,
        escalation_level=EscalationLevel.NONE,
        zone_name=zone.zone_name,
        message=message,
        created_by=user.id
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


@router.put(
    "/report",
    response_model=VenueZoneResponse
)
async def report_occupancy(
    payload: OccupancyReport,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "staff",
            "safety_officer",
            "ops_lead"
        )
    )
):
    if payload.current_count > payload.capacity:

        raise HTTPException(
            status_code=400,
            detail="Occupancy cannot exceed venue capacity"
        )


    zone = db.query(VenueZone).filter(
        VenueZone.event_id == payload.event_id,
        VenueZone.zone_name == payload.zone_name
    ).first()


    if not zone:

        zone = VenueZone(
            event_id=payload.event_id,
            zone_name=payload.zone_name,
            current_count=payload.current_count,
            capacity=payload.capacity
        )

        db.add(zone)

    else:

        zone.current_count = payload.current_count
        zone.capacity = payload.capacity


    db.commit()
    db.refresh(zone)


    reading = OccupancyReading(
        event_id=zone.event_id,
        zone_name=zone.zone_name,
        current_count=zone.current_count,
        capacity=zone.capacity,
        recorded_by=user.id
    )

    db.add(reading)
    db.commit()


    alert = create_occupancy_alert(
        zone=zone,
        db=db,
        user=user
    )


    record_audit(
        db=db,
        user=user,
        action=AuditAction.UPDATE,
        entity_type="venue_zone",
        entity_id=zone.id,
        detail=(
            f"Occupancy reported for "
            f"{zone.zone_name}: "
            f"{zone.current_count}/"
            f"{zone.capacity}"
        )
    )


    await manager.broadcast({
        "type": "occupancy_updated",
        "event_id": zone.event_id,
        "zone_name": zone.zone_name,
        "current_count": zone.current_count,
        "capacity": zone.capacity,
        "utilisation": zone.utilisation,
        "message": "Venue occupancy updated"
    })


    if alert:

        await manager.broadcast({
            "type": "occupancy_alert",
            "event_id": alert.event_id,
            "zone_name": alert.zone_name,
            "level": alert.level.value,
            "message": alert.message
        })


    return zone


@router.post(
    "/delta",
    response_model=VenueZoneResponse
)
async def adjust_occupancy(
    payload: OccupancyDelta,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "staff",
            "safety_officer",
            "ops_lead"
        )
    )
):
    zone = db.query(VenueZone).filter(
        VenueZone.event_id == payload.event_id,
        VenueZone.zone_name == payload.zone_name
    ).first()


    if not zone:

        raise HTTPException(
            status_code=404,
            detail="Zone not found"
        )


    new_count = zone.current_count + payload.delta


    if new_count < 0:
        new_count = 0


    if new_count > zone.capacity:

        raise HTTPException(
            status_code=400,
            detail="Occupancy cannot exceed venue capacity"
        )


    zone.current_count = new_count

    db.commit()
    db.refresh(zone)


    reading = OccupancyReading(
        event_id=zone.event_id,
        zone_name=zone.zone_name,
        current_count=zone.current_count,
        capacity=zone.capacity,
        recorded_by=user.id
    )

    db.add(reading)
    db.commit()


    alert = create_occupancy_alert(
        zone=zone,
        db=db,
        user=user
    )


    record_audit(
        db=db,
        user=user,
        action=AuditAction.UPDATE,
        entity_type="venue_zone",
        entity_id=zone.id,
        detail=(
            f"Occupancy adjusted by "
            f"{payload.delta}. "
            f"New count: "
            f"{zone.current_count}"
        )
    )


    await manager.broadcast({
        "type": "occupancy_updated",
        "event_id": zone.event_id,
        "zone_name": zone.zone_name,
        "current_count": zone.current_count,
        "capacity": zone.capacity,
        "utilisation": zone.utilisation,
        "message": "Venue occupancy updated"
    })


    if alert:

        await manager.broadcast({
            "type": "occupancy_alert",
            "event_id": alert.event_id,
            "zone_name": alert.zone_name,
            "level": alert.level.value,
            "message": alert.message
        })


    return zone


@router.get(
    "/zones",
    response_model=list[VenueZoneResponse]
)
def list_zones(
    event_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(*OPS_ROLES)
    )
):
    zones = db.query(VenueZone).filter(
        VenueZone.event_id == event_id
    ).all()


    record_audit(
        db=db,
        user=user,
        action=AuditAction.READ,
        entity_type="venue_zone",
        detail=(
            f"Viewed occupancy zones "
            f"for event {event_id}"
        )
    )


    return zones


@router.get(
    "/history",
    response_model=list[OccupancyReadingResponse]
)
def zone_history(
    event_id: str,
    zone_name: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(*OPS_ROLES)
    )
):
    readings = db.query(
        OccupancyReading
    ).filter(
        OccupancyReading.event_id == event_id,
        OccupancyReading.zone_name == zone_name
    ).order_by(
        OccupancyReading.recorded_at.desc()
    ).all()


    record_audit(
        db=db,
        user=user,
        action=AuditAction.READ,
        entity_type="occupancy_reading",
        detail=(
            f"Viewed occupancy history "
            f"for {zone_name}"
        )
    )


    return readings