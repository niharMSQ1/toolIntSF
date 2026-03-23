from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

_settings = get_settings()
engine = create_engine(
    _settings.sqlalchemy_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one SQLAlchemy session per request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def pooled_session() -> Generator[Session, None, None]:
    """Background tasks / scripts: borrow a session and close when done."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
