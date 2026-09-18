from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.connections import get_db
from app.schemas.user import (
    ParticipantProfileOut,
    ParticipantProfileUpdate,
    SpeakerProfileOut,
    SpeakerProfileUpdate,
)
from app.services import (
    get_participant_profile,
    update_participant_profile,
    get_speaker_profile,
    update_speaker_profile,
    get_speaker_profile_by_code,
    list_speaker_profiles,
)
from app.utils import require_roles
from app.models.user import User, RoleEnum

router = APIRouter(tags=["Participant & Speaker Profiles"])


@router.get("/participants/me", response_model=ParticipantProfileOut)
def read_my_participant_profile(
    current_user: User = Depends(require_roles(RoleEnum.participant)),
    db: DBSession = Depends(get_db),
):
    profile = get_participant_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Participant profile not found")
    return profile


@router.put("/participants/me", response_model=ParticipantProfileOut)
def edit_my_participant_profile(
    data: ParticipantProfileUpdate,
    current_user: User = Depends(require_roles(RoleEnum.participant)),
    db: DBSession = Depends(get_db),
):
    return update_participant_profile(db, current_user.id, data)


# Static paths ("/speakers", "/speakers/me") are registered before the
# parameterized "/speakers/{speaker_code}" so they aren't swallowed by it.

@router.get("/speakers", response_model=List[SpeakerProfileOut])
def list_speakers(db: DBSession = Depends(get_db)):
    """Public speaker directory."""
    return list_speaker_profiles(db)


@router.get("/speakers/me", response_model=SpeakerProfileOut)
def read_my_speaker_profile(
    current_user: User = Depends(require_roles(RoleEnum.speaker)),
    db: DBSession = Depends(get_db),
):
    profile = get_speaker_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Speaker profile not found")
    return profile


@router.put("/speakers/me", response_model=SpeakerProfileOut)
def edit_my_speaker_profile(
    data: SpeakerProfileUpdate,
    current_user: User = Depends(require_roles(RoleEnum.speaker)),
    db: DBSession = Depends(get_db),
):
    return update_speaker_profile(db, current_user.id, data)


@router.get("/speakers/{speaker_code}", response_model=SpeakerProfileOut)
def read_speaker_by_code(speaker_code: str, db: DBSession = Depends(get_db)):
    """Look a speaker up by their unique speaker ID."""
    profile = get_speaker_profile_by_code(db, speaker_code)
    if not profile:
        raise HTTPException(status_code=404, detail="No speaker found for this ID")
    return profile

