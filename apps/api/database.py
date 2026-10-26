"""
SQLAlchemy 2.0 Database Session and Engine setup.
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from apps.api.config import api_settings

connect_args = {"check_same_thread": False} if api_settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    api_settings.database_url,
    connect_args=connect_args,
    echo=api_settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables on application startup."""
    from apps.api import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
