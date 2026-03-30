"""Workday HTTP routers."""

from app.integrations.categories.hrms.workday.routers.configure import router as configure_router
from app.integrations.categories.hrms.workday.routers.data import router as data_router
from app.integrations.categories.hrms.workday.routers.refresh import router as refresh_router
from app.integrations.categories.hrms.workday.routers.webhook import router as webhook_router

__all__ = [
    "configure_router",
    "data_router",
    "refresh_router",
    "webhook_router",
]
