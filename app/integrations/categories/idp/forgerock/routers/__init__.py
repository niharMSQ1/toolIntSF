from app.integrations.categories.idp.forgerock.routers.configure import idp_router as forgerock_idp_router
from app.integrations.categories.idp.forgerock.routers.configure import router as forgerock_configure_router
from app.integrations.categories.idp.forgerock.routers.data import router as forgerock_data_router
from app.integrations.categories.idp.forgerock.routers.evidence import router as forgerock_evidence_router

__all__ = [
    "forgerock_configure_router",
    "forgerock_idp_router",
    "forgerock_data_router",
    "forgerock_evidence_router",
]
