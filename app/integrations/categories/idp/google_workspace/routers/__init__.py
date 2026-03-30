from app.integrations.categories.idp.google_workspace.routers.configure import idp_router as google_workspace_idp_router
from app.integrations.categories.idp.google_workspace.routers.configure import router as google_workspace_configure_router
from app.integrations.categories.idp.google_workspace.routers.data import router as google_workspace_data_router
from app.integrations.categories.idp.google_workspace.routers.evidence import router as google_workspace_evidence_router

__all__ = [
    "google_workspace_configure_router",
    "google_workspace_idp_router",
    "google_workspace_data_router",
    "google_workspace_evidence_router",
]
