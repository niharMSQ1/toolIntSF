from app.integrations.categories.idp.sailpoint.routers.configure import idp_router as sailpoint_idp_router
from app.integrations.categories.idp.sailpoint.routers.configure import router as sailpoint_configure_router
from app.integrations.categories.idp.sailpoint.routers.data import router as sailpoint_data_router
from app.integrations.categories.idp.sailpoint.routers.evidence import router as sailpoint_evidence_router

__all__ = [
    "sailpoint_configure_router",
    "sailpoint_idp_router",
    "sailpoint_data_router",
    "sailpoint_evidence_router",
]
