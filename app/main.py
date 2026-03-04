"""FastAPI application entrypoint."""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database import get_db

app = FastAPI(
    title="Stakflo API",
    description="API for stakflo_dev PostgreSQL database",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "Stakflo API", "docs": "/docs"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Check DB connectivity by running a simple query."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
