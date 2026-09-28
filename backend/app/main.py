from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from jose import JWTError

from app.config import settings
from app.connections import Base, SessionLocal, engine
from app.models import (  # noqa: F401
    user,
    event_registration,
    schedule,
    notification,
    networking,
    engagement,
    attendance,
    safety,
    audit,
)
from app.models.audit import AuditLog
from app.models.enums import AuditAction
from app.models.user import User
from app.routers import (
    auth,
    badges,
    registrations,
    profile,
    schedule as schedule_router,
    notifications,
    networking as networking_router,
    engagement as engagement_router,
    attendance as attendance_router,
    occupancy,
    incidents,
    alerts,
    analytics,
    audit as audit_router,
    reports,
)
from app.realtime import manager
from app.seed import seed_demo
from app.utils import decode_access_token
from fastapi import WebSocket, WebSocketDisconnect

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed_demo(db)

app = FastAPI(
    title=settings.APP_NAME,
    description="Unified HACSA Axis event platform: attendees, speakers, organisers, and live operations.",
    version="1.0.0",
)


@app.middleware("http")
async def audit_authenticated_changes(request: Request, call_next):
    actions = {
        "POST": AuditAction.CREATE,
        "PUT": AuditAction.UPDATE,
        "PATCH": AuditAction.UPDATE,
        "DELETE": AuditAction.DELETE,
    }
    action = actions.get(request.method)
    if not action or request.url.path.startswith(f"{settings.API_V1_PREFIX}/audit"):
        return await call_next(request)

    started_at = datetime.utcnow()
    response = await call_next(request)
    if response.status_code >= 400:
        return response

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return response

    try:
        payload = decode_access_token(token)
    except JWTError:
        return response

    person_id = payload.get("person_id") or payload.get("sub")
    if not person_id:
        return response

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.person_id == person_id).first()
        if not user:
            return response

        existing_activity = db.query(AuditLog.id).filter(
            AuditLog.actor_id == str(user.id),
            AuditLog.created_at >= started_at,
        ).first()
        if existing_activity:
            return response

        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)
        route_name = getattr(route, "name", None) or route_path
        path_parameters = request.path_params
        entity_id = next(iter(path_parameters.values()), None)
        db.add(AuditLog(
            actor_id=str(user.id),
            actor_role=user.role.value,
            action=action,
            entity_type=str(route_name)[:60],
            entity_id=str(entity_id) if entity_id is not None else None,
            detail=f"{user.full_name} {action.value} {route_path} (HTTP {response.status_code})",
            ip_address=request.client.host if request.client else None,
        ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(badges.router)
app.include_router(registrations.router)
app.include_router(profile.router)
app.include_router(schedule_router.router)
app.include_router(notifications.router)
app.include_router(networking_router.router)
app.include_router(engagement_router.router)
app.include_router(attendance_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(occupancy.router, prefix=settings.API_V1_PREFIX)
app.include_router(incidents.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": settings.APP_NAME, "event_id": settings.DEFAULT_EVENT_ID}


@app.get("/api/config", tags=["Health"])
def public_config():
    return {
        "event_id": settings.DEFAULT_EVENT_ID,
        "app_name": settings.APP_NAME,
        "public_app_url": settings.PUBLIC_APP_URL,
        "event_center": {
            "name": settings.EVENT_CENTER_NAME,
            "location": settings.EVENT_CENTER_LOCATION,
            "latitude": settings.EVENT_CENTER_LATITUDE,
            "longitude": settings.EVENT_CENTER_LONGITUDE,
            "coordinates_approximate": settings.EVENT_CENTER_COORDINATES_APPROXIMATE,
        },
    }


@app.websocket("/ws/operations")
async def operations_feed(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
