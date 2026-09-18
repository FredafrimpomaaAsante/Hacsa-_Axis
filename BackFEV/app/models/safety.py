from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    ForeignKey,
    Text,
    Boolean,
    Index,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from app.database import Base

from app.models.enums import (
    IncidentSeverity,
    IncidentStatus,
    AlertType,
    AlertLevel,
    EscalationLevel,
)


class Incident(Base):
    """
    Represents an operational incident reported during the event.
    """

    __tablename__ = "incidents"

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

    reported_by = Column(
        String(64),
        nullable=False,
    )

    location = Column(
        String(150),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    severity = Column(
        Enum(IncidentSeverity),
        default=IncidentSeverity.LOW,
        nullable=False,
    )

    status = Column(
        Enum(IncidentStatus),
        default=IncidentStatus.OPEN,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    acknowledged_at = Column(
        DateTime,
        nullable=True,
    )

    resolved_at = Column(
        DateTime,
        nullable=True,
    )

    assignments = relationship(
        "ResponseAssignment",
        back_populates="incident",
    )

    alerts = relationship(
        "SafetyAlert",
        back_populates="incident",
    )

    @property
    def response_time_seconds(self) -> int | None:
        """
        Calculates the time from when the incident was reported
        until it was resolved.
        """

        if not self.resolved_at:
            return None

        return int(
            (self.resolved_at - self.created_at).total_seconds()
        )


class ResponseAssignment(Base):
    """
    Records who was assigned to respond to an incident.
    """

    __tablename__ = "response_assignments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    incident_id = Column(
        Integer,
        ForeignKey("incidents.id"),
        nullable=False,
    )

    responder_id = Column(
        String(64),
        nullable=False,
    )

    assigned_by = Column(
        String(64),
        nullable=False,
    )

    assigned_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    status = Column(
        Enum(IncidentStatus),
        default=IncidentStatus.ASSIGNED,
        nullable=False,
    )

    incident = relationship(
        "Incident",
        back_populates="assignments",
    )


class VenueZone(Base):
    """
    Stores the current occupancy of a venue zone.
    """

    __tablename__ = "venue_zones"

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "zone_name",
            name="uq_zone_per_event",
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

    zone_name = Column(
        String(100),
        nullable=False,
    )

    current_count = Column(
        Integer,
        default=0,
        nullable=False,
    )

    capacity = Column(
        Integer,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    @property
    def utilisation(self) -> float:
        """
        Returns the percentage of the zone capacity currently occupied.
        """

        if self.capacity == 0:
            return 0.0

        return round(
            self.current_count / self.capacity,
            4,
        )


class OccupancyReading(Base):
    """
    Stores the history of occupancy levels over time.
    """

    __tablename__ = "occupancy_readings"

    __table_args__ = (
        Index(
            "ix_reading_event_zone_time",
            "event_id",
            "zone_name",
            "recorded_at",
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

    zone_name = Column(
        String(100),
        nullable=False,
    )

    current_count = Column(
        Integer,
        nullable=False,
    )

    capacity = Column(
        Integer,
        nullable=False,
    )

    recorded_by = Column(
        String(64),
        nullable=False,
    )

    recorded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class SafetyAlert(Base):
    """
    Represents a safety alert caused by an incident,
    crowd conditions, weather, medical situations, etc.
    """

    __tablename__ = "safety_alerts"

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

    alert_type = Column(
        Enum(AlertType),
        default=AlertType.OTHER,
        nullable=False,
    )

    level = Column(
        Enum(AlertLevel),
        default=AlertLevel.INFO,
        nullable=False,
    )

    escalation_level = Column(
        Enum(EscalationLevel),
        default=EscalationLevel.NONE,
        nullable=False,
    )

    zone_name = Column(
        String(100),
        nullable=True,
    )

    incident_id = Column(
        Integer,
        ForeignKey("incidents.id"),
        nullable=True,
    )

    message = Column(
        String(255),
        nullable=False,
    )

    created_by = Column(
        String(64),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    acknowledged_by = Column(
        String(64),
        nullable=True,
    )

    acknowledged_at = Column(
        DateTime,
        nullable=True,
    )

    resolved = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    resolved_at = Column(
        DateTime,
        nullable=True,
    )

    incident = relationship(
        "Incident",
        back_populates="alerts",
    )

    escalations = relationship(
        "AlertEscalation",
        back_populates="alert",
    )


class AlertEscalation(Base):
    """
    Records each time a safety alert is escalated.
    """

    __tablename__ = "alert_escalations"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    alert_id = Column(
        Integer,
        ForeignKey("safety_alerts.id"),
        nullable=False,
    )

    from_level = Column(
        Enum(EscalationLevel),
        nullable=False,
    )

    to_level = Column(
        Enum(EscalationLevel),
        nullable=False,
    )

    reason = Column(
        String(255),
        nullable=True,
    )

    escalated_by = Column(
        String(64),
        nullable=True,
    )

    escalated_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    alert = relationship(
        "SafetyAlert",
        back_populates="escalations",
    )