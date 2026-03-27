from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolIntegrationPayload(BaseModel):
    org_id: str = Field(description="Organization UUID; persisted as tool_integrations.organization_id.")
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
    """Unified sync: same optional filters as collect; provider is optional if evidence_masters exist."""

    org_id: str
    user_id: str
    tool_id: str
    provider_key: str | None = Field(
        default=None,
        description=(
            "Explicit provider: zoho_people | microsoft_entra | microsoft_entra_gcc_high | bitbucket_cloud | wiz | jira_cloud | okta. "
            "Omit to infer from evidence_masters.source (after configure)."
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
