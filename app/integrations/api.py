"""
Central mount point for all integration HTTP routes (Facade).

Add new category routers here (e.g. IDP Okta) without changing `main.py`.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.integrations.categories.hrms.darwinbox.routers import (
    configure as darwinbox_configure,
    evidence as darwinbox_evidence,
)
from app.integrations.categories.itsm.servicenow.routers import (
    configure as servicenow_configure,
    evidence as servicenow_evidence,
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
    app.include_router(configure.router)
    app.include_router(configure.hrms_router)
    app.include_router(oauth.router)
    app.include_router(evidence.router)
    app.include_router(darwinbox_configure.router)
    app.include_router(darwinbox_configure.hrms_router)
    app.include_router(darwinbox_evidence.router)
    app.include_router(servicenow_configure.router)
    app.include_router(servicenow_configure.itsm_router)
    app.include_router(servicenow_evidence.router)
    app.include_router(entra_configure.commercial_router)
    app.include_router(entra_configure.commercial_idp_router)
    app.include_router(entra_configure.gcc_high_router)
    app.include_router(entra_configure.gcc_high_idp_router)
    app.include_router(entra_oauth.router)
    app.include_router(entra_evidence.router)
    app.include_router(integration_sync.router)
