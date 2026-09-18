"""SQLAlchemy engine, session, and schema initialization utilities."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database.models import Base


def create_database_engine(database_url: str) -> Engine:
    """Create an engine configured for SQLite or a future SQLAlchemy dialect."""
    connect_args = (
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    return create_engine(database_url, connect_args=connect_args)


database_url = get_settings().database_url.get_secret_value()
engine = create_database_engine(database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_database() -> None:
    """Create the configured database schema if it does not already exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and guarantee it is closed afterward."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
