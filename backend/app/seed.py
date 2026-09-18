from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.engagement import Poll, PollOption
from app.models.safety import VenueZone
from app.models.schedule import Session as ProgrammeSession, SessionSpeaker, Venue
from app.models.user import RoleEnum, SpeakerProfile, User, ParticipantProfile
from app.utils import hash_password

DEMO_PASSWORD = "Axis2026!"

SPEAKER_PHOTOS = [
    "/portal/images/own.avif",
    "/portal/images/room.avif",
    "/portal/images/heritage.png",
    "/portal/images/OIP.webp",
    "/portal/images/tech4girls.webp",
]


def _user(db: Session, email: str, name: str, role: RoleEnum) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        full_name=name,
        email=email,
        hashed_password=hash_password(DEMO_PASSWORD),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def _profile(db: Session, user: User, organization: str, bio: Optional[str] = None) -> None:
    existing = db.query(ParticipantProfile).filter(ParticipantProfile.user_id == user.id).first()
    if existing:
        return
    db.add(ParticipantProfile(user_id=user.id, organization=organization, bio=bio))


def _speaker(
    db: Session,
    user: User,
    title: str,
    organization: str,
    bio: str,
    expertise: str,
    photo_url: str,
) -> SpeakerProfile:
    profile = db.query(SpeakerProfile).filter(SpeakerProfile.user_id == user.id).first()
    if profile:
        if not profile.photo_url:
            profile.photo_url = photo_url
        return profile
    profile = SpeakerProfile(
        user_id=user.id,
        title=title,
        organization=organization,
        bio=bio,
        expertise=expertise,
        photo_url=photo_url,
    )
    db.add(profile)
    db.flush()
    return profile


def seed_demo(db: Session) -> None:
    organiser = _user(db, "organiser@hacsa.org", "Kofi Agyeman", RoleEnum.organiser)
    speaker = _user(db, "speaker@hacsa.org", "Dr. Adjoa Asamoah", RoleEnum.speaker)
    attendee = _user(db, "attendee@hacsa.org", "Ama Mensah", RoleEnum.participant)
    ops = _user(db, "ops@hacsa.org", "Nana Boateng", RoleEnum.ops_lead)
    peter = _user(db, "peter@hacsa.org", "Peter Akwaboah", RoleEnum.speaker)
    tonye = _user(db, "tonye@hacsa.org", "Tonye Cole", RoleEnum.speaker)
    nanaaba = _user(db, "nanaaba@hacsa.org", "Nana Aba Anamoah", RoleEnum.speaker)
    yaw = _user(db, "yaw@hacsa.org", "Yaw Boateng", RoleEnum.participant)

    _profile(db, organiser, "HACSA Foundation")
    _profile(db, speaker, "HACSA Foundation", "Advisor on heritage and education.")
    _profile(db, attendee, "Tech4Girls", "Builder and community organiser.")
    _profile(db, ops, "HACSA Operations")
    _profile(db, peter, "HACSA Axis", "Featured speaker.")
    _profile(db, tonye, "Sahara Group", "Energy and enterprise leader.")
    _profile(db, nanaaba, "Media", "Broadcaster and storyteller.")
    _profile(db, yaw, "HACSA Builders")

    speakers = [
        _speaker(
            db,
            speaker,
            "Policy strategist",
            "HACSA Foundation",
            "Advisor on heritage, education and social impact.",
            "Policy, education, heritage",
            SPEAKER_PHOTOS[0],
        ),
        _speaker(
            db,
            peter,
            "Featured speaker",
            "HACSA Axis",
            "Opens the programme and welcomes the community.",
            "Leadership, culture",
            SPEAKER_PHOTOS[1],
        ),
        _speaker(
            db,
            tonye,
            "Co-founder, Sahara Group",
            "Sahara Group",
            "Enterprise leadership across Africa.",
            "Business, energy",
            SPEAKER_PHOTOS[2],
        ),
        _speaker(
            db,
            nanaaba,
            "Media personality & broadcaster",
            "HACSA Axis",
            "Storytelling for culture and public conversation.",
            "Media, culture",
            SPEAKER_PHOTOS[3],
        ),
    ]

    if not db.query(Venue).first():
        venues = [
            Venue(name="Main Auditorium", location="HACSA Innovation Hub", capacity=400),
            Venue(name="Innovation Lab", location="HACSA Campus", capacity=180),
            Venue(name="Heritage Hall", location="HACSA Campus", capacity=220),
            Venue(name="Main Entrance", location="Gate 1", capacity=300),
        ]
        db.add_all(venues)
        db.flush()
    else:
        venues = db.query(Venue).order_by(Venue.id).all()

    if not db.query(ProgrammeSession).first():
        start = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
        sessions = [
            ProgrammeSession(
                title="Opening Ceremony & Welcome",
                description="Kick-off for the HACSA Axis programme.",
                venue_id=venues[0].id,
                start_time=start,
                end_time=start + timedelta(hours=1),
                capacity=400,
            ),
            ProgrammeSession(
                title="Women and Girls in Technology",
                description="Workshop on building with purpose.",
                venue_id=venues[1].id if len(venues) > 1 else venues[0].id,
                start_time=start + timedelta(hours=2),
                end_time=start + timedelta(hours=4),
                capacity=120,
            ),
            ProgrammeSession(
                title="Sankofa Dialogue: Reclaiming Our Narratives",
                description="A conversation on heritage and future-making.",
                venue_id=venues[2].id if len(venues) > 2 else venues[0].id,
                start_time=start + timedelta(days=1, hours=2),
                end_time=start + timedelta(days=1, hours=3),
                capacity=200,
            ),
        ]
        db.add_all(sessions)
        db.flush()
    else:
        sessions = db.query(ProgrammeSession).order_by(ProgrammeSession.start_time).all()

    for index, profile in enumerate(speakers):
        session = sessions[index % len(sessions)]
        exists = (
            db.query(SessionSpeaker)
            .filter(
                SessionSpeaker.session_id == session.id,
                SessionSpeaker.speaker_id == profile.id,
            )
            .first()
        )
        if not exists:
            db.add(SessionSpeaker(session_id=session.id, speaker_id=profile.id))

    if not db.query(Poll).first() and sessions:
        poll = Poll(
            session_id=sessions[0].id,
            question="What should shape the next decade?",
            created_by=organiser.id,
        )
        db.add(poll)
        db.flush()
        db.add_all(
            [
                PollOption(poll_id=poll.id, option_text="Education and skills"),
                PollOption(poll_id=poll.id, option_text="Heritage preservation"),
                PollOption(poll_id=poll.id, option_text="Women and girls in technology"),
                PollOption(poll_id=poll.id, option_text="Diaspora collaboration"),
            ]
        )

    event_id = settings.DEFAULT_EVENT_ID
    if not db.query(VenueZone).filter(VenueZone.event_id == event_id).first():
        db.add_all(
            [
                VenueZone(event_id=event_id, zone_name="Main Entrance", current_count=75, capacity=300),
                VenueZone(event_id=event_id, zone_name="Exhibition Hall", current_count=210, capacity=300),
                VenueZone(event_id=event_id, zone_name="VIP Lounge", current_count=52, capacity=100),
                VenueZone(event_id=event_id, zone_name="Loading Bay", current_count=68, capacity=150),
            ]
        )

    db.commit()
    _ = attendee
    _ = yaw


def seed_if_empty(db: Session) -> None:
    seed_demo(db)
