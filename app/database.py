"""Database connection and session for FastAPI."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import get_database_url
from .models import Base

engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
