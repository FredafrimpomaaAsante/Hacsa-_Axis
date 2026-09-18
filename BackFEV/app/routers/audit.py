from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import AuditLog
from app.models.enums import AuditAction
from app.schemas.audit import AuditLogOut

from app.security import (
    CurrentUser,
    require_roles,
    OPS_ROLES,
    record_audit,
)


router = APIRouter(
    prefix="/audit",
    tags=["Audit & Secure Access"]
)


@router.get(
    "/logs",
    response_model=list[AuditLogOut]
)
def list_audit_logs(
    actor_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    action: AuditAction | None = None,
    since: datetime | None = None,
    limit: int = Query(
        200,
        le=1000
    ),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "ops_lead"
        )
    )
):

    query = db.query(AuditLog)


    if actor_id:
        query = query.filter(
            AuditLog.actor_id == actor_id
        )


    if entity_type:
        query = query.filter(
            AuditLog.entity_type == entity_type
        )


    if entity_id:
        query = query.filter(
            AuditLog.entity_id == entity_id
        )


    if action:
        query = query.filter(
            AuditLog.action == action
        )


    if since:
        query = query.filter(
            AuditLog.created_at >= since
        )


    results = query.order_by(
        AuditLog.created_at.desc()
    ).limit(limit).all()


    record_audit(
        db=db,
        user=user,
        action=AuditAction.READ,
        entity_type="audit_log",
        detail="Viewed audit logs"
    )


    return results


@router.get(
    "/entity/{entity_type}/{entity_id}",
    response_model=list[AuditLogOut]
)
def entity_history(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            "ops_lead"
        )
    )
):

    results = db.query(
        AuditLog
    ).filter(
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(
        AuditLog.created_at.asc()
    ).all()


    record_audit(
        db=db,
        user=user,
        action=AuditAction.READ,
        entity_type="audit_log",
        entity_id=entity_id,
        detail=(
            f"Viewed audit history "
            f"for {entity_type}"
        )
    )


    return results