import enum


class CheckInMethod(str, enum.Enum):
    QR_SCAN = "qr_scan"
    MANUAL = "manual"  # staff override when a pass won't scan


class IncidentSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class AlertType(str, enum.Enum):
    CROWD = "crowd"
    INCIDENT = "incident"
    WEATHER = "weather"
    MEDICAL = "medical"
    OTHER = "other"


class AlertLevel(str, enum.Enum):
    INFO = "info"
    ELEVATED = "elevated"
    CRITICAL = "critical"


class EscalationLevel(str, enum.Enum):
    """Who currently needs to act on this alert."""
    NONE = "none"
    SUPERVISOR = "supervisor"
    OPERATIONS_LEAD = "operations_lead"
    EMERGENCY_SERVICES = "emergency_services"


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"
    EXPORT = "export"
    LOGIN_DENIED = "login_denied"
