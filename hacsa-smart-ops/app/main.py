from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import *  # noqa: F401,F403
from app.services.auth import ensure_admin_exists


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_admin_exists(db, settings.seed_admin_email, settings.seed_admin_password)
        db.commit()
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Organizers & Vendors backend for HACSA AXIS.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": settings.app_name}
