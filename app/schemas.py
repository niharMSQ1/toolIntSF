from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolIntegrationPayload(BaseModel):
    org_id: str = Field(description="Organization UUID; persisted as tool_integrations.organization_id.")
    user_id: str
    tool_id: str
    configuration_data: dict[str, Any]


class ToolIntegrationRequestBody(BaseModel):
    """
    Client POST body for configure endpoints. When GRC auth is configured (grc_auth_validate_url),
    omit org_id and send Authorization: Bearer; otherwise include org_id (legacy).
    """

    org_id: str | None = Field(
        default=None,
        description="Required when GRC auth is not configured; ignored when using bearer validation.",
    )
    user_id: str
    tool_id: str
    configuration_data: dict[str, Any]


class ToolIntegrationResponse(BaseModel):
    id: str
    organization_id: str
    tool_id: str
    configuration_data: dict


class ZohoConfigureResponse(BaseModel):
    """Returned by POST /configure: saved row + next OAuth step (auth URL when tokens are missing)."""

    id: str
    organization_id: str
    tool_id: str
    oauth_complete: bool = Field(description="True if access_token already stored (skip browser OAuth).")
    authorization_url: str | None = Field(
        default=None,
        description="Open in browser to authorize Zoho (only when oauth_complete is false).",
    )
    state: str | None = Field(default=None, description="OAuth state parameter; returned with the callback.")
    next_step: str
    configuration_data: dict = Field(
        description="Saved config with secrets masked (same masking as GET /status).",
    )


class AuthorizeQuery(BaseModel):
    org_id: str
    tool_id: str


class AuthorizeResponse(BaseModel):
    authorization_url: str
    state: str


class ZohoOAuthCallbackResponse(BaseModel):
    """Returned by GET /hrms/zoho/callback after a successful code exchange."""

    ok: bool
    organization_id: str
    tool_id: str
    message: str
    collection_started: bool = Field(
        description="True if a background job was queued to pull all evidence from Zoho People.",
    )
    next_step: str
    collect_post_json_example: dict[str, Any] | None = Field(
        default=None,
        description="Reserved; always null. Evidence collection runs in the background after OAuth when user_id is present.",
    )


class CollectEvidenceBody(BaseModel):
    org_id: str
    user_id: str
    tool_id: str
    # Optional: limit to specific evidence master codes
    evidence_codes: list[str] | None = None
    # Date range for time-bound APIs (YYYY-MM-DD)
    date_from: str | None = None
    date_to: str | None = None


class CollectionItemResult(BaseModel):
    evidence_master_code: str
    name: str
    status: str
    error: str | None = None


class CollectEvidenceResponse(BaseModel):
    org_id: str
    tool_id: str
    user_id: str
    results: list[CollectionItemResult]


class SyncIntegrationBody(BaseModel):
    """Unified sync: same optional filters as collect; provider is optional when evidence_masters rows exist for the domain."""

    org_id: str
    user_id: str
    tool_id: str
    provider_key: str | None = Field(
        default=None,
        description=(
            "Explicit provider: zoho_people | microsoft_entra | microsoft_entra_gcc_high | bitbucket_cloud | wiz | snyk | aws | jira_cloud | okta. "
            "Omit to infer from evidence_masters.source when present; generic IAM source ``iam`` is resolved from configuration_data."
        ),
    )
    evidence_codes: list[str] | None = None
    date_from: str | None = None
    date_to: str | None = None


class SyncIntegrationResponse(BaseModel):
    """Result of POST /api/v1/integrations/sync."""

    provider_key: str = Field(description="Provider used for this run (from request or auto-detected).")
    org_id: str
    tool_id: str
    user_id: str
    results: list[CollectionItemResult]


class ZohoFlowResponse(BaseModel):
    """Where you are in configure → OAuth → collect."""

    organization_id: str
    tool_id: str
    oauth_complete: bool
    redirect_uri: str | None = None
    next_step: str
    authorization_url: str | None = None
    state: str | None = None
    collect_post_json_example: dict | None = None


class ZohoRefreshTokensBody(BaseModel):
    org_id: str
    tool_id: str
    force: bool = Field(
        default=False,
        description="If true, always call Zoho refresh even when access_token is still valid.",
    )


class ZohoRefreshTokensResponse(BaseModel):
    ok: bool
    organization_id: str
    tool_id: str
    refreshed: bool = Field(description="True if Zoho token API was called.")
    message: str
    configuration_data: dict = Field(description="Saved config with secrets masked.")


class JiraConfigureResponse(BaseModel):
    """Returned by POST /api/v1/integrations/jira/configure: saved row + next OAuth step."""

    id: str
    organization_id: str
    tool_id: str
    oauth_complete: bool = Field(description="True if access_token already stored (skip browser OAuth).")
    authorization_url: str | None = Field(
        default=None,
        description="Open in browser to authorize Atlassian (only when oauth_complete is false).",
    )
    state: str | None = Field(default=None, description="OAuth state parameter; returned with the callback.")
    next_step: str
    configuration_data: dict = Field(
        description="Saved config with secrets masked (same masking as GET /status).",
    )


class JiraOAuthCallbackResponse(BaseModel):
    """Returned by GET /itsm/jira/callback after a successful code exchange."""

    ok: bool
    organization_id: str
    tool_id: str
    message: str
    collection_started: bool = Field(
        description="True if a background job was queued to pull evidence from Jira Cloud.",
    )
    next_step: str
    collect_post_json_example: dict[str, Any] | None = Field(
        default=None,
        description="Reserved; always null when collection runs in the background after OAuth.",
    )


class JiraFlowResponse(BaseModel):
    """Where you are in configure → OAuth → collect for Jira Cloud."""

    organization_id: str
    tool_id: str
    oauth_complete: bool
    redirect_uri: str | None = None
    next_step: str
    authorization_url: str | None = None
    state: str | None = None
    collect_post_json_example: dict | None = None


class JiraRefreshTokensBody(BaseModel):
    org_id: str
    tool_id: str
    force: bool = Field(
        default=False,
        description="If true, always call Atlassian token endpoint even when access_token is still valid.",
    )


class JiraRefreshTokensResponse(BaseModel):
    ok: bool
    organization_id: str
    tool_id: str
    refreshed: bool = Field(description="True if Atlassian token API was called.")
    message: str
    configuration_data: dict = Field(description="Saved config with secrets masked.")


class EntraConfigureResponse(BaseModel):
    """Returned by POST .../configure: saved row + next OAuth step."""

    id: str
    organization_id: str
    tool_id: str
    oauth_complete: bool = Field(description="True if access_token already stored (skip browser OAuth).")
    authorization_url: str | None = Field(
        default=None,
        description="Open in browser to authorize Microsoft Entra (only when oauth_complete is false).",
    )
    state: str | None = Field(default=None, description="OAuth state parameter; returned with the callback.")
    next_step: str
    configuration_data: dict = Field(
        description="Saved config with secrets masked (same masking as GET /status).",
    )


class EntraOAuthCallbackResponse(BaseModel):
    ok: bool
    organization_id: str
    tool_id: str
    message: str
    collection_started: bool = Field(
        description="True if a background job was queued to pull evidence from Microsoft Graph.",
    )
    next_step: str
    collect_post_json_example: dict[str, Any] | None = Field(
        default=None,
        description="Reserved; null when collection runs in the background after OAuth.",
    )


class EntraFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    oauth_complete: bool
    redirect_uri: str | None = None
    next_step: str
    authorization_url: str | None = None
    state: str | None = None
    collect_post_json_example: dict | None = None


class EntraRefreshTokensBody(BaseModel):
    org_id: str
    tool_id: str
    force: bool = Field(
        default=False,
        description="If true, always call Microsoft token endpoint even when access_token is still valid.",
    )


class EntraRefreshTokensResponse(BaseModel):
    ok: bool
    organization_id: str
    tool_id: str
    refreshed: bool = Field(description="True if Microsoft token endpoint was called.")
    message: str
    configuration_data: dict = Field(description="Saved config with secrets masked.")


class BitbucketConfigureResponse(BaseModel):
    """Returned by POST .../devtools/bitbucket/configure."""

    id: str
    organization_id: str
    tool_id: str
    oauth_complete: bool
    workspace_selection_required: bool
    ready_for_collection: bool
    authorization_url: str | None = None
    state: str | None = None
    next_step: str
    configuration_data: dict


class BitbucketFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    oauth_complete: bool
    workspace_selection_required: bool
    ready_for_collection: bool
    redirect_uri: str | None = None
    next_step: str
    authorization_url: str | None = None
    state: str | None = None


class BitbucketOAuthCallbackResponse(BaseModel):
    ok: bool
    organization_id: str
    tool_id: str
    message: str
    next_step: str


class GitHubConfigureResponse(BaseModel):
    """Returned by POST .../devtools/github/configure (PAT or OAuth app)."""

    id: str
    organization_id: str
    tool_id: str
    oauth_complete: bool = Field(description="True when a bearer token is stored (PAT or OAuth access_token).")
    ready_for_collection: bool = Field(description="True when REST calls can be made (same as oauth_complete for GitHub).")
    authorization_url: str | None = None
    state: str | None = None
    next_step: str
    configuration_data: dict


class GitHubFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    oauth_complete: bool
    ready_for_collection: bool
    redirect_uri: str | None = None
    next_step: str
    authorization_url: str | None = None
    state: str | None = None


class GitHubOAuthCallbackResponse(BaseModel):
    ok: bool
    organization_id: str
    tool_id: str
    message: str
    next_step: str


class AzureDevOpsConfigureResponse(BaseModel):
    """Returned by POST .../devtools/azure-devops/configure (PAT + organization)."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if a sample Projects API call succeeded.")
    ready_for_collection: bool = Field(description="Same as credentials_valid for this integration.")
    next_step: str
    configuration_data: dict


class AzureDevOpsFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    ready_for_collection: bool
    next_step: str


class JenkinsConfigureResponse(BaseModel):
    """Returned by POST .../devtools/jenkins/configure."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if GET /api/json on Jenkins succeeded.")
    ready_for_collection: bool
    next_step: str
    configuration_data: dict


class JenkinsFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    ready_for_collection: bool
    next_step: str


class CircleCIConfigureResponse(BaseModel):
    """Returned by POST .../devtools/circleci/configure."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if GET /api/v2/me succeeded.")
    ready_for_collection: bool = Field(description="True when token and project_slug are set and token is valid.")
    next_step: str
    configuration_data: dict


class CircleCIFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    ready_for_collection: bool
    next_step: str


class ArgoCDConfigureResponse(BaseModel):
    """Returned by POST .../devtools/argocd/configure."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if GET /api/v1/version succeeded.")
    ready_for_collection: bool
    next_step: str
    configuration_data: dict


class ArgoCDFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    ready_for_collection: bool
    next_step: str


class TeamCityConfigureResponse(BaseModel):
    """Returned by POST .../devtools/teamcity/configure."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if GET /app/rest/server succeeded.")
    ready_for_collection: bool
    next_step: str
    configuration_data: dict


class TeamCityFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    ready_for_collection: bool
    next_step: str


class WorkdayConfigureResponse(BaseModel):
    """Returned by POST .../hrms/workday/configure."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if Workers API sample call succeeded.")
    ready_for_collection: bool
    next_step: str
    configuration_data: dict


class WorkdayFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    ready_for_collection: bool
    api_version: str = Field(description="REST API version segment (e.g. v1).")
    next_step: str


class WorkdayRefreshTokensBody(BaseModel):
    org_id: str
    tool_id: str
    force: bool = Field(default=False, description="Reserved; refresh always attempts when refresh_token exists.")


class WorkdayRefreshTokensResponse(BaseModel):
    ok: bool
    organization_id: str
    tool_id: str
    refreshed: bool
    message: str
    configuration_data: dict = Field(description="Saved config with secrets masked.")


class SAPSuccessFactorsConfigureResponse(BaseModel):
    """Returned by POST .../hrms/sap-successfactors/configure."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if OData User sample call succeeded.")
    ready_for_collection: bool
    next_step: str
    configuration_data: dict


class SAPSuccessFactorsFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    ready_for_collection: bool
    next_step: str


class AdpConfigureResponse(BaseModel):
    """Returned by POST .../hrms/adp/configure."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if ADP workers sample call succeeded.")
    ready_for_collection: bool
    next_step: str
    configuration_data: dict


class AdpFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    ready_for_collection: bool
    next_step: str


class UkgConfigureResponse(BaseModel):
    """Returned by POST .../hrms/ukg/configure."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if UKG people API sample call succeeded.")
    ready_for_collection: bool
    next_step: str
    configuration_data: dict


class UkgFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    ready_for_collection: bool
    next_step: str


class BambooHrConfigureResponse(BaseModel):
    """Returned by POST .../hrms/bamboohr/configure."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if BambooHR directory API call succeeded.")
    ready_for_collection: bool
    next_step: str
    configuration_data: dict


class BambooHrFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    ready_for_collection: bool
    next_step: str


class PaycomConfigureResponse(BaseModel):
    """Returned by POST .../hrms/paycom/configure."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if Paycom employees sample call succeeded.")
    ready_for_collection: bool
    next_step: str
    configuration_data: dict


class PaycomFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    ready_for_collection: bool
    next_step: str


class RipplingConfigureResponse(BaseModel):
    """Returned by POST .../hrms/rippling/configure."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if Rippling employees sample call succeeded.")
    ready_for_collection: bool
    next_step: str
    configuration_data: dict


class RipplingFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    ready_for_collection: bool
    next_step: str


class BitbucketSelectWorkspacesBody(BaseModel):
    org_id: str
    tool_id: str
    workspace_slugs: list[str] = Field(description="Bitbucket workspace slugs to sync (must be in GET /workspaces list).")


class BitbucketWorkspacesListResponse(BaseModel):
    workspaces: list[dict[str, Any]]


class WizConfigureResponse(BaseModel):
    """Returned by POST /api/v1/integrations/cspm/wiz/configure (service account + GraphQL URL)."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if OAuth client-credentials exchange returned an access_token.")
    ready_for_collection: bool = Field(description="True when graphql_url and secrets are valid and token is stored.")
    collection_started_in_background: bool = Field(
        default=True,
        description="When true, a background job is pulling all Wiz evidence (same as POST .../evidence/wiz/collect).",
    )
    next_step: str
    configuration_data: dict = Field(description="Saved config with secrets masked (same as GET /status).")


class SnykConfigureResponse(BaseModel):
    """Returned by POST /api/v1/integrations/cspm/snyk/configure (API key, access token, or OAuth client credentials + scope)."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(
        description="True if static token or OAuth credentials validate (e.g. GET /v1/orgs after OAuth exchange when applicable)."
    )
    ready_for_collection: bool = Field(description="True when credentials, region, and org_ids or group_id are set.")
    collection_started_in_background: bool = Field(
        default=True,
        description="When true, a background job is pulling Snyk evidence (same as POST .../evidence/snyk/collect).",
    )
    next_step: str
    configuration_data: dict = Field(description="Saved config with secrets masked (same as GET /status).")


class SnykFlowResponse(BaseModel):
    """Where you are in configure → collect for Snyk."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class PrismaCloudConfigureResponse(BaseModel):
    """Returned by POST /api/v1/integrations/cspm/prisma-cloud/configure (CSPM REST access key + API URL)."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(
        description="True if POST /login succeeded with the configured access key and API base URL.",
    )
    ready_for_collection: bool = Field(description="True when api_base_url and keys are valid and JWT is stored.")
    collection_started_in_background: bool = Field(
        default=True,
        description="When true, a background job is pulling Prisma Cloud evidence.",
    )
    next_step: str
    configuration_data: dict = Field(description="Saved config with secrets and JWT masked.")


class PrismaCloudFlowResponse(BaseModel):
    """Where you are in configure → collect for Prisma Cloud."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class DefenderCloudConfigureResponse(BaseModel):
    """POST .../cspm/defender-cloud/configure — Azure AD app registration + subscription ID."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(
        description="True if OAuth2 client credentials and ARM Microsoft.Security secureScores call succeeded.",
    )
    ready_for_collection: bool = Field(description="True when tenant, app secret, and subscription are set.")
    collection_started_in_background: bool = Field(
        default=True,
        description="When true, background job pulls Defender for Cloud evidence.",
    )
    next_step: str
    configuration_data: dict = Field(description="Saved config with secrets and token masked.")


class DefenderCloudFlowResponse(BaseModel):
    """Configure → collect flow for Microsoft Defender for Cloud."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class OrcaSecurityConfigureResponse(BaseModel):
    """POST .../cspm/orca-security/configure — API token + optional regional host."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if POST .../automations/query/alerts with limit=1 succeeded.")
    ready_for_collection: bool = Field(description="True when api_token and API base URL are set.")
    collection_started_in_background: bool = Field(default=True, description="Background evidence pull when ready.")
    next_step: str
    configuration_data: dict = Field(description="Saved config with token masked.")


class OrcaSecurityFlowResponse(BaseModel):
    """Configure → collect flow for Orca Security."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class LaceworkConfigureResponse(BaseModel):
    """POST .../cspm/lacework/configure — account subdomain + API key id + secret."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(
        description="True if POST /api/v2/access/tokens and GET /api/v2/UserProfile succeeded.",
    )
    ready_for_collection: bool = Field(description="True when account, key_id, and secret are set.")
    collection_started_in_background: bool = Field(default=True, description="Background evidence pull when ready.")
    next_step: str
    configuration_data: dict = Field(description="Saved config with secret masked.")


class LaceworkFlowResponse(BaseModel):
    """Configure → collect flow for Lacework."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class AquaSecurityConfigureResponse(BaseModel):
    """POST .../cspm/aqua-security/configure — self-hosted console URL + login id + password."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(
        description="True if POST /api/v1/login and GET /api/v1/hosts succeeded.",
    )
    ready_for_collection: bool = Field(description="True when api_base_url, login_id, and password are set.")
    collection_started_in_background: bool = Field(default=True, description="Background evidence pull when ready.")
    next_step: str
    configuration_data: dict = Field(description="Saved config with password masked.")


class AquaSecurityFlowResponse(BaseModel):
    """Configure → collect flow for Aqua Security."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class SysdigSecureConfigureResponse(BaseModel):
    """POST .../cspm/sysdig-secure/configure — regional API base URL + Bearer API token."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(
        description="True if GET /api/user/me succeeded with the configured token.",
    )
    ready_for_collection: bool = Field(description="True when api_token and api_base_url are set.")
    collection_started_in_background: bool = Field(default=True, description="Background evidence pull when ready.")
    next_step: str
    configuration_data: dict = Field(description="Saved config with token masked.")


class SysdigSecureFlowResponse(BaseModel):
    """Configure → collect flow for Sysdig Secure."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class CrowdStrikeFalconConfigureResponse(BaseModel):
    """POST .../endpoint/crowdstrike-falcon/configure — OAuth2 API client + secret."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(
        description="True if POST /oauth2/token and GET /devices/queries/devices/v1?limit=1 succeeded.",
    )
    ready_for_collection: bool = Field(description="True when client_id, client_secret, and api_base_url are set.")
    collection_started_in_background: bool = Field(default=True, description="Background evidence pull when ready.")
    next_step: str
    configuration_data: dict = Field(description="Saved config with client_secret masked.")


class CrowdStrikeFalconFlowResponse(BaseModel):
    """Configure → collect flow for CrowdStrike Falcon."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class DefenderForEndpointConfigureResponse(BaseModel):
    """POST .../endpoint/defender-for-endpoint/configure — Entra app + secret."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(
        description="True if token acquisition and GET /api/machines?$top=1 succeeded (200 or 404).",
    )
    ready_for_collection: bool = Field(description="True when tenant_id, client_id, client_secret, and api_base_url are set.")
    collection_started_in_background: bool = Field(default=True, description="Background evidence pull when ready.")
    next_step: str
    configuration_data: dict = Field(description="Saved config with client_secret masked.")


class DefenderForEndpointFlowResponse(BaseModel):
    """Configure → collect flow for Microsoft Defender for Endpoint."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class SentinelOneConfigureResponse(BaseModel):
    """POST .../endpoint/sentinelone/configure — API token + console URL."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(
        description="True if GET .../web/api/v2.1/agents?limit=1 succeeded with ApiToken auth.",
    )
    ready_for_collection: bool = Field(description="True when api_token and api_base_url are set.")
    collection_started_in_background: bool = Field(default=True, description="Background evidence pull when ready.")
    next_step: str
    configuration_data: dict = Field(description="Saved config with api_token masked.")


class SentinelOneFlowResponse(BaseModel):
    """Configure → collect flow for SentinelOne."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class TenableIoConfigureResponse(BaseModel):
    """POST .../vulnerability/tenable-io/configure — Tenable.io access + secret keys."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if GET /assets succeeded with X-ApiKeys.")
    ready_for_collection: bool = Field(description="True when access_key, secret_key, and api_base_url are set.")
    collection_started_in_background: bool = Field(default=True, description="Background evidence pull when ready.")
    next_step: str
    configuration_data: dict = Field(description="Saved config with secret_key masked.")


class TenableIoFlowResponse(BaseModel):
    """Configure → collect flow for Tenable.io."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class QualysConfigureResponse(BaseModel):
    """POST .../vulnerability/qualys/configure — Qualys user + password (Basic)."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if host list API returned 200 with valid XML.")
    ready_for_collection: bool = Field(description="True when username, password, and api_base_url are set.")
    collection_started_in_background: bool = Field(default=True, description="Background evidence pull when ready.")
    next_step: str
    configuration_data: dict = Field(description="Saved config with password masked.")


class QualysFlowResponse(BaseModel):
    """Configure → collect flow for Qualys."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class Rapid7InsightVmConfigureResponse(BaseModel):
    """POST .../vulnerability/rapid7-insightvm/configure — Security Console Basic auth."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if GET /api/3/sites?size=1 succeeded.")
    ready_for_collection: bool = Field(description="True when username, password, and api_base_url are set.")
    collection_started_in_background: bool = Field(default=True, description="Background evidence pull when ready.")
    next_step: str
    configuration_data: dict = Field(description="Saved config with password masked.")


class Rapid7InsightVmFlowResponse(BaseModel):
    """Configure → collect flow for Rapid7 InsightVM."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class TaniumConfigureResponse(BaseModel):
    """POST .../endpoint/tanium/configure — API token in session header."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if GET /api/v2/session/info succeeded.")
    ready_for_collection: bool = Field(description="True when api_token and api_base_url are set.")
    collection_started_in_background: bool = Field(default=True, description="Background evidence pull when ready.")
    next_step: str
    configuration_data: dict = Field(description="Saved config with api_token masked.")


class TaniumFlowResponse(BaseModel):
    """Configure → collect flow for Tanium."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class AwsConfigureResponse(BaseModel):
    """Returned by POST /api/v1/integrations/cloud/aws/configure (IAM role ARN for STS AssumeRole)."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(
        description="True if role_arn is well-formed and STS AssumeRole + GetCallerIdentity succeeded."
    )
    ready_for_collection: bool = Field(description="True when role_arn is set and assumption succeeded.")
    collection_started_in_background: bool = Field(
        default=True,
        description="When true, a background job is pulling AWS evidence (same as POST .../evidence/aws/collect).",
    )
    next_step: str
    configuration_data: dict = Field(description="Saved config with secrets masked (same as GET /status).")


class AwsFlowResponse(BaseModel):
    """Where you are in configure → collect for AWS."""

    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class WizFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class WizRefreshTokensResponse(BaseModel):
    ok: bool
    organization_id: str
    tool_id: str
    refreshed: bool = Field(description="True if a new token was obtained from Wiz auth.")
    message: str
    configuration_data: dict = Field(description="Saved config with secrets masked.")


class OktaConfigureResponse(BaseModel):
    """Returned by POST /api/v1/integrations/okta/configure (org URL + SSWS API token)."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if GET /api/v1/org succeeded with the API token.")
    ready_for_collection: bool = Field(description="True when org_domain and api_token are valid for collection.")
    collection_started_in_background: bool = Field(
        default=True,
        description="When true, a background job is pulling all Okta IAM evidence (same as POST .../evidence/okta/collect).",
    )
    next_step: str
    configuration_data: dict = Field(description="Saved config with secrets masked (same as GET /status).")


class OktaFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class PingIdentityConfigureResponse(BaseModel):
    """Returned by POST /api/v1/integrations/ping-identity/configure (PingOne Worker + Management API)."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(
        description="True if GET .../environments/{envID}/users succeeded with the access token.",
    )
    ready_for_collection: bool = Field(description="True when PingOne OAuth and environment ID are valid.")
    collection_started_in_background: bool = Field(
        default=True,
        description="When true, IAM evidence collection runs after successful configure.",
    )
    next_step: str
    configuration_data: dict = Field(description="Saved config with secrets masked.")


class PingIdentityFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class CyberArkConfigureResponse(BaseModel):
    """POST .../integrations/cyberark-identity/configure — CyberArk Identity SCIM + OAuth."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if SCIM Users sample succeeded.")
    ready_for_collection: bool
    collection_started_in_background: bool = Field(default=True)
    next_step: str
    configuration_data: dict


class CyberArkFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class SailPointConfigureResponse(BaseModel):
    """POST .../integrations/sailpoint-identity/configure — IdentityNow OAuth + public identities."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if public identities sample succeeded.")
    ready_for_collection: bool
    collection_started_in_background: bool = Field(default=True)
    next_step: str
    configuration_data: dict


class SailPointFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class GoogleWorkspaceConfigureResponse(BaseModel):
    """POST .../integrations/google-workspace/configure — Admin SDK Directory API."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool = Field(description="True if users.list succeeded.")
    ready_for_collection: bool
    collection_started_in_background: bool = Field(default=True)
    next_step: str
    configuration_data: dict


class GoogleWorkspaceFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class ForgeRockConfigureResponse(BaseModel):
    """POST .../integrations/forgerock/configure — OAuth 2.0 + REST user query."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    collection_started_in_background: bool = Field(default=True)
    next_step: str
    configuration_data: dict


class ForgeRockFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class OneLoginConfigureResponse(BaseModel):
    """POST .../integrations/onelogin/configure — OAuth 2.0 + Users API."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    collection_started_in_background: bool = Field(default=True)
    next_step: str
    configuration_data: dict


class OneLoginFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class JumpCloudConfigureResponse(BaseModel):
    """POST .../integrations/jumpcloud/configure — API key + system users."""

    id: str
    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    collection_started_in_background: bool = Field(default=True)
    next_step: str
    configuration_data: dict


class JumpCloudFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    credentials_valid: bool
    ready_for_collection: bool
    next_step: str


class AsanaConfigureResponse(BaseModel):
    """Returned by POST /api/v1/integrations/project-management/asana/configure."""

    id: str
    organization_id: str
    tool_id: str
    oauth_complete: bool = Field(
        description="True when a bearer token is available (PAT or OAuth access_token).",
    )
    auth_method: str | None = Field(
        default=None,
        description="pat | oauth when inferable from configuration_data.",
    )
    authorization_url: str | None = None
    state: str | None = None
    next_step: str
    configuration_data: dict


class AsanaFlowResponse(BaseModel):
    """Where you are in configure → OAuth → API for Asana."""

    organization_id: str
    tool_id: str
    oauth_complete: bool
    auth_method: str | None = None
    redirect_uri: str | None = None
    next_step: str
    authorization_url: str | None = None
    state: str | None = None


class AsanaRefreshTokensBody(BaseModel):
    org_id: str
    tool_id: str
    force: bool = Field(
        default=False,
        description="If true, always call Asana token endpoint even when access_token is still valid.",
    )


class AsanaRefreshTokensResponse(BaseModel):
    ok: bool
    organization_id: str
    tool_id: str
    refreshed: bool = Field(description="True if Asana oauth_token API was called.")
    message: str
    configuration_data: dict = Field(description="Saved config with secrets masked.")


class AsanaOAuthCallbackResponse(BaseModel):
    """Returned by GET /project-management/asana/callback after a successful code exchange."""

    ok: bool
    organization_id: str
    tool_id: str
    message: str
    collection_started: bool = Field(
        default=False,
        description="Reserved; Asana does not run GRC evidence collection from this callback.",
    )
    next_step: str


class MondayConfigureResponse(BaseModel):
    """Returned by POST /api/v1/integrations/project-management/monday/configure."""

    id: str
    organization_id: str
    tool_id: str
    token_configured: bool = Field(description="True when a Monday personal API token is stored.")
    next_step: str
    configuration_data: dict


class MondayFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    token_configured: bool
    next_step: str


class MicrosoftPlannerConfigureResponse(BaseModel):
    id: str
    organization_id: str
    tool_id: str
    auth_configured: bool = Field(description="True when access_token or client credentials are present.")
    next_step: str
    configuration_data: dict


class MicrosoftPlannerFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    auth_configured: bool
    next_step: str


class MicrosoftPlannerRefreshTokensBody(BaseModel):
    org_id: str
    tool_id: str
    force: bool = False


class MicrosoftPlannerRefreshTokensResponse(BaseModel):
    ok: bool
    organization_id: str
    tool_id: str
    refreshed: bool
    message: str
    configuration_data: dict


class PmTokenConfigureResponse(BaseModel):
    """Shared shape for API-token PM tools (Smartsheet, ClickUp, Notion, Linear)."""

    id: str
    organization_id: str
    tool_id: str
    token_configured: bool
    next_step: str
    configuration_data: dict


class PmTokenFlowResponse(BaseModel):
    organization_id: str
    tool_id: str
    token_configured: bool
    next_step: str


class DomainCatalogRow(BaseModel):
    """GRC catalog row: one evidence source per row; `evidence_sources` is the primary display label."""

    id: str
    domain_group: str = Field(description="Logical grouping (e.g. IT Service Management).")
    evidence_sources: str | None = Field(description="Single evidence-source entity for this row.")
    primary_evidence: str | None = None
    secondary_evidence: str | None = None
    common_tools: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
