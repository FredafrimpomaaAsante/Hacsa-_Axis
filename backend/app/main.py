from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.connections import Base, SessionLocal, engine
from app.models import (  # noqa: F401
    user,
    schedule,
    notification,
    networking,
    engagement,
    attendance,
    safety,
    audit,
)
from app.routers import (
    auth,
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
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
    return {"event_id": settings.DEFAULT_EVENT_ID, "app_name": settings.APP_NAME}


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
