from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.connections import get_db
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

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: DBSession = Depends(get_db)):
    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        return create_user(db, user_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: DBSession = Depends(get_db)):
    """Exchange email + password for a JWT that encodes the user's role."""
    user = get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(
    data={
        "sub": user.person_id,
        "person_id": user.person_id,
        "role": user.role.value,
    }
)

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
    return create_unclaimed_speaker_profile(db, data)

@router.post("/link-speaker", response_model=UserOut)
def link_speaker(
    data: SpeakerLink,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    try:
        return link_speaker_profile(
            db,
            current_user,
            data.speaker_code,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc