from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    UniqueConstraint,
    Index,
)

from app.database import Base
from app.models.enums import CheckInMethod


class CheckIn(Base):
    """
    Records when a participant checks into the event.

    One successful check-in is allowed per participant
    for each event.
    """

    __tablename__ = "check_ins"

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "participant_id",
            name="uq_one_checkin_per_event",
        ),
        Index(
            "ix_checkin_event_time",
            "event_id",
            "checked_in_at",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    event_id = Column(
        String(64),
        nullable=False,
        index=True,
    )

    participant_id = Column(
        String(64),
        nullable=False,
        index=True,
    )

    pass_code = Column(
        String(128),
        nullable=False,
    )

    method = Column(
        Enum(CheckInMethod),
        default=CheckInMethod.QR_SCAN,
        nullable=False,
    )

    scanned_by = Column(
        String(64),
        nullable=False,
    )

    checked_in_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class ScanRejection(Base):
    """
    Records failed or duplicate check-in attempts.
    """

    __tablename__ = "scan_rejections"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    event_id = Column(
        String(64),
        nullable=False,
        index=True,
    )

    pass_code = Column(
        String(128),
        nullable=True,
    )

    reason = Column(
        String(200),
        nullable=False,
    )

    scanned_by = Column(
        String(64),
        nullable=False,
    )

    occurred_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
