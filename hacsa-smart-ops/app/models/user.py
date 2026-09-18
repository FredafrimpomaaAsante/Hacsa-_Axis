from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole, db_enum


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    role: Mapped[UserRole] = mapped_column(db_enum(UserRole), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    organization_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    events = relationship("Event", back_populates="organizer", foreign_keys="Event.organizer_id")
    applications = relationship("VendorApplication", back_populates="vendor", foreign_keys="VendorApplication.vendor_id")
    assignments = relationship("BoothAssignment", back_populates="vendor", foreign_keys="BoothAssignment.vendor_id")
    payments = relationship("Payment", back_populates="payer", foreign_keys="Payment.payer_id")
