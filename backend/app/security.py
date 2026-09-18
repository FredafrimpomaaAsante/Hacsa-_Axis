from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.enums import AuditAction
from app.models.user import RoleEnum, User
from app.utils import get_current_user as get_db_user

OPS_ROLES = (
    RoleEnum.organiser.value,
    RoleEnum.staff.value,
    RoleEnum.safety_officer.value,
    RoleEnum.ops_lead.value,
)


class CurrentUser(BaseModel):
    id: str
    role: str
    ip: Optional[str] = None
    db_user: Optional[User] = None

    model_config = {"arbitrary_types_allowed": True}


def get_current_user(
    request: Request,
    user: User = Depends(get_db_user),
) -> CurrentUser:
    return CurrentUser(
        id=str(user.id),
        role=user.role.value,
        ip=request.client.host if request.client else None,
        db_user=user,
    )


def require_roles(*allowed_roles: str):
    allowed = {role.value if isinstance(role, RoleEnum) else role for role in allowed_roles}

    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not permitted to perform this action",
            )
        return user

    return dependency


def record_audit(
    db: Session,
    user: CurrentUser,
    action: AuditAction,
    entity_type: str,
    entity_id=None,
    detail: Optional[str] = None,
    commit: bool = True,
) -> None:
    try:
        db.add(
            AuditLog(
                actor_id=user.id,
                actor_role=user.role,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                detail=detail,
                ip_address=user.ip,
            )
        )
        if commit:
            db.commit()
    except Exception:
        db.rollback()
