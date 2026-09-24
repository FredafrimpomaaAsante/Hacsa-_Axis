from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.attendance import CheckIn, ScanRejection
from app.models.engagement import Poll, PollOption
from app.models.enums import (
    AlertLevel,
    AlertType,
    CheckInMethod,
    IncidentSeverity,
    IncidentStatus,
)
from app.models.safety import Incident, OccupancyReading, ResponseAssignment, SafetyAlert, VenueZone
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
    _seed_live_ops(db, event_id, ops)

    db.commit()
    _ = attendee
    _ = yaw


def _seed_live_ops(db: Session, event_id: str, ops: User) -> None:
    staff = [
        _user(db, "achen@hacsa.org", "A. Chen", RoleEnum.staff),
        _user(db, "mpatel@hacsa.org", "M. Patel", RoleEnum.safety_officer),
        _user(db, "dbrooks@hacsa.org", "D. Brooks", RoleEnum.staff),
        _user(db, "nsingh@hacsa.org", "N. Singh", RoleEnum.staff),
    ]
    _profile(db, staff[0], "HACSA Gate team")
    _profile(db, staff[1], "HACSA Safety")
    _profile(db, staff[2], "HACSA Floor team")
    _profile(db, staff[3], "HACSA Medical")

    guests = [
        _user(db, "efua@hacsa.org", "Efua Boateng", RoleEnum.participant),
        _user(db, "kwame@hacsa.org", "Kwame Mensah", RoleEnum.participant),
        _user(db, "akosua@hacsa.org", "Akosua Darko", RoleEnum.participant),
        _user(db, "selorm@hacsa.org", "Selorm Tetteh", RoleEnum.participant),
        _user(db, "esther@hacsa.org", "Esther Owusu", RoleEnum.participant),
        _user(db, "michael@hacsa.org", "Michael Addo", RoleEnum.participant),
        _user(db, "joyce@hacsa.org", "Joyce Nkrumah", RoleEnum.participant),
        _user(db, "daniel@hacsa.org", "Daniel Quaye", RoleEnum.participant),
        _user(db, "lina@hacsa.org", "Lina Appiah", RoleEnum.participant),
        _user(db, "isaac@hacsa.org", "Isaac Forson", RoleEnum.participant),
    ]
    for guest in guests:
        _profile(db, guest, "HACSA Axis guest")

    zone_counts = {
        "Main Entrance": (118, 300),
        "Exhibition Hall": (262, 300),
        "VIP Lounge": (61, 100),
        "Loading Bay": (44, 150),
    }
    for name, (count, capacity) in zone_counts.items():
        zone = db.query(VenueZone).filter(VenueZone.event_id == event_id, VenueZone.zone_name == name).first()
        if zone:
            zone.current_count = count
            zone.capacity = capacity
        else:
            zone = VenueZone(event_id=event_id, zone_name=name, current_count=count, capacity=capacity)
            db.add(zone)
        db.flush()
        if not db.query(OccupancyReading).filter(OccupancyReading.event_id == event_id, OccupancyReading.zone_name == name).first():
            now = datetime.utcnow()
            db.add_all(
                [
                    OccupancyReading(
                        event_id=event_id,
                        zone_name=name,
                        current_count=max(20, count - 40),
                        capacity=capacity,
                        recorded_by=str(ops.id),
                        recorded_at=now - timedelta(hours=3),
                    ),
                    OccupancyReading(
                        event_id=event_id,
                        zone_name=name,
                        current_count=count,
                        capacity=capacity,
                        recorded_by=str(ops.id),
                        recorded_at=now - timedelta(minutes=12),
                    ),
                ]
            )

    people = db.query(User).filter(User.role.in_([RoleEnum.participant, RoleEnum.speaker])).all()
    now = datetime.utcnow()
    for index, person in enumerate(people):
        if person.email in {"lina@hacsa.org", "isaac@hacsa.org", "daniel@hacsa.org"}:
            continue
        exists = (
            db.query(CheckIn)
            .filter(CheckIn.event_id == event_id, CheckIn.participant_id == person.person_id)
            .first()
        )
        if exists:
            continue
        db.add(
            CheckIn(
                event_id=event_id,
                participant_id=person.person_id,
                pass_code=f"PASS-{person.id:04d}",
                method=CheckInMethod.MANUAL if index % 4 == 0 else CheckInMethod.QR_SCAN,
                scanned_by=str(staff[index % len(staff)].id),
                checked_in_at=now - timedelta(hours=5 - (index % 6), minutes=8 * (index % 5)),
            )
        )

    leftover = db.query(User).filter(User.role == RoleEnum.participant).order_by(User.id.desc()).first()
    if leftover and not db.query(ScanRejection).filter(ScanRejection.event_id == event_id).first():
        db.add(
            ScanRejection(
                event_id=event_id,
                pass_code="PASS-EXPIRED",
                reason="Pass already used at Main Entrance",
                scanned_by=str(staff[0].id),
                occurred_at=now - timedelta(minutes=40),
            )
        )

    incident_specs = [
        {
            "location": "Main Entrance",
            "description": "Queue overflow at Gate 3: Backup forming on the approach lane.",
            "severity": IncidentSeverity.MEDIUM,
            "status": IncidentStatus.IN_PROGRESS,
            "created_at": now - timedelta(hours=2),
            "acknowledged_at": now - timedelta(hours=1, minutes=50),
            "responder": staff[0],
        },
        {
            "location": "Exhibition Hall",
            "description": "Medical assist: Guest feeling faint near booth 12.",
            "severity": IncidentSeverity.HIGH,
            "status": IncidentStatus.ASSIGNED,
            "created_at": now - timedelta(minutes=35),
            "acknowledged_at": now - timedelta(minutes=30),
            "responder": staff[3],
        },
        {
            "location": "VIP Lounge",
            "description": "Access control: Unscanned guest at the lounge door.",
            "severity": IncidentSeverity.LOW,
            "status": IncidentStatus.OPEN,
            "created_at": now - timedelta(minutes=18),
            "acknowledged_at": None,
            "responder": None,
        },
        {
            "location": "Loading Bay",
            "description": "Facility issue: Temporary cable cover placed on wet floor.",
            "severity": IncidentSeverity.LOW,
            "status": IncidentStatus.RESOLVED,
            "created_at": now - timedelta(hours=4),
            "acknowledged_at": now - timedelta(hours=3, minutes=50),
            "resolved_at": now - timedelta(hours=3, minutes=20),
            "responder": staff[2],
        },
        {
            "location": "Exhibition Hall",
            "description": "Crowd density watch: East aisle approaching comfort limit.",
            "severity": IncidentSeverity.CRITICAL,
            "status": IncidentStatus.OPEN,
            "created_at": now - timedelta(minutes=9),
            "acknowledged_at": None,
            "responder": None,
        },
    ]
    for spec in incident_specs:
        exists = db.query(Incident).filter(Incident.event_id == event_id, Incident.description == spec["description"]).first()
        if exists:
            incident = exists
        else:
            incident = Incident(
                event_id=event_id,
                reported_by=str(ops.id),
                location=spec["location"],
                description=spec["description"],
                severity=spec["severity"],
                status=spec["status"],
                created_at=spec["created_at"],
                acknowledged_at=spec.get("acknowledged_at"),
                resolved_at=spec.get("resolved_at"),
            )
            db.add(incident)
            db.flush()
        if spec.get("responder") and not db.query(ResponseAssignment).filter(ResponseAssignment.incident_id == incident.id).first():
            db.add(
                ResponseAssignment(
                    incident_id=incident.id,
                    responder_id=str(spec["responder"].id),
                    assigned_by=str(ops.id),
                    notes="Seeded floor assignment",
                    status=IncidentStatus.ASSIGNED if spec["status"] == IncidentStatus.OPEN else spec["status"],
                )
            )

    alert_specs = [
        {
            "alert_type": AlertType.CROWD,
            "level": AlertLevel.ELEVATED,
            "zone_name": "Exhibition Hall",
            "message": "High occupancy in Exhibition Hall: 262/300",
        },
        {
            "alert_type": AlertType.MEDICAL,
            "level": AlertLevel.CRITICAL,
            "zone_name": "Exhibition Hall",
            "message": "Medical team requested at booth 12.",
        },
        {
            "alert_type": AlertType.INCIDENT,
            "level": AlertLevel.INFO,
            "zone_name": "Main Entrance",
            "message": "Queue lane at Gate 3 under watch.",
        },
    ]
    for spec in alert_specs:
        exists = (
            db.query(SafetyAlert)
            .filter(SafetyAlert.event_id == event_id, SafetyAlert.message == spec["message"])
            .first()
        )
        if exists:
            continue
        db.add(
            SafetyAlert(
                event_id=event_id,
                alert_type=spec["alert_type"],
                level=spec["level"],
                zone_name=spec["zone_name"],
                message=spec["message"],
                created_by=str(ops.id),
                created_at=now - timedelta(minutes=14),
            )
        )


def seed_if_empty(db: Session) -> None:
    seed_demo(db)
