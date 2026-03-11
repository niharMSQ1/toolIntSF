import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DB_NAME = os.getenv("DB_NAME", "stakflo_dev")
DB_USER = os.getenv("DB_USER", "stakflo")
DB_PASSWORD = os.getenv("DB_PASSWORD", "stakflo@321")
DB_HOST = os.getenv("DB_HOST", "192.168.6.4")
DB_PORT = os.getenv("DB_PORT", "5432")

# URL‑encode password so special characters like '@' don't break the DSN
ENC_PASSWORD = quote_plus(DB_PASSWORD)

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{ENC_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

