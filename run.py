"""Run: uvicorn run:app --reload --host 0.0.0.0 --port 8006"""

from app.main import app

__all__ = ["app"]
