import enum
from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey, UniqueConstraint

from app.connections import Base


class ConnectionStatusEnum(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class NetworkConnection(Base):
    """An attendee-to-attendee networking connection request."""

    __tablename__ = "network_connections"
    __table_args__ = (
        UniqueConstraint("requester_id", "recipient_id", name="uq_network_pair"),
    )

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(
        Enum(ConnectionStatusEnum), default=ConnectionStatusEnum.pending, nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)
