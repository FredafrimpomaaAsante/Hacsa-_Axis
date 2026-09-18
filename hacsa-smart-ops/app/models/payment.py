from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PaymentMethod, PaymentStatus, db_enum


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    assignment_id: Mapped[int | None] = mapped_column(ForeignKey("booth_assignments.id"), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8), default="GHS")
    method: Mapped[PaymentMethod] = mapped_column(db_enum(PaymentMethod), default=PaymentMethod.CARD)
    status: Mapped[PaymentStatus] = mapped_column(db_enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    reference: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    provider_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    payer = relationship("User", back_populates="payments", foreign_keys=[payer_id])
    event = relationship("Event", back_populates="payments")
    assignment = relationship("BoothAssignment", back_populates="payments")
