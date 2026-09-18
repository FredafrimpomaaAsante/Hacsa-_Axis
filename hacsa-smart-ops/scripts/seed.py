from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.application import VendorApplication
from app.models.booth import Booth, BoothAssignment
from app.models.enums import (
    ApplicationStatus,
    AssignmentStatus,
    BoothStatus,
    EventStatus,
    PaymentMethod,
    PaymentStatus,
    UserRole,
)
from app.models.event import Event, EventSession
from app.models.payment import Payment
from app.models.user import User


def seed(db: Session) -> None:
    if db.query(User).filter(User.email == "organizer@hacsa10.example.com").first():
        return

    organizer = User(
        email="organizer@hacsa10.example.com",
        hashed_password=hash_password("Organizer123!"),
        full_name="Ama Mensah",
        role=UserRole.ORGANIZER,
        organization_name="HACSA@10 Organizing Committee",
        phone="+233200000001",
    )
    vendor = User(
        email="vendor@hacsa10.example.com",
        hashed_password=hash_password("Vendor123!"),
        full_name="Kojo Boateng",
        role=UserRole.VENDOR,
        business_name="Kojo Crafts Ltd",
        phone="+233200000002",
    )
    db.add_all([organizer, vendor])
    db.flush()

    now = datetime.now(timezone.utc)
    event = Event(
        organizer_id=organizer.id,
        name="HACSA@10 Anniversary Expo",
        description="Smart operations showcase for the 10th anniversary.",
        venue="Accra International Conference Centre",
        start_at=now + timedelta(days=30),
        end_at=now + timedelta(days=33),
        status=EventStatus.PUBLISHED,
    )
    db.add(event)
    db.flush()

    db.add(
        EventSession(
            event_id=event.id,
            title="Opening Keynote: Digital Operations",
            speaker="Dr. Adwoa Sarpong",
            location="Main Hall",
            start_at=event.start_at,
            end_at=event.start_at + timedelta(hours=2),
            capacity=400,
        )
    )
    booth = Booth(
        event_id=event.id,
        code="A12",
        zone="Main Pavilion",
        size="3x3",
        fee=Decimal("1500.00"),
        status=BoothStatus.AVAILABLE,
    )
    db.add(booth)
    db.flush()

    application = VendorApplication(
        vendor_id=vendor.id,
        event_id=event.id,
        products="Handcrafted souvenirs and apparel",
        message="We would like a high-traffic booth.",
        requested_booth_size="3x3",
        status=ApplicationStatus.APPROVED,
        reviewed_by_id=organizer.id,
        reviewed_at=now,
        review_notes="Strong brand fit.",
    )
    db.add(application)
    db.flush()

    booth.status = BoothStatus.ASSIGNED
    assignment = BoothAssignment(
        booth_id=booth.id,
        vendor_id=vendor.id,
        application_id=application.id,
        assigned_by_id=organizer.id,
        status=AssignmentStatus.ACTIVE,
    )
    db.add(assignment)
    db.flush()

    db.add(
        Payment(
            payer_id=vendor.id,
            event_id=event.id,
            assignment_id=assignment.id,
            amount=Decimal("1500.00"),
            currency="GHS",
            method=PaymentMethod.MOBILE_MONEY,
            status=PaymentStatus.SUCCEEDED,
            reference="HACSA-SEED-0001",
            provider_ref="sim_seed",
            description="Booth A12 fee",
            settled_at=now,
        )
    )
    db.flush()


if __name__ == "__main__":
    session = SessionLocal()
    try:
        seed(session)
        session.commit()
        print("Seed data created (organizer@hacsa10.example.com / vendor@hacsa10.example.com).")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
