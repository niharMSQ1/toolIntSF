"""
Central mount point for all integration HTTP routes (Facade).

Add new category routers here (e.g. IDP Okta) without changing `main.py`.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.integrations.categories.cspm.wiz.routers import (
    configure_router as wiz_configure_router,
    evidence_router as wiz_evidence_router,
)
from app.integrations.categories.devtools.bitbucket.routers import (
    callback_router as bitbucket_callback_router,
    configure_router as bitbucket_configure_router,
    evidence_router as bitbucket_evidence_router,
    oauth_authorize_router as bitbucket_oauth_authorize_router,
    workspaces_router as bitbucket_workspaces_router,
)
from app.integrations.categories.hrms.zoho_people.routers import configure, evidence, oauth
from app.integrations.categories.idp.microsoft_entra.routers import (
    configure as entra_configure,
    evidence as entra_evidence,
    oauth as entra_oauth,
)
from app.integrations.routers import integration_sync


def mount_integration_routes(app: FastAPI) -> None:
    """Register all provider routers on the FastAPI application."""
    app.include_router(wiz_configure_router)
    app.include_router(wiz_evidence_router)
    app.include_router(bitbucket_configure_router)
    app.include_router(bitbucket_workspaces_router)
    app.include_router(bitbucket_oauth_authorize_router)
    app.include_router(bitbucket_callback_router)
    app.include_router(bitbucket_evidence_router)
    app.include_router(configure.router)
    app.include_router(configure.hrms_router)
    app.include_router(oauth.router)
    app.include_router(evidence.router)
    app.include_router(entra_configure.commercial_router)
    app.include_router(entra_configure.commercial_idp_router)
    app.include_router(entra_configure.gcc_high_router)
    app.include_router(entra_configure.gcc_high_idp_router)
    app.include_router(entra_oauth.router)
    app.include_router(entra_evidence.router)
    app.include_router(integration_sync.router)
