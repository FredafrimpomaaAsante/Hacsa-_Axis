from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.config import settings
from app.connections import Base
from app.models.attendance import CheckIn, ScanRejection
from app.models.safety import VenueZone
from app.models.safety import Incident, OccupancyReading, SafetyAlert
from app.models.user import RoleEnum
from app.routers.auth import login
from app.schemas.user import UserLogin
from app.seed import seed_demo


def test_seed_demo_omits_sample_operations_activity_by_default(monkeypatch):
    monkeypatch.setattr(settings, "SEED_OPS_DEMO_ACTIVITY", False)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    try:
        with session_factory() as db:
            seed_demo(db)
            zones = db.query(VenueZone).all()
            assert zones
            assert all(zone.current_count == 0 for zone in zones)
            assert db.query(OccupancyReading).count() == 0
            assert db.query(CheckIn).count() == 0
            assert db.query(ScanRejection).count() == 0
            assert db.query(Incident).count() == 0
            assert db.query(SafetyAlert).count() == 0
    finally:
        engine.dispose()


def test_seed_demo_preserves_existing_occupancy_state(monkeypatch):
    monkeypatch.setattr(settings, "SEED_OPS_DEMO_ACTIVITY", True)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    try:
        with session_factory() as db:
            seed_demo(db)
            zone = db.query(VenueZone).filter_by(
                event_id="summit-2026",
                zone_name="Main Entrance",
            ).one()
            zone.current_count = 137
            zone.capacity = 350
            db.commit()

            seed_demo(db)

            zone = db.query(VenueZone).filter_by(
                event_id="summit-2026",
                zone_name="Main Entrance",
            ).one()
            assert zone.current_count == 137
            assert zone.capacity == 350
    finally:
        engine.dispose()


def test_seed_demo_vendor_account_can_sign_in(monkeypatch):
    monkeypatch.setattr(settings, "SEED_OPS_DEMO_ACTIVITY", False)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    try:
        with session_factory() as db:
            seed_demo(db)
            result = login(
                UserLogin(email="vendor@hacsa.org", password="Axis2026!"),
                db,
            )
            assert result.user.role == RoleEnum.vendor
    finally:
        engine.dispose()