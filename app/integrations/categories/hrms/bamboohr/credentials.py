"""Resolve BambooHR authentication details from ``tool_integrations.configuration_data``.

This is the first useful BambooHR file because every later layer will depend on it:
- configure routes need to validate what auth mode the user selected
- API clients need a usable API key or access token
- token refresh logic needs to know whether OAuth/app auth is active

We support two auth modes:
1. API key mode: customer gives BambooHR subdomain + API key
2. App/OAuth mode: customer connects through the BambooHR app flow
"""

from __future__ import annotations

from typing import Any, Literal


AuthMode = Literal["api_key", "app_oauth"]

AUTH_MODE_API_KEY: AuthMode = "api_key"
AUTH_MODE_APP_OAUTH: AuthMode = "app_oauth"
DEFAULT_AUTH_MODE: AuthMode = AUTH_MODE_API_KEY


def resolve_auth_mode(cfg: dict[str, Any]) -> AuthMode:
    """Return the active BambooHR auth mode.

    Why this exists:
    - we will support two login styles for the same integration
    - all later code needs one consistent place to ask "which mode are we in?"
    """
    raw = str(cfg.get("auth_mode") or DEFAULT_AUTH_MODE).strip().lower()
    if raw in {AUTH_MODE_API_KEY, AUTH_MODE_APP_OAUTH}:
        return raw  # type: ignore[return-value]
    raise ValueError("Invalid BambooHR auth_mode. Expected 'api_key' or 'app_oauth'.")


def resolve_subdomain(cfg: dict[str, Any]) -> str:
    """Resolve the BambooHR company subdomain.

    Example:
    - if the BambooHR URL is https://acme.bamboohr.com, the subdomain is ``acme``

    Why this exists:
    - both API key auth and app auth will still need to know which BambooHR tenant to call
    """
    raw = cfg.get("subdomain") or cfg.get("company_domain")
    if raw is None or not str(raw).strip():
        raise ValueError("Missing BambooHR subdomain in configuration_data.")
    return str(raw).strip()


def resolve_api_key(cfg: dict[str, Any]) -> str | None:
    """Return the BambooHR API key when API key auth is used."""
    raw = cfg.get("api_key")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def resolve_access_token(cfg: dict[str, Any]) -> str | None:
    """Return the OAuth/app access token when app auth is used."""
    raw = cfg.get("access_token")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def resolve_refresh_token(cfg: dict[str, Any]) -> str | None:
    """Return the refresh token for BambooHR app/OAuth mode."""
    raw = cfg.get("refresh_token")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def access_token_expires_raw(cfg: dict[str, Any]) -> str | None:
    """Return the stored BambooHR token expiry timestamp if present."""
    raw = cfg.get("access_token_expires_at")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def resolve_redirect_uri(cfg: dict[str, Any]) -> str:
    """Return the configured OAuth redirect URI for BambooHR app auth."""
    raw = cfg.get("redirect_uri")
    if raw is None or not str(raw).strip():
        raise ValueError("Missing BambooHR redirect_uri in configuration_data.")
    return str(raw).strip()


def resolve_client_credentials(cfg: dict[str, Any]) -> tuple[str, str]:
    """Return BambooHR app client credentials for OAuth/app auth."""
    client_id = cfg.get("client_id")
    client_secret = cfg.get("client_secret")
    if client_id is None or not str(client_id).strip():
        raise ValueError("Missing BambooHR client_id in configuration_data.")
    if client_secret is None or not str(client_secret).strip():
        raise ValueError("Missing BambooHR client_secret in configuration_data.")
    return str(client_id).strip(), str(client_secret).strip()


def has_usable_credentials(cfg: dict[str, Any]) -> bool:
    """Quick readiness check used by later workflow steps.

    API key mode is usable when:
    - subdomain exists
    - api_key exists

    App/OAuth mode is usable when:
    - subdomain exists
    - access_token exists
    """
    try:
        resolve_subdomain(cfg)
        mode = resolve_auth_mode(cfg)
    except ValueError:
        return False

    if mode == AUTH_MODE_API_KEY:
        return bool(resolve_api_key(cfg))
    return bool(resolve_access_token(cfg))
