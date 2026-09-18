from fastapi import APIRouter

from app.api.v1.organizers import applications_router, auth_router, booths_router, events_router
from app.api.v1.platform import admin_router, payments_router, reports_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(events_router)
api_router.include_router(applications_router)
api_router.include_router(booths_router)
api_router.include_router(payments_router)
api_router.include_router(reports_router)
api_router.include_router(admin_router)
