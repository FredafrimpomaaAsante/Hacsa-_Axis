from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.rbac import ensure_event_owner
from app.models.application import VendorApplication
from app.models.enums import ApplicationStatus, UserRole
from app.models.event import Event, EventSession
from app.models.user import User
from app.schemas.report import EventSummary
from app.services.operations import get_event
from app.services.payments import funnel_for_event, occupancy_for_event, revenue_for_event


def event_summary(db: Session, user: User, event_id: int) -> EventSummary:
    event = get_event(db, event_id)
    if user.role != UserRole.ADMIN:
        ensure_event_owner(event, user)
    sessions = db.scalar(select(func.count()).select_from(EventSession).where(EventSession.event_id == event.id)) or 0
    approved = (
        db.scalar(
            select(func.count())
            .select_from(VendorApplication)
            .where(
                VendorApplication.event_id == event.id,
                VendorApplication.status == ApplicationStatus.APPROVED,
            )
        )
        or 0
    )
    return EventSummary(
        event_id=event.id,
        event_name=event.name,
        sessions=sessions,
        vendors_approved=approved,
        occupancy=occupancy_for_event(db, event),
        revenue=revenue_for_event(db, event),
        applications=funnel_for_event(db, event),
    )


def list_occupancy(db: Session, user: User):
    events = _visible_events(db, user)
    return [occupancy_for_event(db, event) for event in events]


def list_revenue(db: Session, user: User):
    events = _visible_events(db, user)
    return [revenue_for_event(db, event) for event in events]


def list_funnels(db: Session, user: User):
    events = _visible_events(db, user)
    return [funnel_for_event(db, event) for event in events]


def _visible_events(db: Session, user: User) -> list[Event]:
    stmt = select(Event)
    if user.role == UserRole.ORGANIZER:
        stmt = stmt.where(Event.organizer_id == user.id)
    elif user.role == UserRole.VENDOR:
        stmt = stmt.join(VendorApplication).where(VendorApplication.vendor_id == user.id)
    return list(db.scalars(stmt))
