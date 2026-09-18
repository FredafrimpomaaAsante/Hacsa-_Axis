from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.connections import get_db
from app.schemas.schedule import (
    VenueOut,
    VenueCreate,
    SessionOut,
    SessionCreate,
    SessionUpdate,
    SpeakerAssignmentOut,
    SessionInterestOut,
)
from app.services import (
    get_venues,
    get_venue,
    create_venue,
    get_sessions,
    get_session,
    create_session,
    update_session,
    assign_speaker_to_session,
    get_speakers_for_session,
    get_sessions_for_speaker,
    mark_interest_in_session,
    get_interests_for_user,
    get_speaker_profile_by_code,
)
from app.utils import get_current_user, require_roles
from app.models.user import User, RoleEnum

router = APIRouter(tags=["Session, Venue & Schedule"])


@router.get("/venues", response_model=List[VenueOut])
def list_venues(db: DBSession = Depends(get_db)):
    return get_venues(db)


@router.get("/venues/{venue_id}", response_model=VenueOut)
def read_venue(venue_id: int, db: DBSession = Depends(get_db)):
    venue = get_venue(db, venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@router.post(
    "/venues",
    response_model=VenueOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RoleEnum.organiser))],
)
def add_venue(data: VenueCreate, db: DBSession = Depends(get_db)):
    return create_venue(db, data)


@router.get("/schedule/sessions", response_model=List[SessionOut])
def list_sessions(db: DBSession = Depends(get_db)):
    return get_sessions(db)


@router.get("/schedule/sessions/{session_id}", response_model=SessionOut)
def read_session(session_id: int, db: DBSession = Depends(get_db)):
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post(
    "/schedule/sessions",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RoleEnum.organiser))],
)
def add_session(data: SessionCreate, db: DBSession = Depends(get_db)):
    return create_session(db, data)


@router.patch(
    "/schedule/sessions/{session_id}",
    response_model=SessionOut,
    dependencies=[Depends(require_roles(RoleEnum.organiser))],
)
def edit_session(session_id: int, data: SessionUpdate, db: DBSession = Depends(get_db)):
    """Partial update — e.g. a reschedule or cancellation. If time, venue, or
    status actually change, assigned speakers and interested participants
    are notified automatically."""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return update_session(db, session, data)


@router.post(
    "/schedule/sessions/{session_id}/speakers/{speaker_code}",
    response_model=SpeakerAssignmentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RoleEnum.organiser))],
)
def assign_speaker(session_id: int, speaker_code: str, db: DBSession = Depends(get_db)):
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    speaker = get_speaker_profile_by_code(db, speaker_code)
    if not speaker:
        raise HTTPException(status_code=404, detail="No speaker found for this ID")

    return assign_speaker_to_session(db, session_id=session_id, speaker_id=speaker.id)


@router.get("/schedule/sessions/{session_id}/speakers", response_model=List[SpeakerAssignmentOut])
def list_session_speakers(session_id: int, db: DBSession = Depends(get_db)):
    return get_speakers_for_session(db, session_id)


@router.get("/speakers/{speaker_code}/sessions", response_model=List[SessionOut])
def list_speaker_sessions(speaker_code: str, db: DBSession = Depends(get_db)):
    speaker = get_speaker_profile_by_code(db, speaker_code)
    if not speaker:
        raise HTTPException(status_code=404, detail="No speaker found for this ID")
    return get_sessions_for_speaker(db, speaker.id)


@router.post(
    "/schedule/sessions/{session_id}/interest",
    response_model=SessionInterestOut,
    status_code=status.HTTP_201_CREATED,
)
def mark_interest(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """A participant follows a session, so they're notified if it's rescheduled
    or cancelled."""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return mark_interest_in_session(db, session_id=session_id, user_id=current_user.id)


@router.get("/users/me/interests", response_model=List[SessionInterestOut])
def my_interests(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return get_interests_for_user(db, current_user.id)

