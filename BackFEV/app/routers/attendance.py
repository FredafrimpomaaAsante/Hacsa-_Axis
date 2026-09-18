from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.attendance import (
    CheckIn,
    ScanRejection,
)

from app.models.enums import AuditAction

from app.schemas.attendance import (
    CheckInCreate,
    CheckInResponse,
    ScanRejectionResponse,
)

from app.security import (
    CurrentUser,
    OPS_ROLES,
    require_roles,
    record_audit,
)

from app.realtime import manager


router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"]
)


@router.post(
    "/check-in",
    response_model=CheckInResponse
)
async def check_in_participant(
    payload: CheckInCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(*OPS_ROLES)
    )
):
    existing = db.query(CheckIn).filter(
        CheckIn.event_id == payload.event_id,
        CheckIn.participant_id == payload.participant_id
    ).first()

    if existing:

        rejection = ScanRejection(
            event_id=payload.event_id,
            pass_code=payload.pass_code,
            reason="Participant already checked in",
            scanned_by=user.id
        )

        db.add(rejection)
        db.commit()

        record_audit(
            db=db,
            user=user,
            action=AuditAction.UPDATE,
            entity_type="check_in",
            entity_id=existing.id,
            detail="Duplicate check-in rejected"
        )

        await manager.broadcast({
            "type": "check_in_rejected",
            "event_id": payload.event_id,
            "participant_id": payload.participant_id,
            "reason": "Participant already checked in",
            "message": "Duplicate check-in rejected"
        })

        raise HTTPException(
            status_code=409,
            detail="Participant already checked in"
        )


    check_in = CheckIn(
        event_id=payload.event_id,
        participant_id=payload.participant_id,
        pass_code=payload.pass_code,
        method=payload.method,
        scanned_by=user.id
    )

    db.add(check_in)
    db.commit()
    db.refresh(check_in)

    record_audit(
        db=db,
        user=user,
        action=AuditAction.CREATE,
        entity_type="check_in",
        entity_id=check_in.id,
        detail="Participant checked in"
    )

    await manager.broadcast({
        "type": "participant_checked_in",
        "event_id": check_in.event_id,
        "participant_id": check_in.participant_id,
        "check_in_id": check_in.id,
        "method": check_in.method.value,
        "checked_in_at": check_in.checked_in_at.isoformat(),
        "message": "Participant checked in"
    })

    return check_in


@router.get(
    "/check-ins",
    response_model=list[CheckInResponse]
)
def list_check_ins(
    event_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(*OPS_ROLES)
    )
):
    check_ins = db.query(CheckIn).filter(
        CheckIn.event_id == event_id
    ).order_by(
        CheckIn.checked_in_at.desc()
    ).all()

    record_audit(
        db=db,
        user=user,
        action=AuditAction.READ,
        entity_type="check_in",
        detail=f"Viewed check-ins for event {event_id}"
    )

    return check_ins


@router.get(
    "/rejections",
    response_model=list[ScanRejectionResponse]
)
def list_scan_rejections(
    event_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "organiser",
            "safety_officer",
            "ops_lead"
        )
    )
):
    rejections = db.query(ScanRejection).filter(
        ScanRejection.event_id == event_id
    ).order_by(
        ScanRejection.occurred_at.desc()
    ).all()

    record_audit(
        db=db,
        user=user,
        action=AuditAction.READ,
        entity_type="scan_rejection",
        detail=(
            f"Viewed rejected scans "
            f"for event {event_id}"
        )
    )

    return rejections