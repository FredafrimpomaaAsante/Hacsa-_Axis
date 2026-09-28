import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.config import settings
from app.connections import get_db
from app.models.audit import AuditLog
from app.models.enums import AuditAction
from app.models.user import User, RoleEnum
from app.schemas.user import (
    UserCreate,
    UserOut,
    UserLogin,
    Token,
    SpeakerProfileCreate,
    SpeakerProfileOut,
    SpeakerLink,
)
from app.services import (
    get_user_by_email,
    create_user,
    link_speaker_profile,
    create_unclaimed_speaker_profile,
)
from app.utils import (
    verify_password,
    create_access_token,
    get_current_user,
    require_roles,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Roles"])


def _record_auth_activity(db: DBSession, user: User, action: AuditAction, detail: str):
    try:
        db.add(AuditLog(
            actor_id=str(user.id),
            actor_role=user.role.value,
            action=action,
            entity_type="authentication",
            entity_id=str(user.id),
            detail=detail,
        ))
        db.commit()
    except Exception:
        db.rollback()


def _token_for(user: User) -> Token:
    access_token = create_access_token(
        data={
            "sub": user.person_id,
            "person_id": user.person_id,
            "role": user.role.value,
        }
    )
    return Token(access_token=access_token, user=user)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: DBSession = Depends(get_db)):
    self_service_roles = {RoleEnum.participant, RoleEnum.speaker, RoleEnum.vendor}
    if user_in.role == RoleEnum.organiser:
        invitation_code = settings.ORGANISER_SIGNUP_CODE
        if not invitation_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organiser sign-up is currently disabled. Contact HACSA for an invitation code.",
            )
        if not user_in.organiser_code or not secrets.compare_digest(
            user_in.organiser_code, invitation_code
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid organiser invitation code",
            )
    elif user_in.role not in self_service_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account type must be provisioned by HACSA",
        )

    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        user = create_user(db, user_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _record_auth_activity(
        db,
        user,
        AuditAction.CREATE,
        f"{user.full_name} registered as {user.role.value}",
    )
    return _token_for(user)


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: DBSession = Depends(get_db)):
    user = get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    _record_auth_activity(
        db,
        user,
        AuditAction.READ,
        f"{user.full_name} signed in",
    )
    return _token_for(user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post(
    "/speakers",
    response_model=SpeakerProfileOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RoleEnum.organiser))],
)
def issue_speaker_id(
    data: SpeakerProfileCreate,
    db: DBSession = Depends(get_db),
):
    profile = create_unclaimed_speaker_profile(db, data)
    payload = SpeakerProfileOut.model_validate(profile)
    payload.full_name = data.full_name or profile.title
    return payload


@router.post("/link-speaker", response_model=UserOut)
def link_speaker(
    data: SpeakerLink,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    try:
        return link_speaker_profile(db, current_user, data.speaker_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
