from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Base

_engine = None
_SessionLocal = None


def configure_database(database_url: str) -> None:
    global _engine, _SessionLocal
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    _engine = create_engine(database_url, connect_args=connect_args)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_session_factory() -> sessionmaker:
    if _SessionLocal is None:
        raise RuntimeError("Database is not configured.")
    return _SessionLocal


def create_tables() -> None:
    if _engine is None:
        raise RuntimeError("Database is not configured.")
    Base.metadata.create_all(bind=_engine)


def get_db() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
