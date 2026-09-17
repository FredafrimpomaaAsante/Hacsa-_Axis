"""
Database connection setup. The connection string comes entirely from the
DATABASE_URL environment variable — no host, user, or password is hardcoded
here. IF DATABASE_URL is unset, this falls back to a local SQLite file so
the API still runs with zero setup for local testing.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend1.db")

# SQLite needs this flag for use with FastAPI's threaded request handling;
# other databases (Postgres, MySQL) don't need it.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and always closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

