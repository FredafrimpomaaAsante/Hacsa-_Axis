from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.connections import get_db
from app.models.event_registration import EventRegistration
from app.models.user import User

router = APIRouter(prefix="/badges", tags=["Badges"])


def _access_id(person_id: str) -> str:
    return f"HAX-{person_id.replace('-', '')[:8].upper()}-26"


@router.get("/verify/{person_id}")
def verify_badge(person_id: UUID, db: Session = Depends(get_db)):
    person_key = str(person_id)
    user = db.query(User).filter(User.person_id == person_key).first()
    registration = None
    if user:
        registration = (
            db.query(EventRegistration)
            .filter(EventRegistration.user_id == user.id)
            .order_by(EventRegistration.registered_at.desc())
            .first()
        )

    event_id = registration.event_id if registration else None
    event_name = registration.event_name if registration else "No event registered"

    if user is None:
        return {
            "full_name": None,
            "access_id": _access_id(person_key),
            "registered": False,
            "event_id": None,
            "event_name": "No event registered",
        }

    return {
        "full_name": user.full_name,
        "access_id": _access_id(user.person_id),
        "registered": registration is not None,
        "event_id": event_id,
        "event_name": event_name,
    }
