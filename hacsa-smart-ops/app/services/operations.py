from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rbac import ensure_event_owner
from app.models.enums import ApplicationStatus, AssignmentStatus, BoothStatus, EventStatus, UserRole
from app.models.application import VendorApplication
from app.models.booth import Booth, BoothAssignment
from app.models.event import Event, EventSession
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationReview
from app.schemas.booth import AssignmentCreate, BoothCreate, BoothUpdate
from app.schemas.event import EventCreate, EventUpdate, SessionCreate, SessionUpdate
from app.services.audit import write_audit
from app.services.auth import utcnow


def create_event(db: Session, organizer: User, payload: EventCreate) -> Event:
    if organizer.role == UserRole.VENDOR:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Vendors cannot create events")
    event = Event(organizer_id=organizer.id, **payload.model_dump())
    db.add(event)
    db.flush()
    write_audit(db, actor=organizer, action="create_event", entity_type="event", entity_id=event.id)
    return event


def list_events(db: Session, user: User | None, public_only: bool = False) -> list[Event]:
    stmt = select(Event)
    if public_only or user is None:
        stmt = stmt.where(Event.status.in_([EventStatus.PUBLISHED, EventStatus.LIVE]))
    elif user.role == UserRole.ORGANIZER:
        stmt = stmt.where(Event.organizer_id == user.id)
    elif user.role == UserRole.VENDOR:
        stmt = stmt.where(Event.status.in_([EventStatus.PUBLISHED, EventStatus.LIVE]))
    return list(db.scalars(stmt.order_by(Event.start_at.desc())))


def get_event(db: Session, event_id: int) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")
    return event


def update_event(db: Session, user: User, event_id: int, payload: EventUpdate) -> Event:
    event = ensure_event_owner(db.get(Event, event_id), user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, key, value)
    db.flush()
    write_audit(db, actor=user, action="update_event", entity_type="event", entity_id=event.id)
    return event


def create_session(db: Session, user: User, event_id: int, payload: SessionCreate) -> EventSession:
    event = ensure_event_owner(db.get(Event, event_id), user)
    session = EventSession(event_id=event.id, **payload.model_dump())
    db.add(session)
    db.flush()
    write_audit(db, actor=user, action="create_session", entity_type="session", entity_id=session.id)
    return session


def list_sessions(db: Session, event_id: int) -> list[EventSession]:
    get_event(db, event_id)
    return list(db.scalars(select(EventSession).where(EventSession.event_id == event_id).order_by(EventSession.start_at)))


def update_session(db: Session, user: User, session_id: int, payload: SessionUpdate) -> EventSession:
    session = db.get(EventSession, session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    ensure_event_owner(session.event, user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(session, key, value)
    db.flush()
    return session


def submit_application(db: Session, vendor: User, payload: ApplicationCreate) -> VendorApplication:
    if vendor.role not in (UserRole.VENDOR, UserRole.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only vendors can apply")
    event = get_event(db, payload.event_id)
    if event.status not in (EventStatus.PUBLISHED, EventStatus.LIVE):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Event is not accepting vendors")
    duplicate = db.scalar(
        select(VendorApplication).where(
            VendorApplication.vendor_id == vendor.id, VendorApplication.event_id == event.id
        )
    )
    if duplicate:
        raise HTTPException(status.HTTP_409_CONFLICT, "Application already exists for this event")
    application = VendorApplication(vendor_id=vendor.id, **payload.model_dump())
    db.add(application)
    db.flush()
    write_audit(db, actor=vendor, action="submit_application", entity_type="application", entity_id=application.id)
    return application


def list_applications(db: Session, user: User, event_id: int | None = None) -> list[VendorApplication]:
    stmt = select(VendorApplication)
    if user.role == UserRole.VENDOR:
        stmt = stmt.where(VendorApplication.vendor_id == user.id)
    elif user.role == UserRole.ORGANIZER:
        stmt = stmt.join(Event).where(Event.organizer_id == user.id)
    if event_id is not None:
        stmt = stmt.where(VendorApplication.event_id == event_id)
    return list(db.scalars(stmt.order_by(VendorApplication.created_at.desc())))


def review_application(db: Session, user: User, application_id: int, payload: ApplicationReview) -> VendorApplication:
    application = db.get(VendorApplication, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    ensure_event_owner(application.event, user)
    if payload.status not in (ApplicationStatus.UNDER_REVIEW, ApplicationStatus.APPROVED, ApplicationStatus.REJECTED):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid review status")
    application.status = payload.status
    application.review_notes = payload.review_notes
    application.reviewed_by_id = user.id
    application.reviewed_at = utcnow()
    db.flush()
    if payload.status == ApplicationStatus.APPROVED and payload.booth_id is not None:
        assign_booth(
            db,
            user,
            AssignmentCreate(booth_id=payload.booth_id, vendor_id=application.vendor_id, application_id=application.id),
        )
    write_audit(db, actor=user, action="review_application", entity_type="application", entity_id=application.id)
    return application


def create_booth(db: Session, user: User, event_id: int, payload: BoothCreate) -> Booth:
    event = ensure_event_owner(db.get(Event, event_id), user)
    booth = Booth(event_id=event.id, **payload.model_dump())
    db.add(booth)
    db.flush()
    write_audit(db, actor=user, action="create_booth", entity_type="booth", entity_id=booth.id)
    return booth


def list_booths(db: Session, event_id: int) -> list[Booth]:
    get_event(db, event_id)
    return list(db.scalars(select(Booth).where(Booth.event_id == event_id).order_by(Booth.code)))


def update_booth(db: Session, user: User, booth_id: int, payload: BoothUpdate) -> Booth:
    booth = db.get(Booth, booth_id)
    if booth is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booth not found")
    ensure_event_owner(booth.event, user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(booth, key, value)
    db.flush()
    return booth


def assign_booth(db: Session, user: User, payload: AssignmentCreate) -> BoothAssignment:
    booth = db.get(Booth, payload.booth_id)
    if booth is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booth not found")
    ensure_event_owner(booth.event, user)
    if booth.status == BoothStatus.ASSIGNED:
        active = db.scalar(
            select(BoothAssignment).where(
                BoothAssignment.booth_id == booth.id, BoothAssignment.status == AssignmentStatus.ACTIVE
            )
        )
        if active:
            raise HTTPException(status.HTTP_409_CONFLICT, "Booth already assigned")
    vendor = db.get(User, payload.vendor_id)
    if vendor is None or vendor.role != UserRole.VENDOR:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Vendor account required")
    if payload.application_id:
        application = db.get(VendorApplication, payload.application_id)
        if application is None or application.status != ApplicationStatus.APPROVED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Application must be approved")
        if application.vendor_id != vendor.id or application.event_id != booth.event_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Application does not match vendor/event")
    assignment = BoothAssignment(
        booth_id=booth.id,
        vendor_id=vendor.id,
        application_id=payload.application_id,
        assigned_by_id=user.id,
        status=AssignmentStatus.ACTIVE,
    )
    booth.status = BoothStatus.ASSIGNED
    db.add(assignment)
    db.flush()
    write_audit(db, actor=user, action="assign_booth", entity_type="assignment", entity_id=assignment.id)
    return assignment


def release_assignment(db: Session, user: User, assignment_id: int) -> BoothAssignment:
    assignment = db.get(BoothAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    ensure_event_owner(assignment.booth.event, user)
    assignment.status = AssignmentStatus.RELEASED
    assignment.released_at = utcnow()
    assignment.booth.status = BoothStatus.AVAILABLE
    db.flush()
    write_audit(db, actor=user, action="release_booth", entity_type="assignment", entity_id=assignment.id)
    return assignment


def list_assignments(db: Session, user: User, event_id: int | None = None) -> list[BoothAssignment]:
    stmt = select(BoothAssignment).join(Booth)
    if user.role == UserRole.VENDOR:
        stmt = stmt.where(BoothAssignment.vendor_id == user.id)
    elif user.role == UserRole.ORGANIZER:
        stmt = stmt.join(Event).where(Event.organizer_id == user.id)
    if event_id is not None:
        stmt = stmt.where(Booth.event_id == event_id)
    return list(db.scalars(stmt))
