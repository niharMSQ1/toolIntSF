from app.integrations.categories.idp.ping_identity.routers.configure import (
    idp_router as ping_identity_idp_router,
    router as ping_identity_configure_router,
)
from app.integrations.categories.idp.ping_identity.routers.data import router as ping_identity_data_router
from app.integrations.categories.idp.ping_identity.routers.evidence import router as ping_identity_evidence_router

__all__ = [
    "ping_identity_configure_router",
    "ping_identity_idp_router",
    "ping_identity_data_router",
    "ping_identity_evidence_router",
]
