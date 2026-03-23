"""
Central mount point for all integration HTTP routes (Facade).

Add new category routers here (e.g. IDP Okta) without changing `main.py`.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.integrations.categories.hrms.zoho_people.routers import configure, evidence, oauth


def mount_integration_routes(app: FastAPI) -> None:
    """Register all provider routers on the FastAPI application."""
    app.include_router(configure.router)
    app.include_router(configure.hrms_router)
    app.include_router(oauth.router)
    app.include_router(evidence.router)
