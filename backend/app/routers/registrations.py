from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.connections import get_db
from app.email_service import send_registration_confirmation_email
from app.models.event_registration import EventRegistration
from app.models.user import RoleEnum, User
from app.schemas.registration import EventRegistrationCreate, EventRegistrationOut
from app.services import create_notification
from app.utils import get_current_user, require_roles

router = APIRouter(prefix="/registrations", tags=["Event registrations"])

EVENTS = {
    "hackathon": "HACSA Tech4Girls Hackathon",
    "graduation": "Tech4Girls Cohort 5 Graduation",
    "summit-2026": "Sankofa Summit 2026",
}


def _registration_output(registration: EventRegistration) -> dict:
    return {
        "event_id": registration.event_id,
        "event_name": registration.event_name,
        "registered": True,
        "registered_at": registration.registered_at,
    }


@router.post("", response_model=EventRegistrationOut, status_code=status.HTTP_201_CREATED)
def register_for_event(
    data: EventRegistrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.participant)),
):
    event_name = EVENTS.get(data.event_id)
    if event_name is None:
        raise HTTPException(status_code=404, detail="Event not found")

    registration = (
        db.query(EventRegistration)
        .filter_by(event_id=data.event_id, user_id=current_user.id)
        .first()
    )
    if registration:
        return _registration_output(registration)

    registration = EventRegistration(
        event_id=data.event_id,
        event_name=event_name,
        user_id=current_user.id,
    )
    db.add(registration)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        registration = (
            db.query(EventRegistration)
            .filter_by(event_id=data.event_id, user_id=current_user.id)
            .first()
        )
        if registration is None:
            raise
    else:
        db.refresh(registration)

    create_notification(
        db,
        user_id=current_user.id,
        title="Registration confirmed",
        message=(
            f"You are registered for {registration.event_name}. "
            f"Your access details are ready in your badge."
        ),
    )

    send_registration_confirmation_email(
        current_user.email,
        current_user.full_name,
        registration.event_name,
        registration.event_id,
    )

    return _registration_output(registration)


@router.get("/mine/{event_id}")
def my_event_registration(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event_name = EVENTS.get(event_id)
    if event_name is None:
        raise HTTPException(status_code=404, detail="Event not found")

    registration = (
        db.query(EventRegistration)
        .filter_by(event_id=event_id, user_id=current_user.id)
        .first()
    )
    return {
        "event_id": event_id,
        "event_name": event_name,
        "registered": registration is not None,
        "registered_at": registration.registered_at if registration else None,
    }
