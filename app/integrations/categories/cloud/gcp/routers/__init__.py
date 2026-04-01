"""GCP HTTP routers."""

from app.integrations.categories.cloud.gcp.routers.configure import router as configure_router
from app.integrations.categories.cloud.gcp.routers.evidence import router as evidence_router

__all__ = ["configure_router", "evidence_router"]

