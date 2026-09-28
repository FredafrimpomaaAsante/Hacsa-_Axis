"""Single SQLAlchemy engine for the whole project."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_schema():  # Avoid running schema migration before all models are loaded
    try:
        from app.models.event_registration import EventRegistration  # noqa: F401
        from app.models.schedule import Venue, Session, SessionSpeaker, SessionInterest  # noqa: F401
        from app.models.notification import Notification  # noqa: F401
        from app.models.networking import NetworkConnection  # noqa: F401
        from app.models.engagement import Poll, PollOption, PollVote, Question, QuestionUpvote, Feedback  # noqa: F401
        from app.models.attendance import CheckIn, ScanRejection  # noqa: F401
        from app.models.safety import Incident, ResponseAssignment, VenueZone, OccupancyReading, SafetyAlert, AlertEscalation  # noqa: F401
        from app.models.audit import AuditLog  # noqa: F401
        Base.metadata.create_all(bind=engine)
        with engine.begin() as conn:
            result = conn.execute("SELECT name FROM pragma_table_info('users')").fetchall()
            columns = {row[0] for row in result}
            if "is_open_to_connect" not in columns:
                conn.execute(
                    "ALTER TABLE users ADD COLUMN is_open_to_connect BOOLEAN NOT NULL DEFAULT 1"
                )
    except Exception:
        pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
