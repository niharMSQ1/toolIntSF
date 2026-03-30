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
from app.integrations.categories.endpoint_security.crowdstrike_falcon.routers import (
    configure_router as crowdstrike_falcon_configure_router,
    evidence_router as crowdstrike_falcon_evidence_router,
)
from app.integrations.categories.endpoint_security.defender_for_endpoint.routers import (
    configure_router as defender_for_endpoint_configure_router,
    evidence_router as defender_for_endpoint_evidence_router,
)
from app.integrations.categories.endpoint_security.sentinelone.routers import (
    configure_router as sentinelone_configure_router,
    evidence_router as sentinelone_evidence_router,
)
from app.integrations.categories.vulnerability_management.qualys.routers import (
    configure_router as qualys_configure_router,
    evidence_router as qualys_evidence_router,
)
from app.integrations.categories.vulnerability_management.rapid7_insightvm.routers import (
    configure_router as rapid7_insightvm_configure_router,
    evidence_router as rapid7_insightvm_evidence_router,
)
from app.integrations.categories.vulnerability_management.tanium.routers import (
    configure_router as tanium_configure_router,
    evidence_router as tanium_evidence_router,
)
from app.integrations.categories.vulnerability_management.tenable_io.routers import (
    configure_router as tenable_io_configure_router,
    evidence_router as tenable_io_evidence_router,
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
from app.integrations.categories.devtools.azure_devops.routers import (
    configure_router as azure_devops_configure_router,
    data_router as azure_devops_data_router,
    webhook_router as azure_devops_webhook_router,
)
from app.integrations.categories.devtools.jenkins.routers import (
    configure_router as jenkins_configure_router,
    data_router as jenkins_data_router,
    webhook_router as jenkins_webhook_router,
)
from app.integrations.categories.devtools.circleci.routers import (
    configure_router as circleci_configure_router,
    data_router as circleci_data_router,
    webhook_router as circleci_webhook_router,
)
from app.integrations.categories.devtools.argocd.routers import (
    configure_router as argocd_configure_router,
    data_router as argocd_data_router,
    webhook_router as argocd_webhook_router,
)
from app.integrations.categories.devtools.teamcity.routers import (
    configure_router as teamcity_configure_router,
    data_router as teamcity_data_router,
    webhook_router as teamcity_webhook_router,
)
from app.integrations.categories.devtools.github.routers import (
    callback_router as github_callback_router,
    configure_router as github_configure_router,
    data_router as github_data_router,
    oauth_authorize_router as github_oauth_authorize_router,
    webhook_router as github_webhook_router,
)
from app.integrations.categories.project_management.asana.routers import configure as asana_configure
from app.integrations.categories.project_management.asana.routers import data as asana_data
from app.integrations.categories.project_management.asana.routers import oauth as asana_oauth
from app.integrations.categories.project_management.asana.routers import webhook as asana_webhook
from app.integrations.categories.project_management.monday.routers import configure as monday_configure
from app.integrations.categories.project_management.monday.routers import data as monday_data
from app.integrations.categories.project_management.monday.routers import webhook as monday_webhook
from app.integrations.categories.project_management.microsoft_planner.routers import configure as ms_planner_configure
from app.integrations.categories.project_management.microsoft_planner.routers import data as ms_planner_data
from app.integrations.categories.project_management.smartsheet.routers import configure as smartsheet_configure
from app.integrations.categories.project_management.smartsheet.routers import data as smartsheet_data
from app.integrations.categories.project_management.clickup.routers import configure as clickup_configure
from app.integrations.categories.project_management.clickup.routers import data as clickup_data
from app.integrations.categories.project_management.notion.routers import configure as notion_configure
from app.integrations.categories.project_management.notion.routers import data as notion_data
from app.integrations.categories.project_management.linear.routers import configure as linear_configure
from app.integrations.categories.project_management.linear.routers import data as linear_data
from app.integrations.categories.hrms.workday.routers import (
    configure_router as workday_configure_router,
    data_router as workday_data_router,
    refresh_router as workday_refresh_router,
    webhook_router as workday_webhook_router,
)
from app.integrations.categories.hrms.sap_successfactors.routers import (
    configure_router as sap_successfactors_configure_router,
    data_router as sap_successfactors_data_router,
    webhook_router as sap_successfactors_webhook_router,
)
from app.integrations.categories.hrms.adp.routers import (
    configure_router as adp_configure_router,
    data_router as adp_data_router,
    webhook_router as adp_webhook_router,
)
from app.integrations.categories.hrms.ukg.routers import (
    configure_router as ukg_configure_router,
    data_router as ukg_data_router,
    webhook_router as ukg_webhook_router,
)
from app.integrations.categories.hrms.bamboohr.routers import (
    configure_router as bamboohr_configure_router,
    data_router as bamboohr_data_router,
    webhook_router as bamboohr_webhook_router,
)
from app.integrations.categories.hrms.paycom.routers import (
    configure_router as paycom_configure_router,
    data_router as paycom_data_router,
    webhook_router as paycom_webhook_router,
)
from app.integrations.categories.hrms.rippling.routers import (
    configure_router as rippling_configure_router,
    data_router as rippling_data_router,
    webhook_router as rippling_webhook_router,
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
    app.include_router(crowdstrike_falcon_configure_router)
    app.include_router(crowdstrike_falcon_evidence_router)
    app.include_router(defender_for_endpoint_configure_router)
    app.include_router(defender_for_endpoint_evidence_router)
    app.include_router(sentinelone_configure_router)
    app.include_router(sentinelone_evidence_router)
    app.include_router(tenable_io_configure_router)
    app.include_router(tenable_io_evidence_router)
    app.include_router(qualys_configure_router)
    app.include_router(qualys_evidence_router)
    app.include_router(rapid7_insightvm_configure_router)
    app.include_router(rapid7_insightvm_evidence_router)
    app.include_router(tanium_configure_router)
    app.include_router(tanium_evidence_router)
    app.include_router(aws_configure_router)
    app.include_router(aws_evidence_router)
    app.include_router(asana_configure.router)
    app.include_router(asana_configure.pm_router)
    app.include_router(asana_oauth.router)
    app.include_router(asana_data.router)
    app.include_router(asana_webhook.router)
    app.include_router(monday_configure.router)
    app.include_router(monday_configure.pm_router)
    app.include_router(monday_data.router)
    app.include_router(monday_webhook.router)
    app.include_router(ms_planner_configure.router)
    app.include_router(ms_planner_configure.pm_router)
    app.include_router(ms_planner_data.router)
    app.include_router(smartsheet_configure.router)
    app.include_router(smartsheet_configure.pm_router)
    app.include_router(smartsheet_data.router)
    app.include_router(clickup_configure.router)
    app.include_router(clickup_configure.pm_router)
    app.include_router(clickup_data.router)
    app.include_router(notion_configure.router)
    app.include_router(notion_configure.pm_router)
    app.include_router(notion_data.router)
    app.include_router(linear_configure.router)
    app.include_router(linear_configure.pm_router)
    app.include_router(linear_data.router)
    app.include_router(bitbucket_configure_router)
    app.include_router(bitbucket_workspaces_router)
    app.include_router(bitbucket_oauth_authorize_router)
    app.include_router(bitbucket_callback_router)
    app.include_router(bitbucket_evidence_router)
    app.include_router(github_configure_router)
    app.include_router(github_data_router)
    app.include_router(github_oauth_authorize_router)
    app.include_router(github_callback_router)
    app.include_router(github_webhook_router)
    app.include_router(azure_devops_configure_router)
    app.include_router(azure_devops_data_router)
    app.include_router(azure_devops_webhook_router)
    app.include_router(jenkins_configure_router)
    app.include_router(jenkins_data_router)
    app.include_router(jenkins_webhook_router)
    app.include_router(circleci_configure_router)
    app.include_router(circleci_data_router)
    app.include_router(circleci_webhook_router)
    app.include_router(argocd_configure_router)
    app.include_router(argocd_data_router)
    app.include_router(argocd_webhook_router)
    app.include_router(teamcity_configure_router)
    app.include_router(teamcity_data_router)
    app.include_router(teamcity_webhook_router)
    app.include_router(workday_configure_router)
    app.include_router(workday_data_router)
    app.include_router(workday_refresh_router)
    app.include_router(workday_webhook_router)
    app.include_router(sap_successfactors_configure_router)
    app.include_router(sap_successfactors_data_router)
    app.include_router(sap_successfactors_webhook_router)
    app.include_router(adp_configure_router)
    app.include_router(adp_data_router)
    app.include_router(adp_webhook_router)
    app.include_router(ukg_configure_router)
    app.include_router(ukg_data_router)
    app.include_router(ukg_webhook_router)
    app.include_router(bamboohr_configure_router)
    app.include_router(bamboohr_data_router)
    app.include_router(bamboohr_webhook_router)
    app.include_router(paycom_configure_router)
    app.include_router(paycom_data_router)
    app.include_router(paycom_webhook_router)
    app.include_router(rippling_configure_router)
    app.include_router(rippling_data_router)
    app.include_router(rippling_webhook_router)
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
