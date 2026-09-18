from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, OrganizerUser, VendorUser
from app.core.deps import DbSession
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationReview
from app.schemas.auth import RefreshRequest, TokenPair, UserCreate, UserLogin, UserOut
from app.schemas.booth import AssignmentCreate, AssignmentOut, BoothCreate, BoothOut, BoothUpdate
from app.schemas.event import EventCreate, EventOut, EventUpdate, SessionCreate, SessionOut, SessionUpdate
from app.services import auth as auth_service
from app.services import operations as ops

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
events_router = APIRouter(prefix="/events", tags=["Events & Sessions"])
applications_router = APIRouter(prefix="/applications", tags=["Vendor Applications"])
booths_router = APIRouter(tags=["Booths & Assignments"])


@auth_router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: DbSession):
    return auth_service.register_user(db, payload)


@auth_router.post("/login", response_model=TokenPair)
def login(payload: UserLogin, db: DbSession):
    user = auth_service.authenticate(db, payload.email, payload.password)
    return auth_service.issue_tokens(user)


@auth_router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: DbSession):
    return auth_service.refresh_tokens(db, payload.refresh_token)


@auth_router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user


@events_router.get("/public", response_model=list[EventOut])
def public_events(db: DbSession):
    return ops.list_events(db, None, public_only=True)


@events_router.get("", response_model=list[EventOut])
def list_events(db: DbSession, user: CurrentUser):
    return ops.list_events(db, user)


@events_router.post("", response_model=EventOut, status_code=201)
def create_event(payload: EventCreate, db: DbSession, user: OrganizerUser):
    return ops.create_event(db, user, payload)


@events_router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: DbSession):
    return ops.get_event(db, event_id)


@events_router.patch("/{event_id}", response_model=EventOut)
def update_event(event_id: int, payload: EventUpdate, db: DbSession, user: OrganizerUser):
    return ops.update_event(db, user, event_id, payload)


@events_router.get("/{event_id}/sessions", response_model=list[SessionOut])
def list_sessions(event_id: int, db: DbSession):
    return ops.list_sessions(db, event_id)


@events_router.post("/{event_id}/sessions", response_model=SessionOut, status_code=201)
def create_session(event_id: int, payload: SessionCreate, db: DbSession, user: OrganizerUser):
    return ops.create_session(db, user, event_id, payload)


@events_router.patch("/sessions/{session_id}", response_model=SessionOut)
def update_session(session_id: int, payload: SessionUpdate, db: DbSession, user: OrganizerUser):
    return ops.update_session(db, user, session_id, payload)


@events_router.get("/{event_id}/booths", response_model=list[BoothOut])
def list_booths(event_id: int, db: DbSession):
    return ops.list_booths(db, event_id)


@events_router.post("/{event_id}/booths", response_model=BoothOut, status_code=201)
def create_booth(event_id: int, payload: BoothCreate, db: DbSession, user: OrganizerUser):
    return ops.create_booth(db, user, event_id, payload)


@applications_router.post("", response_model=ApplicationOut, status_code=201)
def submit_application(payload: ApplicationCreate, db: DbSession, user: VendorUser):
    return ops.submit_application(db, user, payload)


@applications_router.get("", response_model=list[ApplicationOut])
def list_applications(db: DbSession, user: CurrentUser, event_id: int | None = Query(default=None)):
    return ops.list_applications(db, user, event_id)


@applications_router.post("/{application_id}/review", response_model=ApplicationOut)
def review_application(application_id: int, payload: ApplicationReview, db: DbSession, user: OrganizerUser):
    return ops.review_application(db, user, application_id, payload)


@booths_router.patch("/booths/{booth_id}", response_model=BoothOut)
def update_booth(booth_id: int, payload: BoothUpdate, db: DbSession, user: OrganizerUser):
    return ops.update_booth(db, user, booth_id, payload)


@booths_router.post("/assignments", response_model=AssignmentOut, status_code=201)
def assign_booth(payload: AssignmentCreate, db: DbSession, user: OrganizerUser):
    return ops.assign_booth(db, user, payload)


@booths_router.get("/assignments", response_model=list[AssignmentOut])
def list_assignments(db: DbSession, user: CurrentUser, event_id: int | None = Query(default=None)):
    return ops.list_assignments(db, user, event_id)


@booths_router.post("/assignments/{assignment_id}/release", response_model=AssignmentOut)
def release_assignment(assignment_id: int, db: DbSession, user: OrganizerUser):
    return ops.release_assignment(db, user, assignment_id)
