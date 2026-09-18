"""SQLAlchemy engine, session, and schema initialization utilities."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def configure_database(database_url: str) -> None:
    """Configure the database engine and associated session factory."""
    global _engine, _SessionLocal
    connect_args = (
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    _engine = create_engine(database_url, connect_args=connect_args)
    _SessionLocal = sessionmaker(
        bind=_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_session_factory() -> sessionmaker[Session]:
    """Return the configured session factory."""
    if _SessionLocal is None:
        raise RuntimeError("Database is not configured.")
    return _SessionLocal


def create_tables() -> None:
    """Create the configured database schema."""
    if _engine is None:
        raise RuntimeError("Database is not configured.")
    Base.metadata.create_all(bind=_engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and guarantee it is closed afterward."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
