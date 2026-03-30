from app.integrations.categories.idp.onelogin.routers.configure import idp_router as onelogin_idp_router
from app.integrations.categories.idp.onelogin.routers.configure import router as onelogin_configure_router
from app.integrations.categories.idp.onelogin.routers.data import router as onelogin_data_router
from app.integrations.categories.idp.onelogin.routers.evidence import router as onelogin_evidence_router

__all__ = [
    "onelogin_configure_router",
    "onelogin_idp_router",
    "onelogin_data_router",
    "onelogin_evidence_router",
]
