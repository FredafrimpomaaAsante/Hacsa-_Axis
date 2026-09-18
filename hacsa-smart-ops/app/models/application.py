from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ApplicationStatus, db_enum


class VendorApplication(Base):
    __tablename__ = "vendor_applications"
    __table_args__ = (UniqueConstraint("vendor_id", "event_id", name="uq_vendor_event_application"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    products: Mapped[str] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_booth_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        db_enum(ApplicationStatus), default=ApplicationStatus.SUBMITTED, index=True
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vendor = relationship("User", back_populates="applications", foreign_keys=[vendor_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by_id])
    event = relationship("Event", back_populates="applications")
    assignment = relationship("BoothAssignment", back_populates="application", uselist=False)
