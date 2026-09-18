from fastapi import HTTPException, status

from app.models.enums import UserRole
from app.models.event import Event
from app.models.user import User


def ensure_event_owner(event: Event | None, user: User) -> Event:
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")
    if user.role != UserRole.ADMIN and event.organizer_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not own this event")
    return event
