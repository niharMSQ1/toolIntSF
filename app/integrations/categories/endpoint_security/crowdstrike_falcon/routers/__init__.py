from app.integrations.categories.endpoint_security.crowdstrike_falcon.routers.configure import router as configure_router
from app.integrations.categories.endpoint_security.crowdstrike_falcon.routers.evidence import router as evidence_router

__all__ = ["configure_router", "evidence_router"]
