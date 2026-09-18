from datetime import datetime, timezone

from fastapi import HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import UserCreate
from app.services.audit import write_audit


def register_user(db: Session, payload: UserCreate) -> User:
    if payload.role == UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin accounts cannot be self-registered")
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
        organization_name=payload.organization_name,
        business_name=payload.business_name,
    )
    db.add(user)
    db.flush()
    write_audit(db, actor=user, action="register", entity_type="user", entity_id=user.id)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
    return user


def issue_tokens(user: User) -> dict[str, str]:
    return {
        "access_token": create_token(str(user.id), user.role.value, "access"),
        "refresh_token": create_token(str(user.id), user.role.value, "refresh"),
        "token_type": "bearer",
    }


def refresh_tokens(db: Session, refresh_token: str) -> dict[str, str]:
    try:
        payload = decode_token(refresh_token)
        if payload.get("typ") != "refresh":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token required")
        user = db.get(User, int(payload["sub"]))
    except (InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token") from None
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    return issue_tokens(user)


def ensure_admin_exists(db: Session, email: str, password: str) -> None:
    existing = db.scalar(select(User).where(User.email == email.lower()))
    if existing:
        return
    db.add(
        User(
            email=email.lower(),
            hashed_password=hash_password(password),
            full_name="Platform Administrator",
            role=UserRole.ADMIN,
            is_active=True,
        )
    )
    db.flush()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
