from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session as DBSession

from app.models.user import User, ParticipantProfile, SpeakerProfile, RoleEnum, generate_speaker_code
from app.models.schedule import Venue, Session, SessionSpeaker, SessionInterest, SessionStatusEnum
from app.models.notification import Notification
from app.models.networking import NetworkConnection, ConnectionStatusEnum
from app.models.engagement import Poll, PollOption, PollVote, Question, QuestionUpvote, Feedback
from app.schemas.user import (
    UserCreate,
    ParticipantProfileUpdate,
    SpeakerProfileUpdate,
    SpeakerProfileCreate,
)
from app.schemas.schedule import VenueCreate, SessionCreate, SessionUpdate
from app.schemas.engagement import PollCreate

from app.utils import hash_password



# User, role identification & profile services

def get_user_by_email(db: DBSession, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: DBSession, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def list_users(db: DBSession, exclude_user_id: Optional[int] = None) -> List[User]:
    query = db.query(User)
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)
    return query.all()


def create_user(db: DBSession, user_in: UserCreate) -> User:
    speaker_profile = None

    if user_in.speaker_code:
        speaker_profile = get_speaker_profile_by_code(
            db, user_in.speaker_code
        )

        if speaker_profile is None:
            raise ValueError("Invalid speaker ID")

        if speaker_profile.user_id is not None:
            raise ValueError("Speaker ID has already been claimed")

    user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=RoleEnum.speaker if speaker_profile else RoleEnum.participant,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Every account remains a participant.
    db.add(ParticipantProfile(user_id=user.id))

    if speaker_profile:
        speaker_profile.user_id = user.id

    db.commit()
    return user

def get_participant_profile(db: DBSession, user_id: int) -> Optional[ParticipantProfile]:
    return db.query(ParticipantProfile).filter(ParticipantProfile.user_id == user_id).first()


def update_participant_profile(
    db: DBSession, user_id: int, data: ParticipantProfileUpdate
) -> ParticipantProfile:
    profile = get_participant_profile(db, user_id)
    if profile is None:
        profile = ParticipantProfile(user_id=user_id)
        db.add(profile)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


def get_speaker_profile(db: DBSession, user_id: int) -> Optional[SpeakerProfile]:
    return db.query(SpeakerProfile).filter(SpeakerProfile.user_id == user_id).first()


def get_speaker_profile_by_code(db: DBSession, speaker_code: str) -> Optional[SpeakerProfile]:
    return db.query(SpeakerProfile).filter(SpeakerProfile.speaker_code == speaker_code).first()


def list_speaker_profiles(db: DBSession) -> List[SpeakerProfile]:
    return db.query(SpeakerProfile).all()


def update_speaker_profile(
    db: DBSession, user_id: int, data: SpeakerProfileUpdate
) -> SpeakerProfile:
    profile = get_speaker_profile(db, user_id)
    if profile is None:
        profile = SpeakerProfile(user_id=user_id, speaker_code=generate_speaker_code())
        db.add(profile)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile



# Venue, session & speaker-assignment services


def get_venues(db: DBSession) -> List[Venue]:
    return db.query(Venue).all()


def get_venue(db: DBSession, venue_id: int) -> Optional[Venue]:
    return db.query(Venue).filter(Venue.id == venue_id).first()


def create_venue(db: DBSession, data: VenueCreate) -> Venue:
    venue = Venue(**data.model_dump())
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


def get_sessions(db: DBSession) -> List[Session]:
    return db.query(Session).order_by(Session.start_time).all()


def get_session(db: DBSession, session_id: int) -> Optional[Session]:
    return db.query(Session).filter(Session.id == session_id).first()


def create_session(db: DBSession, data: SessionCreate) -> Session:
    session = Session(**data.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_session(db: DBSession, session: Session, data: SessionUpdate) -> Session:
    """Updates a session and, if the time/venue/status actually changed,
    fires schedule-change notifications to assigned speakers + interested
    participants."""
    changes = data.model_dump(exclude_unset=True)
    tracked_fields = {"start_time", "end_time", "venue_id", "status"}
    schedule_changed = any(
        field in changes and getattr(session, field) != changes[field]
        for field in tracked_fields
    )

    for field, value in changes.items():
        setattr(session, field, value)

    db.commit()
    db.refresh(session)

    if schedule_changed:
        notify_schedule_change(db, session)

    return session


def assign_speaker_to_session(db: DBSession, session_id: int, speaker_id: int) -> SessionSpeaker:
    existing = (
        db.query(SessionSpeaker)
        .filter(SessionSpeaker.session_id == session_id, SessionSpeaker.speaker_id == speaker_id)
        .first()
    )
    if existing:
        return existing

    assignment = SessionSpeaker(session_id=session_id, speaker_id=speaker_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def get_speakers_for_session(db: DBSession, session_id: int) -> List[SessionSpeaker]:
    return db.query(SessionSpeaker).filter(SessionSpeaker.session_id == session_id).all()


def get_sessions_for_speaker(db: DBSession, speaker_id: int) -> List[Session]:
    return (
        db.query(Session)
        .join(SessionSpeaker, SessionSpeaker.session_id == Session.id)
        .filter(SessionSpeaker.speaker_id == speaker_id)
        .all()
    )


def mark_interest_in_session(db: DBSession, session_id: int, user_id: int) -> SessionInterest:
    existing = (
        db.query(SessionInterest)
        .filter(SessionInterest.session_id == session_id, SessionInterest.user_id == user_id)
        .first()
    )
    if existing:
        return existing

    interest = SessionInterest(session_id=session_id, user_id=user_id)
    db.add(interest)
    db.commit()
    db.refresh(interest)
    return interest


def get_interests_for_user(db: DBSession, user_id: int) -> List[SessionInterest]:
    return db.query(SessionInterest).filter(SessionInterest.user_id == user_id).all()



# Notification services


def create_notification(
    db: DBSession,
    user_id: int,
    title: str,
    message: str,
    related_session_id: Optional[int] = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        related_session_id=related_session_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def notify_schedule_change(db: DBSession, session: Session) -> None:
    """Builds the notification text from the session's current data (never a
    fixed string) and sends it to every assigned speaker and every
    participant who marked interest in this session."""
    if session.status == SessionStatusEnum.cancelled:
        title = "Session cancelled"
        message = f'"{session.title}" has been cancelled.'
    else:
        title = "Session schedule updated"
        message = (
            f'"{session.title}" has been updated — now scheduled '
            f"{session.start_time.strftime('%Y-%m-%d %H:%M')} to "
            f"{session.end_time.strftime('%H:%M')}."
        )

    recipient_ids = set()

    for link in get_speakers_for_session(db, session.id):
        speaker_profile = db.query(SpeakerProfile).filter(SpeakerProfile.id == link.speaker_id).first()
        if speaker_profile:
            recipient_ids.add(speaker_profile.user_id)

    for interest in db.query(SessionInterest).filter(SessionInterest.session_id == session.id).all():
        recipient_ids.add(interest.user_id)

    for recipient_id in recipient_ids:
        create_notification(
            db, user_id=recipient_id, title=title, message=message, related_session_id=session.id
        )


def get_notifications_for_user(
    db: DBSession, user_id: int, unread_only: bool = False
) -> List[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return query.order_by(Notification.created_at.desc()).all()


def mark_notification_read(db: DBSession, notification: Notification) -> Notification:
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


# ---------------------------------------------------------------------------
# Networking services
# ---------------------------------------------------------------------------

def send_connection_request(db: DBSession, requester_id: int, recipient_id: int) -> NetworkConnection:
    existing = (
        db.query(NetworkConnection)
        .filter(
            NetworkConnection.requester_id == requester_id,
            NetworkConnection.recipient_id == recipient_id,
        )
        .first()
    )
    if existing:
        return existing

    connection = NetworkConnection(requester_id=requester_id, recipient_id=recipient_id)
    db.add(connection)
    db.commit()
    db.refresh(connection)

    create_notification(
        db,
        user_id=recipient_id,
        title="New connection request",
        message="Someone would like to connect with you.",
    )
    return connection


def respond_to_connection(db: DBSession, connection: NetworkConnection, accept: bool) -> NetworkConnection:
    connection.status = ConnectionStatusEnum.accepted if accept else ConnectionStatusEnum.declined
    connection.responded_at = datetime.utcnow()
    db.commit()
    db.refresh(connection)

    if accept:
        create_notification(
            db,
            user_id=connection.requester_id,
            title="Connection accepted",
            message="Your connection request was accepted.",
        )
    return connection


def get_connection_by_id(db: DBSession, connection_id: int) -> Optional[NetworkConnection]:
    return db.query(NetworkConnection).filter(NetworkConnection.id == connection_id).first()


def get_connections_for_user(
    db: DBSession, user_id: int, status: Optional[ConnectionStatusEnum] = None
) -> List[NetworkConnection]:
    query = db.query(NetworkConnection).filter(
        (NetworkConnection.requester_id == user_id) | (NetworkConnection.recipient_id == user_id)
    )
    if status is not None:
        query = query.filter(NetworkConnection.status == status)
    return query.order_by(NetworkConnection.created_at.desc()).all()


# ---------------------------------------------------------------------------
# Engagement services — polls, Q&A, feedback
# ---------------------------------------------------------------------------

def create_poll(db: DBSession, data: PollCreate, created_by: int) -> Poll:
    poll = Poll(session_id=data.session_id, question=data.question, created_by=created_by)
    db.add(poll)
    db.commit()
    db.refresh(poll)

    for option in data.options:
        db.add(PollOption(poll_id=poll.id, option_text=option.option_text))
    db.commit()
    db.refresh(poll)
    return poll


def get_poll(db: DBSession, poll_id: int) -> Optional[Poll]:
    return db.query(Poll).filter(Poll.id == poll_id).first()


def list_polls(db: DBSession, session_id: Optional[int] = None) -> List[Poll]:
    query = db.query(Poll)
    if session_id is not None:
        query = query.filter(Poll.session_id == session_id)
    return query.order_by(Poll.created_at.desc()).all()


def cast_poll_vote(db: DBSession, poll_id: int, poll_option_id: int, user_id: int) -> PollVote:
    existing = (
        db.query(PollVote)
        .filter(PollVote.poll_id == poll_id, PollVote.user_id == user_id)
        .first()
    )
    if existing:
        return existing

    vote = PollVote(poll_id=poll_id, poll_option_id=poll_option_id, user_id=user_id)
    db.add(vote)
    db.commit()
    db.refresh(vote)
    return vote


def get_poll_results(db: DBSession, poll: Poll) -> dict:
    results = []
    total_votes = 0
    for option in poll.options:
        vote_count = db.query(PollVote).filter(PollVote.poll_option_id == option.id).count()
        total_votes += vote_count
        results.append(
            {"option_id": option.id, "option_text": option.option_text, "vote_count": vote_count}
        )

    return {
        "poll_id": poll.id,
        "question": poll.question,
        "total_votes": total_votes,
        "results": results,
    }


def _question_to_dict(question: Question) -> dict:
    return {
        "id": question.id,
        "session_id": question.session_id,
        "user_id": question.user_id,
        "question_text": question.question_text,
        "is_answered": question.is_answered,
        "created_at": question.created_at,
        "upvote_count": len(question.upvotes),
    }


def create_question(db: DBSession, session_id: int, user_id: int, question_text: str) -> dict:
    question = Question(session_id=session_id, user_id=user_id, question_text=question_text)
    db.add(question)
    db.commit()
    db.refresh(question)
    return _question_to_dict(question)


def get_questions_for_session(db: DBSession, session_id: int) -> List[dict]:
    questions = db.query(Question).filter(Question.session_id == session_id).all()
    enriched = [_question_to_dict(q) for q in questions]
    # Most upvoted first, then newest first (stable two-pass sort).
    enriched.sort(key=lambda q: q["created_at"], reverse=True)
    enriched.sort(key=lambda q: q["upvote_count"], reverse=True)
    return enriched


def get_question_by_id(db: DBSession, question_id: int) -> Optional[Question]:
    return db.query(Question).filter(Question.id == question_id).first()


def upvote_question(db: DBSession, question_id: int, user_id: int) -> QuestionUpvote:
    existing = (
        db.query(QuestionUpvote)
        .filter(QuestionUpvote.question_id == question_id, QuestionUpvote.user_id == user_id)
        .first()
    )
    if existing:
        return existing

    upvote = QuestionUpvote(question_id=question_id, user_id=user_id)
    db.add(upvote)
    db.commit()
    db.refresh(upvote)
    return upvote


def mark_question_answered(db: DBSession, question: Question) -> dict:
    question.is_answered = True
    db.commit()
    db.refresh(question)
    return _question_to_dict(question)


def submit_feedback(
    db: DBSession, session_id: int, user_id: int, rating: int, comment: Optional[str]
) -> Feedback:
    existing = (
        db.query(Feedback)
        .filter(Feedback.session_id == session_id, Feedback.user_id == user_id)
        .first()
    )
    if existing:
        existing.rating = rating
        existing.comment = comment
        db.commit()
        db.refresh(existing)
        return existing

    feedback = Feedback(session_id=session_id, user_id=user_id, rating=rating, comment=comment)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_feedback_summary(db: DBSession, session_id: int) -> dict:
    entries = db.query(Feedback).filter(Feedback.session_id == session_id).all()
    total = len(entries)
    average = round(sum(e.rating for e in entries) / total, 2) if total else 0.0
    return {"session_id": session_id, "average_rating": average, "total_responses": total}


def create_unclaimed_speaker_profile(
    db: DBSession,
    data: SpeakerProfileCreate,
) -> SpeakerProfile:
    profile = SpeakerProfile(
        speaker_code=generate_speaker_code(),
        title=data.title,
        organization=data.organization,
        bio=data.bio,
        expertise=data.expertise,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def link_speaker_profile(
    db: DBSession,
    user: User,
    speaker_code: str,
) -> User:
    profile = get_speaker_profile_by_code(db, speaker_code)

    if profile is None:
        raise ValueError("Invalid speaker ID")

    if profile.user_id is not None:
        raise ValueError("Speaker ID has already been claimed")

    if user.role == RoleEnum.organiser:
        raise ValueError("Organiser accounts cannot claim speaker IDs")

    profile.user_id = user.id
    user.role = RoleEnum.speaker

    db.commit()
    db.refresh(user)
    return user

