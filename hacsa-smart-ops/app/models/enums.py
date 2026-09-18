from enum import Enum

from sqlalchemy import Enum as SAEnum


def db_enum(enum_cls):
    """Persist lowercase enum *values* as VARCHAR so MySQL and SQLite stay aligned."""
    return SAEnum(
        enum_cls,
        values_callable=lambda members: [item.value for item in members],
        native_enum=False,
        length=32,
        validate_strings=True,
    )


class UserRole(str, Enum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    VENDOR = "vendor"


class EventStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ApplicationStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class BoothStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    ASSIGNED = "assigned"
    MAINTENANCE = "maintenance"


class AssignmentStatus(str, Enum):
    ACTIVE = "active"
    RELEASED = "released"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_MONEY = "mobile_money"
    CASH = "cash"
