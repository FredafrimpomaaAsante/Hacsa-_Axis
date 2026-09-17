from fastapi import FastAPI

from app.connections import Base, engine
from app.models import user, schedule, notification, networking, engagement  # noqa: F401 (registers tables)
from app.routers import (
    auth,
    profile,
    schedule as schedule_router,
    notifications,
    networking as networking_router,
    engagement as engagement_router,
)

# Creates tables on startup if they don't exist yet.
# For a real deployment, swap this for Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Backend Developer 1 — Participants & Speakers",
    description=(
        "Auth & role identification, participant/speaker profiles, unique speaker "
        "IDs, speaker-session assignments, session/venue/schedule APIs with "
        "schedule-change notifications, plus networking, polls, Q&A and feedback."
    ),
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(schedule_router.router)
app.include_router(notifications.router)
app.include_router(networking_router.router)
app.include_router(engagement_router.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "Backend Developer 1 — Participants & Speakers"}

