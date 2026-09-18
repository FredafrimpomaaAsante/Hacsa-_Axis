from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.booth import Booth, BoothAssignment
from app.models.enums import BoothStatus, PaymentStatus, UserRole
from app.models.event import Event
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import PaymentConfirm, PaymentCreate, PaymentWebhook
from app.services.audit import write_audit
from app.services.auth import utcnow
from app.services.operations import get_event


def initiate_payment(db: Session, user: User, payload: PaymentCreate) -> Payment:
    event = get_event(db, payload.event_id)
    if payload.assignment_id:
        assignment = db.get(BoothAssignment, payload.assignment_id)
        if assignment is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
        if user.role == UserRole.VENDOR and assignment.vendor_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only pay for your own booth")
    elif user.role == UserRole.VENDOR:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Vendors must pay against an assignment")
    payment = Payment(
        payer_id=user.id,
        event_id=event.id,
        assignment_id=payload.assignment_id,
        amount=payload.amount,
        currency=payload.currency,
        method=payload.method,
        status=PaymentStatus.PENDING,
        reference=f"HACSA-{uuid4().hex[:16].upper()}",
        description=payload.description,
    )
    db.add(payment)
    db.flush()
    write_audit(db, actor=user, action="initiate_payment", entity_type="payment", entity_id=payment.id)
    return payment


def confirm_payment(db: Session, user: User, payment_id: int, payload: PaymentConfirm) -> Payment:
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")
    if user.role == UserRole.VENDOR and payment.payer_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your payment")
    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment is not pending")
    payment.status = PaymentStatus.SUCCEEDED if payload.succeed else PaymentStatus.FAILED
    payment.provider_ref = payload.provider_ref or f"sim_{uuid4().hex[:12]}"
    payment.settled_at = utcnow()
    db.flush()
    write_audit(db, actor=user, action="confirm_payment", entity_type="payment", entity_id=payment.id)
    return payment


def apply_webhook(db: Session, payload: PaymentWebhook) -> Payment:
    payment = db.scalar(select(Payment).where(Payment.reference == payload.reference))
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown payment reference")
    payment.status = payload.status
    payment.provider_ref = payload.provider_ref
    payment.settled_at = utcnow()
    db.flush()
    write_audit(db, actor=None, action="payment_webhook", entity_type="payment", entity_id=payment.id)
    return payment


def list_payments(db: Session, user: User, event_id: int | None = None) -> list[Payment]:
    stmt = select(Payment)
    if user.role == UserRole.VENDOR:
        stmt = stmt.where(Payment.payer_id == user.id)
    elif user.role == UserRole.ORGANIZER:
        stmt = stmt.join(Event).where(Event.organizer_id == user.id)
    if event_id is not None:
        stmt = stmt.where(Payment.event_id == event_id)
    return list(db.scalars(stmt.order_by(Payment.created_at.desc())))


def refund_payment(db: Session, admin: User, payment_id: int) -> Payment:
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")
    if payment.status != PaymentStatus.SUCCEEDED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only succeeded payments can be refunded")
    payment.status = PaymentStatus.REFUNDED
    payment.settled_at = utcnow()
    db.flush()
    write_audit(db, actor=admin, action="refund_payment", entity_type="payment", entity_id=payment.id)
    return payment


def _money(value: Decimal | None) -> Decimal:
    return value if value is not None else Decimal("0.00")


def occupancy_for_event(db: Session, event: Event):
    from app.schemas.report import OccupancyReport

    total = db.scalar(select(func.count()).select_from(Booth).where(Booth.event_id == event.id)) or 0
    assigned = (
        db.scalar(
            select(func.count())
            .select_from(Booth)
            .where(Booth.event_id == event.id, Booth.status == BoothStatus.ASSIGNED)
        )
        or 0
    )
    available = total - assigned
    rate = (assigned / total) if total else 0.0
    return OccupancyReport(
        event_id=event.id,
        event_name=event.name,
        total_booths=total,
        assigned_booths=assigned,
        available_booths=available,
        occupancy_rate=round(rate, 4),
    )


def revenue_for_event(db: Session, event: Event):
    from app.schemas.report import RevenueReport

    def sum_status(status: PaymentStatus) -> Decimal:
        value = db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.event_id == event.id, Payment.status == status
            )
        )
        return _money(Decimal(value))

    count = db.scalar(select(func.count()).select_from(Payment).where(Payment.event_id == event.id)) or 0
    return RevenueReport(
        event_id=event.id,
        event_name=event.name,
        succeeded_amount=sum_status(PaymentStatus.SUCCEEDED),
        pending_amount=sum_status(PaymentStatus.PENDING),
        refunded_amount=sum_status(PaymentStatus.REFUNDED),
        transaction_count=count,
    )


def funnel_for_event(db: Session, event: Event):
    from app.models.application import VendorApplication
    from app.models.enums import ApplicationStatus
    from app.schemas.report import ApplicationFunnel

    def count_status(status: ApplicationStatus) -> int:
        return (
            db.scalar(
                select(func.count())
                .select_from(VendorApplication)
                .where(VendorApplication.event_id == event.id, VendorApplication.status == status)
            )
            or 0
        )

    return ApplicationFunnel(
        event_id=event.id,
        submitted=count_status(ApplicationStatus.SUBMITTED),
        under_review=count_status(ApplicationStatus.UNDER_REVIEW),
        approved=count_status(ApplicationStatus.APPROVED),
        rejected=count_status(ApplicationStatus.REJECTED),
    )
