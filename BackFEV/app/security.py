from typing import Optional

from fastapi import (
    Depends,
    HTTPException,
    status,
    Request
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from jose import jwt, JWTError

from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.config import settings
from app.models.audit import AuditLog
from app.models.enums import AuditAction


bearer_scheme = HTTPBearer()


OPS_ROLES = (
    "staff",
    "organiser",
    "safety_officer",
    "ops_lead"
)


class CurrentUser(BaseModel):
    id: str
    role: str
    ip: Optional[str] = None


def decode_token(
    token: str
) -> CurrentUser:

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[
                settings.JWT_ALGORITHM
            ]
        )

    except JWTError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


    user_id = payload.get("sub")
    role = payload.get("role")


    if user_id is None or role is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Token missing required claims "
                "(sub, role)"
            )
        )


    return CurrentUser(
        id=user_id,
        role=role
    )


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    )
) -> CurrentUser:

    user = decode_token(
        credentials.credentials
    )


    user.ip = (
        request.client.host
        if request.client
        else None
    )


    return user


def require_roles(
    *allowed_roles: str
):

    def dependency(
        user: CurrentUser = Depends(
            get_current_user
        )
    ) -> CurrentUser:

        if user.role not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{user.role}' "
                    "is not permitted to perform "
                    "this action"
                )
            )

        return user


    return dependency


def record_audit(
    db: Session,
    user: CurrentUser,
    action: AuditAction,
    entity_type: str,
    entity_id: Optional[str] = None,
    detail: Optional[str] = None,
    commit: bool = True
) -> None:

    try:

        db.add(
            AuditLog(
                actor_id=user.id,
                actor_role=user.role,
                action=action,
                entity_type=entity_type,
                entity_id=(
                    str(entity_id)
                    if entity_id is not None
                    else None
                ),
                detail=detail,
                ip_address=user.ip
            )
        )


        if commit:
            db.commit()


    except Exception as exc:

        db.rollback()

        import logging

        logging.getLogger(
            "security"
        ).error(
            "Audit write failed: %s",
            exc
        )