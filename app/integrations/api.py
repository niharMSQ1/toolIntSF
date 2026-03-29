"""
Central mount point for all integration HTTP routes (Facade).

Add new category routers here (e.g. IDP Okta) without changing `main.py`.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.integrations.categories.cloud.aws.routers import (
    configure_router as aws_configure_router,
    evidence_router as aws_evidence_router,
)
from app.integrations.categories.cspm.snyk.routers import (
    configure_router as snyk_configure_router,
    evidence_router as snyk_evidence_router,
)
from app.integrations.categories.cspm.sysdig_secure.routers import (
    configure_router as sysdig_secure_configure_router,
    evidence_router as sysdig_secure_evidence_router,
)
from app.integrations.categories.cspm.aqua_security.routers import (
    configure_router as aqua_security_configure_router,
    evidence_router as aqua_security_evidence_router,
)
from app.integrations.categories.cspm.defender_cloud.routers import (
    configure_router as defender_cloud_configure_router,
    evidence_router as defender_cloud_evidence_router,
)
from app.integrations.categories.cspm.lacework.routers import (
    configure_router as lacework_configure_router,
    evidence_router as lacework_evidence_router,
)
from app.integrations.categories.cspm.orca_security.routers import (
    configure_router as orca_security_configure_router,
    evidence_router as orca_security_evidence_router,
)
from app.integrations.categories.cspm.prisma_cloud.routers import (
    configure_router as prisma_cloud_configure_router,
    evidence_router as prisma_cloud_evidence_router,
)
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
from app.integrations.categories.itsm.jira.routers import configure as jira_configure
from app.integrations.categories.itsm.jira.routers import evidence as jira_evidence
from app.integrations.categories.itsm.jira.routers import oauth as jira_oauth
from app.integrations.categories.idp.microsoft_entra.routers import (
    configure as entra_configure,
    evidence as entra_evidence,
    oauth as entra_oauth,
)
from app.integrations.categories.idp.okta.routers import configure as okta_configure
from app.integrations.categories.idp.okta.routers import evidence as okta_evidence
from app.integrations.routers import integration_sync


def mount_integration_routes(app: FastAPI) -> None:
    """Register all provider routers on the FastAPI application."""
    app.include_router(wiz_configure_router)
    app.include_router(wiz_evidence_router)
    app.include_router(prisma_cloud_configure_router)
    app.include_router(prisma_cloud_evidence_router)
    app.include_router(defender_cloud_configure_router)
    app.include_router(defender_cloud_evidence_router)
    app.include_router(aqua_security_configure_router)
    app.include_router(aqua_security_evidence_router)
    app.include_router(lacework_configure_router)
    app.include_router(lacework_evidence_router)
    app.include_router(orca_security_configure_router)
    app.include_router(orca_security_evidence_router)
    app.include_router(snyk_configure_router)
    app.include_router(snyk_evidence_router)
    app.include_router(sysdig_secure_configure_router)
    app.include_router(sysdig_secure_evidence_router)
    app.include_router(aws_configure_router)
    app.include_router(aws_evidence_router)
    app.include_router(bitbucket_configure_router)
    app.include_router(bitbucket_workspaces_router)
    app.include_router(bitbucket_oauth_authorize_router)
    app.include_router(bitbucket_callback_router)
    app.include_router(bitbucket_evidence_router)
    app.include_router(configure.router)
    app.include_router(configure.hrms_router)
    app.include_router(oauth.router)
    app.include_router(evidence.router)
    app.include_router(jira_configure.router)
    app.include_router(jira_configure.itsm_router)
    app.include_router(jira_oauth.router)
    app.include_router(jira_evidence.router)
    app.include_router(entra_configure.commercial_router)
    app.include_router(entra_configure.commercial_idp_router)
    app.include_router(entra_configure.gcc_high_router)
    app.include_router(entra_configure.gcc_high_idp_router)
    app.include_router(entra_oauth.router)
    app.include_router(entra_evidence.router)
    app.include_router(okta_configure.router)
    app.include_router(okta_configure.idp_router)
    app.include_router(okta_evidence.router)
    app.include_router(integration_sync.router)
