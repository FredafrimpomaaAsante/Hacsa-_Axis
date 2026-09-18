from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app import models
from app.realtime import manager

from app.routers import (
    attendance,
    occupancy,
    incidents,
    alerts,
    analytics,
    audit,
    reports,
)


# Create the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0"
)


# Allow the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create database tables when the server starts
@app.on_event("startup")
def start_database():
    Base.metadata.create_all(bind=engine)


# Health check
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME
    }


# Real-time operations connection
@app.websocket("/ws/operations")
async def operations_feed(websocket: WebSocket):

    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# API routes
app.include_router(
    attendance.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    occupancy.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    incidents.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    alerts.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    analytics.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    audit.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    reports.router,
    prefix=settings.API_V1_PREFIX
)