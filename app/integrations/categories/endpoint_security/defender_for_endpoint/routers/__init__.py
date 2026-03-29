from app.integrations.categories.endpoint_security.defender_for_endpoint.routers.configure import (
    router as configure_router,
)
from app.integrations.categories.endpoint_security.defender_for_endpoint.routers.evidence import (
    router as evidence_router,
)

__all__ = ["configure_router", "evidence_router"]
