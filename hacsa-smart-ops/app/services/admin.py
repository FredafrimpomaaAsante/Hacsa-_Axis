from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import VendorApplication
from app.models.audit import AuditLog
from app.models.event import Event
from app.models.payment import Payment
from app.models.user import User
from app.schemas.admin import UserAdminUpdate
from app.services.audit import write_audit


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


def update_user(db: Session, admin: User, user_id: int, payload: UserAdminUpdate) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.id == admin.id and payload.is_active is False:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Administrators cannot disable themselves")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.flush()
    write_audit(db, actor=admin, action="update_user", entity_type="user", entity_id=user.id)
    return user


def list_audit_logs(db: Session, limit: int = 100) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)))


def platform_stats(db: Session) -> dict:
    return {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "events": db.scalar(select(func.count()).select_from(Event)) or 0,
        "applications": db.scalar(select(func.count()).select_from(VendorApplication)) or 0,
        "payments": db.scalar(select(func.count()).select_from(Payment)) or 0,
    }
