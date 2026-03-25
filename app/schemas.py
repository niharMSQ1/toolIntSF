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
            "Explicit provider: zoho_people | microsoft_entra | microsoft_entra_gcc_high. "
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
