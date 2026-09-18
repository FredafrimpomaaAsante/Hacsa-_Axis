from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AssignmentStatus, BoothStatus, db_enum


class Booth(Base):
    __tablename__ = "booths"
    __table_args__ = (UniqueConstraint("event_id", "code", name="uq_event_booth_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    code: Mapped[str] = mapped_column(String(40))
    zone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    size: Mapped[str] = mapped_column(String(40), default="standard")
    fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[BoothStatus] = mapped_column(db_enum(BoothStatus), default=BoothStatus.AVAILABLE, index=True)

    event = relationship("Event", back_populates="booths")
    assignments = relationship("BoothAssignment", back_populates="booth")


class BoothAssignment(Base):
    __tablename__ = "booth_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booth_id: Mapped[int] = mapped_column(ForeignKey("booths.id"), index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("vendor_applications.id"), nullable=True)
    assigned_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[AssignmentStatus] = mapped_column(db_enum(AssignmentStatus), default=AssignmentStatus.ACTIVE)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    booth = relationship("Booth", back_populates="assignments")
    vendor = relationship("User", back_populates="assignments", foreign_keys=[vendor_id])
    application = relationship("VendorApplication", back_populates="assignment")
    payments = relationship("Payment", back_populates="assignment")
