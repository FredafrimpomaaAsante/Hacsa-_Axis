from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from app.connections import get_db
from app.schemas.notifications import NotificationOut
from app.services import get_notifications_for_user, mark_notification_read
from app.utils import get_current_user
from app.models.user import User
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationOut])
def list_my_notifications(
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return get_notifications_for_user(db, current_user.id, unread_only=unread_only)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def read_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return mark_notification_read(db, notification)

