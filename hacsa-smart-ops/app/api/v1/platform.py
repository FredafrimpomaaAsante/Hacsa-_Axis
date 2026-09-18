from fastapi import APIRouter, Query

from app.core.deps import AdminUser, CurrentUser, DbSession, OrganizerUser
from app.schemas.admin import AdminUserOut, AuditLogOut, UserAdminUpdate
from app.schemas.payment import PaymentConfirm, PaymentCreate, PaymentOut, PaymentWebhook
from app.schemas.report import ApplicationFunnel, EventSummary, OccupancyReport, RevenueReport
from app.services import admin as admin_service
from app.services import payments as payment_service
from app.services import reports as report_service

payments_router = APIRouter(prefix="/payments", tags=["Payments & Transactions"])
reports_router = APIRouter(prefix="/reports", tags=["Reporting"])
admin_router = APIRouter(prefix="/admin", tags=["Administration"])


@payments_router.post("", response_model=PaymentOut, status_code=201)
def initiate_payment(payload: PaymentCreate, db: DbSession, user: CurrentUser):
    return payment_service.initiate_payment(db, user, payload)


@payments_router.get("", response_model=list[PaymentOut])
def list_payments(db: DbSession, user: CurrentUser, event_id: int | None = Query(default=None)):
    return payment_service.list_payments(db, user, event_id)


@payments_router.post("/{payment_id}/confirm", response_model=PaymentOut)
def confirm_payment(payment_id: int, payload: PaymentConfirm, db: DbSession, user: CurrentUser):
    return payment_service.confirm_payment(db, user, payment_id, payload)


@payments_router.post("/webhooks/gateway", response_model=PaymentOut)
def payment_webhook(payload: PaymentWebhook, db: DbSession):
    return payment_service.apply_webhook(db, payload)


@payments_router.post("/{payment_id}/refund", response_model=PaymentOut)
def refund_payment(payment_id: int, db: DbSession, user: AdminUser):
    return payment_service.refund_payment(db, user, payment_id)


@reports_router.get("/events/{event_id}/summary", response_model=EventSummary)
def event_summary(event_id: int, db: DbSession, user: OrganizerUser):
    return report_service.event_summary(db, user, event_id)


@reports_router.get("/occupancy", response_model=list[OccupancyReport])
def occupancy(db: DbSession, user: CurrentUser):
    return report_service.list_occupancy(db, user)


@reports_router.get("/revenue", response_model=list[RevenueReport])
def revenue(db: DbSession, user: CurrentUser):
    return report_service.list_revenue(db, user)


@reports_router.get("/applications", response_model=list[ApplicationFunnel])
def application_funnel(db: DbSession, user: CurrentUser):
    return report_service.list_funnels(db, user)


@admin_router.get("/users", response_model=list[AdminUserOut])
def list_users(db: DbSession, _: AdminUser):
    return admin_service.list_users(db)


@admin_router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(user_id: int, payload: UserAdminUpdate, db: DbSession, admin: AdminUser):
    return admin_service.update_user(db, admin, user_id, payload)


@admin_router.get("/audit-logs", response_model=list[AuditLogOut])
def audit_logs(db: DbSession, _: AdminUser, limit: int = Query(default=100, le=500)):
    return admin_service.list_audit_logs(db, limit)


@admin_router.get("/stats")
def stats(db: DbSession, _: AdminUser):
    return admin_service.platform_stats(db)
