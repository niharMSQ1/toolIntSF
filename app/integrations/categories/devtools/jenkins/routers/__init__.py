"""Jenkins HTTP routers."""

from app.integrations.categories.devtools.jenkins.routers.configure import router as configure_router
from app.integrations.categories.devtools.jenkins.routers.data import router as data_router
from app.integrations.categories.devtools.jenkins.routers.webhook import router as webhook_router

__all__ = [
    "configure_router",
    "data_router",
    "webhook_router",
]
