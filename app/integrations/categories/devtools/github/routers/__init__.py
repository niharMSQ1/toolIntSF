"""GitHub HTTP routers."""

from app.integrations.categories.devtools.github.routers.configure import router as configure_router
from app.integrations.categories.devtools.github.routers.data import router as data_router
from app.integrations.categories.devtools.github.routers.oauth import callback_router, oauth_authorize_router
from app.integrations.categories.devtools.github.routers.webhook import router as webhook_router

__all__ = [
    "callback_router",
    "configure_router",
    "data_router",
    "oauth_authorize_router",
    "webhook_router",
]
