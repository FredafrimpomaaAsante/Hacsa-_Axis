from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    Text,
    Index,
)

from app.connections import Base
from app.models.enums import AuditAction


class AuditLog(Base):
    """
    Records who performed an action, what they did,
    and when it happened.
    """

    __tablename__ = "audit_logs"

    __table_args__ = (
        Index(
            "ix_audit_actor_time",
            "actor_id",
            "created_at",
        ),
        Index(
            "ix_audit_entity",
            "entity_type",
            "entity_id",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    actor_id = Column(
        String(64),
        nullable=False,
        index=True,
    )

    actor_role = Column(
        String(40),
        nullable=False,
    )

    action = Column(
        Enum(AuditAction),
        nullable=False,
    )

    entity_type = Column(
        String(60),
        nullable=False,
    )

    entity_id = Column(
        String(64),
        nullable=True,
    )

    detail = Column(
        Text,
        nullable=True,
    )

    ip_address = Column(
        String(64),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )