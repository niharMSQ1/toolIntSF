"""Map UI region keys to Snyk API hosts (Vanta-style region selector)."""

from __future__ import annotations

# Keys: lowercase identifiers stored in configuration_data["region"]
SNYK_REST_HOST_BY_REGION: dict[str, str] = {
    "us": "api.snyk.io",
    "usa": "api.snyk.io",
    "eu": "api.eu.snyk.io",
    "au": "api.au.snyk.io",
}


def resolve_rest_host(region: str | None) -> str:
    if not region or not str(region).strip():
        return SNYK_REST_HOST_BY_REGION["us"]
    key = str(region).strip().lower()
    return SNYK_REST_HOST_BY_REGION.get(key, SNYK_REST_HOST_BY_REGION["us"])


def resolve_v1_base_url(region: str | None) -> str:
    """Legacy v1 API uses same host (https://apidocs.snyk.io/)."""
    host = resolve_rest_host(region)
    return f"https://{host}/v1"


def resolve_rest_base_url(region: str | None) -> str:
    host = resolve_rest_host(region)
    return f"https://{host}/rest"


def resolve_oauth_token_url(region: str | None) -> str:
    """POST client credentials / refresh — same regional host as REST (see Snyk OAuth2 API)."""
    host = resolve_rest_host(region)
    return f"https://{host}/oauth2/token"
