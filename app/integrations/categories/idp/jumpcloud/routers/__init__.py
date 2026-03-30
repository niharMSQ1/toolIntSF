from app.integrations.categories.idp.jumpcloud.routers.configure import idp_router as jumpcloud_idp_router
from app.integrations.categories.idp.jumpcloud.routers.configure import router as jumpcloud_configure_router
from app.integrations.categories.idp.jumpcloud.routers.data import router as jumpcloud_data_router
from app.integrations.categories.idp.jumpcloud.routers.evidence import router as jumpcloud_evidence_router

__all__ = [
    "jumpcloud_configure_router",
    "jumpcloud_idp_router",
    "jumpcloud_data_router",
    "jumpcloud_evidence_router",
]
