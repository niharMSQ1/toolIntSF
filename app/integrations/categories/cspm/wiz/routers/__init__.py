"""HTTP routers for Wiz CSPM."""

from app.integrations.categories.cspm.wiz.routers.configure import router as configure_router
from app.integrations.categories.cspm.wiz.routers.evidence import router as evidence_router

__all__ = ["configure_router", "evidence_router"]
