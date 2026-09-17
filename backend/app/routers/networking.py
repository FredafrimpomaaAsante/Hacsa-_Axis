from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from app.connections import get_db
from app.schemas.networking import ConnectionRequestOut, ConnectionRespond
from app.schemas.user import UserOut
from app.services import (
    send_connection_request,
    respond_to_connection,
    get_connection_by_id,
    get_connections_for_user,
    list_users,
)
from app.utils import get_current_user
from app.models.user import User
from app.models.networking import ConnectionStatusEnum

router = APIRouter(prefix="/network", tags=["Networking"])


@router.get("/directory", response_model=List[UserOut])
def browse_directory(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Browse other attendees to connect with."""
    return list_users(db, exclude_user_id=current_user.id)


@router.post("/connect/{user_id}", response_model=ConnectionRequestOut, status_code=201)
def request_connection(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You can't connect with yourself")
    return send_connection_request(db, requester_id=current_user.id, recipient_id=user_id)


@router.patch("/connections/{connection_id}", response_model=ConnectionRequestOut)
def respond_connection(
    connection_id: int,
    data: ConnectionRespond,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    connection = get_connection_by_id(db, connection_id)
    if not connection or connection.recipient_id != current_user.id:
        raise HTTPException(status_code=404, detail="Connection request not found")
    return respond_to_connection(db, connection, accept=data.accept)


@router.get("/connections", response_model=List[ConnectionRequestOut])
def my_connections(
    status: Optional[ConnectionStatusEnum] = Query(None),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return get_connections_for_user(db, current_user.id, status=status)

